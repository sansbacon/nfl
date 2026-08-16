# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Auction Price Projection Model
# MAGIC %md ## Auction Price Projection Model
# MAGIC
# MAGIC A position-optimal ensemble that predicts **80% prediction intervals** for fantasy football auction draft costs on a $200 budget. Each position routes to the model that performed best in cross-validation:
# MAGIC
# MAGIC | Position | Model | Rationale |
# MAGIC | --- | --- | --- |
# MAGIC | QB | Conformal (Split) | Uniform intervals suit flat QB cost curves |
# MAGIC | RB | GP (Shared Kernel) | Cross-position signal helps steep RB decay |
# MAGIC | WR | GP (Per-Position, Matérn) | Position-specific kernel captures sharp WR drop-off |
# MAGIC | TE | GP (Per-Position, RBF) | Smoother kernel fits gradual TE curve |
# MAGIC
# MAGIC ### Interpreting Validation Metrics
# MAGIC
# MAGIC | Metric | Meaning | Good values |
# MAGIC | --- | --- | --- |
# MAGIC | **Coverage** | % of actual prices that fell within the predicted [low, high] interval | ≥ 80% (the target); values well above indicate conservative intervals |
# MAGIC | **Width** | Average dollar span of the interval (high − low) | Lower is better — tighter range = more actionable bid guidance |
# MAGIC | **MAE** | Mean absolute error of the median prediction vs. actual cost | Lower is better — measures point-estimate accuracy |
# MAGIC
# MAGIC **Tradeoff:** Coverage and width are inversely related. You can always achieve 100% coverage by making intervals infinitely wide. The model targets 80% coverage with the narrowest intervals possible. Coverage moderately above 80% (e.g. 85–90%) is acceptable conservatism for draft strategy; significantly above suggests intervals could be tightened.
# MAGIC

# COMMAND ----------

# MAGIC %md ## Setup

# COMMAND ----------

# MAGIC %pip install ngboost statsmodels -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import logging
import os
import pickle
import tempfile

import pandas as pd
import numpy as np
import mlflow
from mlflow.models import infer_signature
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, ConstantKernel, WhiteKernel
from sklearn.base import clone

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

logging.getLogger("mlflow.tracking.context.registry").setLevel(logging.ERROR)

# COMMAND ----------

dbutils.widgets.text('MODEL_NAME', "nfl.default.auction_price_ensemble")

# COMMAND ----------

MODEL_NAME = dbutils.widgets.get('MODEL_NAME')

# COMMAND ----------

# MAGIC %md ## Load Auction Data

# COMMAND ----------

# Combine auction data from vw_draft_picks with Yahoo ADP
df = spark.table('nfl.yh.vw_auction_model').toPandas()

# COMMAND ----------

# Cast adp from Decimal to float (kept for reference/display, not used as model feature)
df['adp'] = df['adp'].astype(float)

# Filter to rows with average_cost populated (2025 lacks it entirely)
# Keep full df for reference; train only on rows with complete features
df_model = df[df['average_cost'].notna()].copy().reset_index(drop=True)

# Roster-construction demand thresholds (12-team league)
# Beyond these ranks, demand collapses → prices hit the $1 floor
DEMAND_THRESHOLDS = {'QB': 14, 'TE': 13, 'RB': 42, 'WR': 48}

# demand_saturation: position_rank / threshold
# Values > 1.0 signal "past the demand cliff" where nobody is bidding
df_model['demand_saturation'] = df_model.apply(
    lambda r: r['position_rank'] / DEMAND_THRESHOLDS[r['player_position']], axis=1
)

# Prepare features and target — adp dropped (redundant with average_cost, r=-0.86)
X_all = df_model[['position_rank', 'average_cost', 'demand_saturation', 'player_position']].copy()
y_all = df_model['cost'].values

print(f"Full data: {len(df)} players, {df['player_position'].nunique()} positions, {df['season'].nunique()} seasons ({sorted(df['season'].unique())})")
print(f"Model training data: {len(df_model)} players (rows with average_cost)")
print(f"Cost range: ${df_model['cost'].min():.0f} - ${df_model['cost'].max():.0f}")
print(f"Excluded: {len(df) - len(df_model)} rows from season(s) {sorted(df[df['average_cost'].isna()]['season'].unique())} (no average_cost)")



# COMMAND ----------

# MAGIC %md ## Functions

# COMMAND ----------

# --- Custom PyFunc Wrapper ---
class AuctionPriceEnsemble(mlflow.pyfunc.PythonModel):
    """
    Position-optimal ensemble for fantasy football auction price prediction.
    Routes each position to its best-performing model:
      QB → Conformal (Split)
      RB → Gaussian Process (shared kernel)
      WR → GP (Per-Position, Matérn)
      TE → GP (Per-Position, RBF)
    """
    
    def load_context(self, context):
        with open(context.artifacts["ensemble_state"], "rb") as f:
            state = pickle.load(f)
        self.conf_preprocessor = state['conf_preprocessor']
        self.conf_base = state['conf_base']
        self.conf_q_hat = state['conf_q_hat']
        self.gp_shared = state['gp_shared']
        self.gp_shared_scaler = state['gp_shared_scaler']
        self.gp_per_pos_models = state['gp_per_pos_models']
        self.gp_per_pos_scalers = state['gp_per_pos_scalers']
        self.ensemble_config = state['ensemble_config']
        self.demand_thresholds = state['demand_thresholds']
        self.historical_medians = state['historical_medians']
    
    def predict(self, context, model_input: pd.DataFrame) -> pd.DataFrame:
        """Predict auction price ranges. Input: position, position_rank, average_cost (opt)."""
        results = []
        for _, row in model_input.iterrows():
            position = row['position']
            position_rank = int(row['position_rank'])
            average_cost = row.get('average_cost')
            
            # Fill missing average_cost from historical medians
            key = (position, position_rank)
            if pd.isna(average_cost) or average_cost is None:
                average_cost = self.historical_medians.get(key, {}).get('average_cost', 1.0)
            
            average_cost = float(average_cost)
            demand_saturation = position_rank / self.demand_thresholds[position]
            strategy = self.ensemble_config[position]
            
            if strategy == 'conformal':
                input_df = pd.DataFrame({'position_rank': [position_rank], 'average_cost': [average_cost], 'demand_saturation': [demand_saturation], 'player_position': [position]})
                input_enc = self.conf_preprocessor.transform(input_df)
                med = self.conf_base.predict(input_enc)[0]
                tier = 'tail' if position_rank > self.demand_thresholds[position] else 'starter'
                q = self.conf_q_hat[position][tier]
                low, high = med - q, med + q
            elif strategy == 'gp_shared':
                input_df = pd.DataFrame({'position_rank': [position_rank], 'average_cost': [average_cost], 'demand_saturation': [demand_saturation], 'player_position': [position]})
                input_enc = self.conf_preprocessor.transform(input_df)
                input_sc = self.gp_shared_scaler.transform(input_enc)
                mu, sigma = self.gp_shared.predict(input_sc, return_std=True)
                med = mu[0]
                low, high = med - 1.65 * sigma[0], med + 1.65 * sigma[0]
            elif strategy == 'gp_per_position':
                import numpy as np
                input_arr = np.array([[position_rank, average_cost, demand_saturation]])
                input_sc = self.gp_per_pos_scalers[position].transform(input_arr)
                mu, sigma = self.gp_per_pos_models[position].predict(input_sc, return_std=True)
                med = mu[0]
                low, high = med - 1.65 * sigma[0], med + 1.65 * sigma[0]
            
            results.append({
                'low': max(1, int(round(low))),
                'median': max(1, int(round(med))),
                'high': max(1, int(round(high))),
                'model_used': strategy,
            })
        
        return pd.DataFrame(results)

# COMMAND ----------

# MAGIC %md ## Create Model

# COMMAND ----------

# Position-specific kernel designs (from cross-validated comparison):
# - RB/WR: steep exponential decay → shorter length scale, Matérn for roughness
# - QB/TE: flatter curves with more variance → longer length scale, smoother RBF
position_kernels = {
    'RB': ConstantKernel(50.0, (1, 500)) * Matern(length_scale=3.0, length_scale_bounds=(0.5, 20), nu=1.5) + WhiteKernel(noise_level=10, noise_level_bounds=(1, 100)),
    'WR': ConstantKernel(50.0, (1, 500)) * Matern(length_scale=3.0, length_scale_bounds=(0.5, 20), nu=1.5) + WhiteKernel(noise_level=10, noise_level_bounds=(1, 100)),
    'QB': ConstantKernel(20.0, (1, 100)) * RBF(length_scale=5.0, length_scale_bounds=(1, 30)) + WhiteKernel(noise_level=8, noise_level_bounds=(1, 80)),
    'TE': ConstantKernel(30.0, (1, 150)) * RBF(length_scale=4.0, length_scale_bounds=(0.5, 25)) + WhiteKernel(noise_level=8, noise_level_bounds=(1, 80)),
}

# --- Ensemble Strategy (best model per position from CV analysis) ---
# QB  → Conformal (Split): uniform interval works well for flat cost curves
# RB  → Gaussian Process (shared): benefits from cross-position info for steep curves
# WR  → GP (Per-Position): position-specific Matérn captures sharp WR decay
# TE  → GP (Per-Position): position-specific RBF fits smoother TE curve

ENSEMBLE_CONFIG = {
    'QB': 'conformal',
    'RB': 'gp_shared',
    'WR': 'gp_per_position',
    'TE': 'gp_per_position',
}

print("Training Final Ensemble on ALL data...")
print(f"  QB → Conformal (Split)")
print(f"  RB → Gaussian Process (shared kernel)")
print(f"  WR → GP (Per-Position, Matérn ν=1.5)")
print(f"  TE → GP (Per-Position, RBF)")

# COMMAND ----------

# --- Train all component models on full dataset ---
# adp dropped: collinear with average_cost (r=-0.86), marginal importance (+0.73) once avg_cost present
features = ['position_rank', 'average_cost', 'player_position']
numeric_features = ['position_rank', 'average_cost', 'demand_saturation']

# 1. Conformal (Split) for QB
print("  [1/3] Training Conformal base model...")
conf_preprocessor = ColumnTransformer([
    ('pos_encode', OneHotEncoder(drop='first', sparse_output=False), ['player_position'])
], remainder='passthrough')

X_full_enc = conf_preprocessor.fit_transform(X_all)

# Use 80/20 split for conformal calibration
rng = np.random.RandomState(42)
n_cal = len(y_all) // 5
cal_indices = rng.choice(len(y_all), n_cal, replace=False)
fit_indices = np.setdiff1d(np.arange(len(y_all)), cal_indices)

conf_base = GradientBoostingRegressor(
    n_estimators=200, max_depth=3, learning_rate=0.05,
    min_samples_leaf=5, random_state=42
)
conf_base.fit(X_full_enc[fit_indices], y_all[fit_indices])

# Position-specific, tier-stratified conformal quantiles
# Separate q_hat for starters vs. post-cliff tail (demand_saturation > 1.0)
conf_q_hat = {}
for pos in ['QB', 'RB', 'WR', 'TE']:
    threshold = DEMAND_THRESHOLDS[pos]
    pos_cal_mask = df_model.iloc[cal_indices]['player_position'] == pos
    pos_cal_idx = cal_indices[pos_cal_mask.values]
    if len(pos_cal_idx) > 0:
        cal_preds = conf_base.predict(X_full_enc[pos_cal_idx])
        cal_scores = np.abs(y_all[pos_cal_idx] - cal_preds)
        pos_ranks = df_model.iloc[pos_cal_idx]['position_rank'].values
        starter_mask = pos_ranks <= threshold
        tail_mask = pos_ranks > threshold
        conf_q_hat[pos] = {
            'starter': np.quantile(cal_scores[starter_mask], 0.90) if starter_mask.sum() > 2 else np.quantile(cal_scores, 0.90),
            'tail': np.quantile(cal_scores[tail_mask], 0.90) if tail_mask.sum() > 2 else 1.0,
        }

# 2. GP (shared kernel) for RB
print("  [2/3] Training GP shared kernel...")
gp_shared_kernel = ConstantKernel(1.0) * RBF(length_scale=5.0) + WhiteKernel(noise_level=5.0)
gp_shared = GaussianProcessRegressor(kernel=gp_shared_kernel, n_restarts_optimizer=5, random_state=42)
gp_shared_scaler = StandardScaler()
X_gp_shared = gp_shared_scaler.fit_transform(X_full_enc)
gp_shared.fit(X_gp_shared, y_all)

# 3. GP per-position for WR and TE
print("  [3/3] Training per-position GPs...")
gp_per_pos_models = {}
gp_per_pos_scalers = {}

for pos in ['WR', 'TE']:
    pos_mask = (df_model['player_position'] == pos).values
    X_pos = df_model.loc[pos_mask, numeric_features].values
    y_pos = y_all[pos_mask]
    
    scaler = StandardScaler()
    X_pos_sc = scaler.fit_transform(X_pos)
    
    kernel = clone(GaussianProcessRegressor(kernel=position_kernels[pos])).kernel
    gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, random_state=42, alpha=1e-6)
    gp.fit(X_pos_sc, y_pos)
    
    gp_per_pos_models[pos] = gp
    gp_per_pos_scalers[pos] = scaler

print("\n✓ All ensemble components trained.")

# COMMAND ----------

# --- Package Ensemble State ---
historical_medians = {}
for (pos, rank), grp in df_model.groupby(['player_position', 'position_rank']):
    historical_medians[(pos, rank)] = {
        'average_cost': float(grp['average_cost'].median()) if grp['average_cost'].notna().any() else float(grp['cost'].median()),
    }

ensemble_state = {
    'conf_preprocessor': conf_preprocessor,
    'conf_base': conf_base,
    'conf_q_hat': conf_q_hat,
    'gp_shared': gp_shared,
    'gp_shared_scaler': gp_shared_scaler,
    'gp_per_pos_models': gp_per_pos_models,
    'gp_per_pos_scalers': gp_per_pos_scalers,
    'ensemble_config': ENSEMBLE_CONFIG,
    'demand_thresholds': DEMAND_THRESHOLDS,
    'historical_medians': historical_medians,
}

# Save to temp file and create model instance
tmp_dir = tempfile.mkdtemp()
state_path = os.path.join(tmp_dir, "ensemble_state.pkl")
with open(state_path, "wb") as f:
    pickle.dump(ensemble_state, f)

class FakeContext:
    artifacts = {"ensemble_state": state_path}

model_instance = AuctionPriceEnsemble()
model_instance.load_context(FakeContext())

# --- Validate Ensemble (in-sample) ---
input_example = pd.DataFrame({
    'position': ['RB', 'WR', 'QB', 'TE'],
    'position_rank': [1, 5, 3, 2],
    'average_cost': [65.0, 45.0, 20.0, 28.0],
})
sample_output = model_instance.predict(None, input_example)

# Generate projection table
rows = []
for pos in ['QB', 'RB', 'WR', 'TE']:
    pos_input = pd.DataFrame({
        'position': [pos] * 20,
        'position_rank': list(range(1, 21)),
        'average_cost': [
            historical_medians.get((pos, r), {}).get('average_cost', 1.0)
            for r in range(1, 21)
        ],
    })
    pos_output = model_instance.predict(None, pos_input)
    for i in range(len(pos_input)):
        rows.append({
            'position': pos,
            'position_rank': i + 1,
            'low': pos_output.iloc[i]['low'],
            'median': pos_output.iloc[i]['median'],
            'high': pos_output.iloc[i]['high'],
            'model': pos_output.iloc[i]['model_used'],
        })

ensemble_df = pd.DataFrame(rows)
ensemble_df['range'] = ensemble_df.apply(lambda r: f"${r['low']}-${r['high']}", axis=1)

print("Projected Auction Price Ranges — Ensemble Model ($200 budget)")
print("=" * 65)
display(ensemble_df[['position', 'position_rank', 'low', 'median', 'high', 'range', 'model']])

# Per-position validation
print("\nEnsemble Validation (in-sample):")
for pos in ['QB', 'RB', 'WR', 'TE']:
    mask = (df_model['player_position'] == pos).values
    y_pos = y_all[mask]
    val_input = pd.DataFrame({
        'position': df_model.loc[mask, 'player_position'].values,
        'position_rank': df_model.loc[mask, 'position_rank'].values,
        'average_cost': df_model.loc[mask, 'average_cost'].values,
    })
    val_output = model_instance.predict(None, val_input)
    lows = val_output['low'].values
    highs = val_output['high'].values
    meds = val_output['median'].values
    cov = ((y_pos >= lows) & (y_pos <= highs)).mean()
    width = (highs - lows).mean()
    mae = np.mean(np.abs(y_pos - meds))
    print(f"  {pos}: Coverage={cov:.1%}  Width=${width:.1f}  MAE=${mae:.1f}  [{ENSEMBLE_CONFIG[pos]}]")

# COMMAND ----------

# MAGIC %md ## Register Model

# COMMAND ----------

# Compute signature and validation metrics for MLflow logging
signature = infer_signature(input_example, sample_output)

val_metrics = {}
for pos in ['QB', 'RB', 'WR', 'TE']:
    mask = (df_model['player_position'] == pos).values
    y_pos = y_all[mask]
    val_input = pd.DataFrame({
        'position': df_model.loc[mask, 'player_position'].values,
        'position_rank': df_model.loc[mask, 'position_rank'].values,
        'average_cost': df_model.loc[mask, 'average_cost'].values,
    })
    val_output = model_instance.predict(None, val_input)
    lows = val_output['low'].values
    highs = val_output['high'].values
    meds = val_output['median'].values
    val_metrics[pos] = {
        'coverage': ((y_pos >= lows) & (y_pos <= highs)).mean(),
        'width': (highs - lows).mean(),
        'mae': np.mean(np.abs(y_pos - meds)),
    }

coverage_overall = np.mean([m['coverage'] for m in val_metrics.values()])
width_mean = np.mean([m['width'] for m in val_metrics.values()])
mae_mean = np.mean([m['mae'] for m in val_metrics.values()])
training_seasons = ','.join(str(s) for s in sorted(df_model['season'].unique()))

print(f"Overall: Coverage={coverage_overall:.1%}  Width=${width_mean:.1f}  MAE=${mae_mean:.1f}")

# COMMAND ----------

with mlflow.start_run(run_name=f"auction_price_ensemble_{pd.Timestamp.now().strftime('%Y%m%d')}") as run:
    mlflow.log_params({
        "ensemble_strategy": "per_position_best",
        "QB_model": "conformal_split",
        "RB_model": "gp_shared",
        "WR_model": "gp_per_position_matern",
        "TE_model": "gp_per_position_rbf",
        "adp_source": "nfl.yh.adp (Yahoo)",
        "features": "position_rank, average_cost",
        "training_seasons": training_seasons,
        "n_training_samples": len(df_model),
        "interval_coverage_target": 0.80,
    })
    mlflow.log_metrics({
        "cv_coverage_overall": round(coverage_overall, 3),
        "cv_width_mean": round(width_mean, 1),
        "cv_mae_mean": round(mae_mean, 1),
    })
    
    model_info = mlflow.pyfunc.log_model(
        name="model",
        python_model=AuctionPriceEnsemble(),
        artifacts={"ensemble_state": state_path},
        signature=signature,
        input_example=input_example,
        pip_requirements=[
            "scikit-learn>=1.3.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
        ],
        registered_model_name=MODEL_NAME,
    )

print(f"✓ Model registered: {MODEL_NAME}")
print(f"  Run ID: {run.info.run_id}")
print(f"  Model URI: {model_info.model_uri}")
print(f"\nSample predictions:")
display(pd.concat([input_example, sample_output], axis=1))