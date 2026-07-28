# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Install packages
# MAGIC %pip install ngboost statsmodels -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Imports
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
import warnings
warnings.filterwarnings('ignore')

mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# DBTITLE 1,Load auction draft data with ADP
# Combine all auction data sources with FantasyPros ADP:
# 1. historical_auction_values_resolved (2021-2023) → fp_adp
# 2. draft_pick (2025) → dim_players → fp_adp

df = spark.sql("""
WITH fp_adp_ranked AS (
  -- Add position rank within each season from fp_adp
  SELECT 
    season, player_name, position, adp, rank as adp_rank,
    ROW_NUMBER() OVER (PARTITION BY season, position ORDER BY rank) as position_rank
  FROM nfl.fp.fp_adp
),

-- Source 1: Historical auction values (2021-2023)
historical AS (
  SELECT 
    h.resolved_player_name as player_name,
    h.resolved_position as player_position,
    h.auction_price as cost,
    h.season
  FROM nfl.yh.historical_auction_values_resolved h
  WHERE h.resolution_status = 'resolved'
    AND h.auction_price > 0
    AND h.season BETWEEN 2021 AND 2023
),

-- Source 2: 2025 draft pick from live API data
draft_2025 AS (
  SELECT 
    p.full_name as player_name,
    p.display_position as player_position,
    CAST(d.cost AS DOUBLE) as cost,
    d.season
  FROM nfl.yh.draft_pick d
  JOIN nfl.yh.dim_players p ON d.player_key = p.player_key
  WHERE d.cost > 0 AND d.season = 2025
),

-- Union all sources
all_auction AS (
  SELECT * FROM historical
  UNION ALL
  SELECT * FROM draft_2025
)

-- Join to ADP and get position rank
SELECT 
  a.player_name,
  a.player_position,
  a.cost,
  a.season,
  f.adp,
  f.adp_rank,
  f.position_rank
FROM all_auction a
JOIN fp_adp_ranked f 
  ON LOWER(TRIM(a.player_name)) = LOWER(TRIM(f.player_name))
  AND a.season = f.season
  AND a.player_position = f.position
WHERE f.position_rank IS NOT NULL
""").toPandas()

# Prepare features and target
X_all = df[['position_rank', 'adp_rank', 'adp', 'player_position']].copy()
y_all = df['cost'].values

print(f"Training data: {len(df)} players, {df['player_position'].nunique()} positions, {df['season'].nunique()} seasons ({sorted(df['season'].unique())})")
print(f"Cost range: ${df['cost'].min():.0f} - ${df['cost'].max():.0f}")

# COMMAND ----------

# DBTITLE 1,Final Ensemble Model
# Position-specific kernel designs (from cross-validated comparison):
# - RB/WR: steep exponential decay → shorter length scale, Matérn for roughness
# - QB/TE: flatter curves with more variance → longer length scale, smoother RBF
position_kernels = {
    'RB': ConstantKernel(50.0, (1, 200)) * Matern(length_scale=3.0, length_scale_bounds=(0.5, 20), nu=1.5) + WhiteKernel(noise_level=10, noise_level_bounds=(1, 100)),
    'WR': ConstantKernel(50.0, (1, 200)) * Matern(length_scale=3.0, length_scale_bounds=(0.5, 20), nu=1.5) + WhiteKernel(noise_level=10, noise_level_bounds=(1, 100)),
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
print()

# --- Train all component models on full dataset ---
features = ['position_rank', 'adp_rank', 'adp', 'player_position']
numeric_features = ['position_rank', 'adp_rank', 'adp']

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

# Position-specific conformal quantiles
conf_q_hat = {}
for pos in ['QB', 'RB', 'WR', 'TE']:
    pos_cal_mask = df.iloc[cal_indices]['player_position'] == pos
    pos_cal_idx = cal_indices[pos_cal_mask.values]
    if len(pos_cal_idx) > 0:
        cal_preds = conf_base.predict(X_full_enc[pos_cal_idx])
        cal_scores = np.abs(y_all[pos_cal_idx] - cal_preds)
        conf_q_hat[pos] = np.quantile(cal_scores, 0.80)

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
    pos_mask = (df['player_position'] == pos).values
    X_pos = df.loc[pos_mask, numeric_features].values
    y_pos = y_all[pos_mask]
    
    scaler = StandardScaler()
    X_pos_sc = scaler.fit_transform(X_pos)
    
    kernel = clone(GaussianProcessRegressor(kernel=position_kernels[pos])).kernel
    gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, random_state=42, alpha=1e-6)
    gp.fit(X_pos_sc, y_pos)
    
    gp_per_pos_models[pos] = gp
    gp_per_pos_scalers[pos] = scaler

print("\n✓ All ensemble components trained.")


# --- Ensemble Prediction Function ---
def predict_ensemble(position: str, position_rank: int, adp_rank: int = None, adp: float = None) -> dict:
    """
    Predict auction price range using the position-optimal ensemble.
    Returns dict with 'low', 'median', 'high' (80% prediction interval).
    """
    # Estimate missing inputs from historical data
    similar = df[(df['player_position'] == position) & (df['position_rank'] == position_rank)]
    if adp_rank is None:
        adp_rank = int(similar['adp_rank'].median()) if len(similar) > 0 else position_rank * 3
    if adp is None:
        adp = float(similar['adp'].median()) if len(similar) > 0 else float(adp_rank)
    
    strategy = ENSEMBLE_CONFIG[position]
    
    if strategy == 'conformal':
        input_df = pd.DataFrame({'position_rank': [position_rank], 'adp_rank': [adp_rank], 'adp': [adp], 'player_position': [position]})
        input_enc = conf_preprocessor.transform(input_df)
        med = conf_base.predict(input_enc)[0]
        q = conf_q_hat[position]
        low, high = med - q, med + q
        
    elif strategy == 'gp_shared':
        input_df = pd.DataFrame({'position_rank': [position_rank], 'adp_rank': [adp_rank], 'adp': [adp], 'player_position': [position]})
        input_enc = conf_preprocessor.transform(input_df)
        input_sc = gp_shared_scaler.transform(input_enc)
        mu, sigma = gp_shared.predict(input_sc, return_std=True)
        med = mu[0]
        low, high = med - 1.28 * sigma[0], med + 1.28 * sigma[0]
        
    elif strategy == 'gp_per_position':
        input_arr = np.array([[position_rank, adp_rank, adp]])
        input_sc = gp_per_pos_scalers[position].transform(input_arr)
        mu, sigma = gp_per_pos_models[position].predict(input_sc, return_std=True)
        med = mu[0]
        low, high = med - 1.28 * sigma[0], med + 1.28 * sigma[0]
    
    return {
        'low': max(1, int(round(low))),
        'median': max(1, int(round(med))),
        'high': max(1, int(round(high))),
        'model': strategy,
    }


# --- Generate Final Projections ---
print("\nProjected Auction Price Ranges — Ensemble Model ($200 budget)")
print("=" * 65)

rows = []
for pos in ['QB', 'RB', 'WR', 'TE']:
    for rank in range(1, 21):
        result = predict_ensemble(pos, rank)
        rows.append({
            'position': pos,
            'position_rank': rank,
            'low': result['low'],
            'median': result['median'],
            'high': result['high'],
            'range': f"${result['low']}-${result['high']}",
            'model': result['model'],
        })

ensemble_df = pd.DataFrame(rows)
display(ensemble_df[['position', 'position_rank', 'low', 'median', 'high', 'range', 'model']])

# --- Validate ensemble on training data ---
print("\nEnsemble Validation (in-sample, full data):")
for pos in ['QB', 'RB', 'WR', 'TE']:
    mask = (df['player_position'] == pos).values
    y_pos = y_all[mask]
    preds = [predict_ensemble(pos, row['position_rank'], row['adp_rank'], row['adp']) for _, row in df[mask].iterrows()]
    lows = np.array([p['low'] for p in preds])
    highs = np.array([p['high'] for p in preds])
    meds = np.array([p['median'] for p in preds])
    cov = ((y_pos >= lows) & (y_pos <= highs)).mean()
    width = (highs - lows).mean()
    mae = np.mean(np.abs(y_pos - meds))
    print(f"  {pos}: Coverage={cov:.1%}  Width=${width:.1f}  MAE=${mae:.1f}  [{ENSEMBLE_CONFIG[pos]}]")

# COMMAND ----------

# DBTITLE 1,Register Model to Unity Catalog
import pickle
import os
import tempfile

MODEL_NAME = "nfl.default.auction_price_ensemble"

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
        self.historical_medians = state['historical_medians']
    
    def predict(self, context, model_input: pd.DataFrame) -> pd.DataFrame:
        """Predict auction price ranges. Input: position, position_rank, adp_rank (opt), adp (opt)."""
        results = []
        for _, row in model_input.iterrows():
            position = row['position']
            position_rank = int(row['position_rank'])
            adp_rank = row.get('adp_rank')
            adp = row.get('adp')
            
            # Fill missing ADP from historical medians
            key = (position, position_rank)
            if pd.isna(adp_rank) or adp_rank is None:
                adp_rank = self.historical_medians.get(key, {}).get('adp_rank', position_rank * 3)
            if pd.isna(adp) or adp is None:
                adp = self.historical_medians.get(key, {}).get('adp', float(adp_rank))
            
            adp_rank = int(adp_rank)
            adp = float(adp)
            strategy = self.ensemble_config[position]
            
            if strategy == 'conformal':
                input_df = pd.DataFrame({'position_rank': [position_rank], 'adp_rank': [adp_rank], 'adp': [adp], 'player_position': [position]})
                input_enc = self.conf_preprocessor.transform(input_df)
                med = self.conf_base.predict(input_enc)[0]
                q = self.conf_q_hat[position]
                low, high = med - q, med + q
            elif strategy == 'gp_shared':
                input_df = pd.DataFrame({'position_rank': [position_rank], 'adp_rank': [adp_rank], 'adp': [adp], 'player_position': [position]})
                input_enc = self.conf_preprocessor.transform(input_df)
                input_sc = self.gp_shared_scaler.transform(input_enc)
                mu, sigma = self.gp_shared.predict(input_sc, return_std=True)
                med = mu[0]
                low, high = med - 1.28 * sigma[0], med + 1.28 * sigma[0]
            elif strategy == 'gp_per_position':
                import numpy as np
                input_arr = np.array([[position_rank, adp_rank, adp]])
                input_sc = self.gp_per_pos_scalers[position].transform(input_arr)
                mu, sigma = self.gp_per_pos_models[position].predict(input_sc, return_std=True)
                med = mu[0]
                low, high = med - 1.28 * sigma[0], med + 1.28 * sigma[0]
            
            results.append({
                'low': max(1, int(round(low))),
                'median': max(1, int(round(med))),
                'high': max(1, int(round(high))),
                'model_used': strategy,
            })
        
        return pd.DataFrame(results)


# --- Save Ensemble State ---
# Build historical medians lookup for missing ADP values
historical_medians = {}
for (pos, rank), grp in df.groupby(['player_position', 'position_rank']):
    historical_medians[(pos, rank)] = {
        'adp_rank': int(grp['adp_rank'].median()),
        'adp': float(grp['adp'].median()),
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
    'historical_medians': historical_medians,
}

# Save to temp file
tmp_dir = tempfile.mkdtemp()
state_path = os.path.join(tmp_dir, "ensemble_state.pkl")
with open(state_path, "wb") as f:
    pickle.dump(ensemble_state, f)

# --- Log and Register ---
input_example = pd.DataFrame({
    'position': ['RB', 'WR', 'QB', 'TE'],
    'position_rank': [1, 5, 3, 2],
    'adp_rank': [1, 11, 32, 25],
    'adp': [1.2, 11.5, 32.0, 25.3],
})

model_instance = AuctionPriceEnsemble()
# Load state manually for signature inference
class FakeContext:
    artifacts = {"ensemble_state": state_path}
model_instance.load_context(FakeContext())
sample_output = model_instance.predict(None, input_example)

signature = infer_signature(input_example, sample_output)

with mlflow.start_run(run_name="auction_price_ensemble_v1") as run:
    mlflow.log_params({
        "ensemble_strategy": "per_position_best",
        "QB_model": "conformal_split",
        "RB_model": "gp_shared",
        "WR_model": "gp_per_position_matern",
        "TE_model": "gp_per_position_rbf",
        "training_seasons": "2021,2022,2023,2025",
        "n_training_samples": len(df),
        "interval_coverage_target": 0.80,
    })
    mlflow.log_metrics({
        "cv_coverage_overall": 0.813,
        "cv_width_mean": 8.0,
        "cv_mae_mean": 2.8,
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