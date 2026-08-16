# Databricks notebook source
# MAGIC %md ## Phase 4: Feature Ablation Study
# MAGIC
# MAGIC Compare model performance **with vs. without `average_cost`** on a held-out 2024 season to determine whether the market consensus feature adds value beyond `position_rank` + `adp` alone.
# MAGIC
# MAGIC Three variants:
# MAGIC 1. **Full** — `position_rank` + `adp` + `average_cost` (current model)
# MAGIC 2. **No Market** — `position_rank` + `adp` only (baseline without ADP cost)
# MAGIC 3. **Simplified** — `average_cost` + `position` only (test if consensus alone suffices)

# COMMAND ----------

import pickle
import os
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

# Combine auction data from vw_draft_picks with Yahoo ADP

df = spark.sql("""
WITH adp_latest AS (
  SELECT
    g.year AS season,
    CAST(SPLIT(adp.player_key, '[.]')[2] AS BIGINT) AS player_id,
    adp.average_pick,
    adp.average_cost
  FROM nfl.yh.adp adp
  INNER JOIN (SELECT game_id, MAX(snapshot_date) AS sd FROM nfl.yh.adp GROUP BY game_id) ls
    ON adp.game_id = ls.game_id AND adp.snapshot_date = ls.sd
  INNER JOIN nfl.yh.game g ON adp.game_id = g.game_id
  WHERE adp.average_pick IS NOT NULL
),
drafts AS (
  SELECT
    season,
    CAST(SPLIT(player_key, '[.]')[2] AS BIGINT) AS player_id,
    player_name,
    player_position,
    CAST(cost AS DOUBLE) AS cost,
    ROW_NUMBER() OVER (
      PARTITION BY season, player_position
      ORDER BY CAST(cost AS DOUBLE) DESC
    ) AS position_rank
  FROM nfl.yh.vw_draft_picks
  WHERE player_position IN ('QB', 'WR', 'RB', 'TE')
)
SELECT
  d.player_name,
  d.player_position,
  d.cost,
  d.season,
  a.average_pick AS adp,
  CAST(a.average_cost AS DOUBLE) AS average_cost,
  d.position_rank
FROM drafts d
INNER JOIN adp_latest a
  ON d.player_id = a.player_id
  AND d.season = a.season
""").toPandas()

# Cast adp from Decimal to float (kept for reference/display, not used as model feature)
df['adp'] = df['adp'].astype(float)

# Filter to rows with average_cost populated (2025 lacks it entirely)
# Keep full df for reference; train only on rows with complete features
df_model = df[df['average_cost'].notna()].copy().reset_index(drop=True)

# Prepare features and target — adp dropped (redundant with average_cost, r=-0.86)
X_all = df_model[['position_rank', 'average_cost', 'player_position']].copy()
y_all = df_model['cost'].values

print(f"Full data: {len(df)} players, {df['player_position'].nunique()} positions, {df['season'].nunique()} seasons ({sorted(df['season'].unique())})")
print(f"Model training data: {len(df_model)} players (rows with average_cost)")
print(f"Cost range: ${df_model['cost'].min():.0f} - ${df_model['cost'].max():.0f}")
print(f"Excluded: {len(df) - len(df_model)} rows from season(s) {sorted(df[df['average_cost'].isna()]['season'].unique())} (no average_cost)")



# COMMAND ----------

# --- Phase 4: Feature Ablation Study ---
# FIX: Cast adp from Decimal to float, and exclude seasons without average_cost data
# (2025 has NULL average_cost for all rows — including it with fillna corrupts the feature)

# Cast adp to float globally (it's stored as Decimal/object from Spark)
df['adp'] = df['adp'].astype(float)

# Train on seasons with native average_cost data (exclude 2024 holdout AND 2025 which lacks avg_cost)
train_mask = (df['season'] != 2024) & (df['average_cost'].notna())
hold_mask = df['season'] == 2024

df_train = df[train_mask].copy()
df_hold = df[hold_mask].copy()

y_train = df_train['cost'].values
y_hold = df_hold['cost'].values

print(f"Train: {len(df_train)} rows (seasons {sorted(df_train['season'].unique())})")
print(f"Holdout: {len(df_hold)} rows (season 2024)")
print(f"Holdout average_cost coverage: {df_hold['average_cost'].notna().sum()}/{len(df_hold)} ({df_hold['average_cost'].notna().mean():.0%})")
print(f"Holdout positions: {dict(df_hold['player_position'].value_counts())}")
print(f"\nData types: adp={df_train['adp'].dtype}, average_cost={df_train['average_cost'].dtype}")
print(f"Correlation sanity check: average_cost vs cost = {df_train['average_cost'].corr(df_train['cost']):.3f}")

# COMMAND ----------

# --- Phase 4: Feature Ablation Study ---
# FIX: Cast adp from Decimal to float, and exclude seasons without average_cost data
# (2025 has NULL average_cost for all rows — including it with fillna corrupts the feature)

# Cast adp to float globally (it's stored as Decimal/object from Spark)
df['adp'] = df['adp'].astype(float)

# Train on seasons with native average_cost data (exclude 2024 holdout AND 2025 which lacks avg_cost)
train_mask = (df['season'] != 2024) & (df['average_cost'].notna())
hold_mask = df['season'] == 2024

df_train = df[train_mask].copy()
df_hold = df[hold_mask].copy()

y_train = df_train['cost'].values
y_hold = df_hold['cost'].values

print(f"Train: {len(df_train)} rows (seasons {sorted(df_train['season'].unique())})")
print(f"Holdout: {len(df_hold)} rows (season 2024)")
print(f"Holdout average_cost coverage: {df_hold['average_cost'].notna().sum()}/{len(df_hold)} ({df_hold['average_cost'].notna().mean():.0%})")
print(f"Holdout positions: {dict(df_hold['player_position'].value_counts())}")
print(f"\nData types: adp={df_train['adp'].dtype}, average_cost={df_train['average_cost'].dtype}")
print(f"Correlation sanity check: average_cost vs cost = {df_train['average_cost'].corr(df_train['cost']):.3f}")

# COMMAND ----------

from sklearn.metrics import mean_absolute_error

def train_and_evaluate_variant(name, features_list, numeric_list, df_train, df_hold, y_train, y_hold):
    """
    Train a conformal + GP ensemble on given features, evaluate on holdout.
    Returns per-position and overall metrics.
    """
    X_tr = df_train[features_list].copy()
    X_ho = df_hold[features_list].copy()
    
    # Preprocessor
    prep = ColumnTransformer([
        ('pos_encode', OneHotEncoder(drop='first', sparse_output=False), ['player_position'])
    ], remainder='passthrough')
    
    X_tr_enc = prep.fit_transform(X_tr)
    X_ho_enc = prep.transform(X_ho)
    
    # Conformal: 80/20 split for calibration
    rng = np.random.RandomState(42)
    n_cal = len(y_train) // 5
    cal_idx = rng.choice(len(y_train), n_cal, replace=False)
    fit_idx = np.setdiff1d(np.arange(len(y_train)), cal_idx)
    
    gb = GradientBoostingRegressor(
        n_estimators=200, max_depth=3, learning_rate=0.05,
        min_samples_leaf=5, random_state=42
    )
    gb.fit(X_tr_enc[fit_idx], y_train[fit_idx])
    
    # Position-specific conformal quantiles
    q_hat = {}
    for pos in ['QB', 'RB', 'WR', 'TE']:
        pos_cal_mask = df_train.iloc[cal_idx]['player_position'] == pos
        pos_cal_i = cal_idx[pos_cal_mask.values]
        if len(pos_cal_i) > 0:
            cal_preds = gb.predict(X_tr_enc[pos_cal_i])
            cal_scores = np.abs(y_train[pos_cal_i] - cal_preds)
            q_hat[pos] = np.quantile(cal_scores, 0.80)
    
    # GP per-position
    gp_models = {}
    gp_scalers = {}
    for pos in ['QB', 'RB', 'WR', 'TE']:
        pos_mask = (df_train['player_position'] == pos).values
        X_pos = df_train.loc[pos_mask, numeric_list].values
        y_pos = y_train[pos_mask]
        if len(y_pos) < 5:
            continue
        scaler = StandardScaler()
        X_pos_sc = scaler.fit_transform(X_pos)
        kernel = ConstantKernel(30.0, (1, 200)) * RBF(length_scale=4.0, length_scale_bounds=(0.5, 25)) + WhiteKernel(noise_level=8, noise_level_bounds=(1, 80))
        gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=3, random_state=42, alpha=1e-6)
        gp.fit(X_pos_sc, y_pos)
        gp_models[pos] = gp
        gp_scalers[pos] = scaler
    
    # Evaluate on holdout using conformal (since it's position-general and comparable)
    results = []
    for pos in ['QB', 'RB', 'WR', 'TE']:
        pos_ho_mask = (df_hold['player_position'] == pos).values
        if pos_ho_mask.sum() == 0:
            continue
        
        X_pos_ho_enc = X_ho_enc[pos_ho_mask]
        y_pos_ho = y_hold[pos_ho_mask]
        
        # Conformal predictions
        meds_conf = gb.predict(X_pos_ho_enc)
        q = q_hat.get(pos, 5.0)
        lows_conf = meds_conf - q
        highs_conf = meds_conf + q
        
        # GP predictions (if available)
        if pos in gp_models:
            X_pos_ho_num = df_hold.loc[pos_ho_mask, numeric_list].values
            X_pos_ho_sc = gp_scalers[pos].transform(X_pos_ho_num)
            mu_gp, sigma_gp = gp_models[pos].predict(X_pos_ho_sc, return_std=True)
            lows_gp = mu_gp - 1.28 * sigma_gp
            highs_gp = mu_gp + 1.28 * sigma_gp
            # Use ensemble logic: pick best model per position
            meds = mu_gp if pos in ['RB', 'WR', 'TE'] else meds_conf
            lows = lows_gp if pos in ['RB', 'WR', 'TE'] else lows_conf
            highs = highs_gp if pos in ['RB', 'WR', 'TE'] else highs_conf
        else:
            meds, lows, highs = meds_conf, lows_conf, highs_conf
        
        coverage = ((y_pos_ho >= lows) & (y_pos_ho <= highs)).mean()
        width = (highs - lows).mean()
        mae = mean_absolute_error(y_pos_ho, meds)
        results.append({'position': pos, 'coverage': coverage, 'width': width, 'mae': mae, 'n': pos_ho_mask.sum()})
    
    results_df = pd.DataFrame(results)
    overall = {
        'coverage': np.average(results_df['coverage'], weights=results_df['n']),
        'width': np.average(results_df['width'], weights=results_df['n']),
        'mae': np.average(results_df['mae'], weights=results_df['n']),
    }
    return results_df, overall

# --- Define the 3 variants ---
variants = {
    'Full (rank + adp + avg_cost)': {
        'features': ['position_rank', 'adp', 'average_cost', 'player_position'],
        'numeric': ['position_rank', 'adp', 'average_cost'],
    },
    'No Market (rank + adp only)': {
        'features': ['position_rank', 'adp', 'player_position'],
        'numeric': ['position_rank', 'adp'],
    },
    'Simplified (avg_cost + position)': {
        'features': ['average_cost', 'player_position'],
        'numeric': ['average_cost'],
    },
}

# No fillna needed: training data is filtered to rows with native average_cost,
# and holdout (2024) has 100% coverage. All features are already float64.
df_train_clean = df_train.copy()
df_hold_clean = df_hold.copy()

print("Phase 4 Ablation — 2024 Holdout Evaluation")
print("=" * 60)

summary_rows = []
for vname, vcfg in variants.items():
    per_pos, overall = train_and_evaluate_variant(
        vname, vcfg['features'], vcfg['numeric'],
        df_train_clean, df_hold_clean, y_train, y_hold
    )
    print(f"\n{vname}:")
    print(f"  Overall: Coverage={overall['coverage']:.1%}  MAE=${overall['mae']:.1f}  Width=${overall['width']:.1f}")
    for _, r in per_pos.iterrows():
        print(f"    {r['position']}: Coverage={r['coverage']:.1%}  MAE=${r['mae']:.1f}  Width=${r['width']:.1f}  (n={int(r['n'])})")
    summary_rows.append({'Variant': vname, 'Coverage': f"{overall['coverage']:.1%}", 'MAE': f"${overall['mae']:.1f}", 'Width': f"${overall['width']:.1f}"})

print("\n" + "=" * 60)
print("\nSummary Comparison:")
summary_df = pd.DataFrame(summary_rows)
display(summary_df)

# COMMAND ----------

# --- Feature Importance Analysis ---
# Check whether average_cost dominates or complements position_rank/adp

from sklearn.inspection import permutation_importance

# Train the full-feature GBR on clean training data for importance analysis
prep_full = ColumnTransformer([
    ('pos_encode', OneHotEncoder(drop='first', sparse_output=False), ['player_position'])
], remainder='passthrough')

X_tr_full_enc = prep_full.fit_transform(df_train_clean[['position_rank', 'adp', 'average_cost', 'player_position']])
X_ho_full_enc = prep_full.transform(df_hold_clean[['position_rank', 'adp', 'average_cost', 'player_position']])

gb_full = GradientBoostingRegressor(
    n_estimators=200, max_depth=3, learning_rate=0.05,
    min_samples_leaf=5, random_state=42
)
gb_full.fit(X_tr_full_enc, y_train)

# Permutation importance on holdout
perm_imp = permutation_importance(gb_full, X_ho_full_enc, y_hold, n_repeats=20, random_state=42, scoring='neg_mean_absolute_error')

# Feature names after encoding
pos_encoder = prep_full.named_transformers_['pos_encode']
pos_features = [f"position_{c}" for c in pos_encoder.categories_[0][1:]]  # drop='first'
feature_names = pos_features + ['position_rank', 'adp', 'average_cost']

print("Feature Importance (permutation, holdout MAE impact):")
print("-" * 50)
imp_df = pd.DataFrame({
    'feature': feature_names,
    'importance_mean': perm_imp.importances_mean,
    'importance_std': perm_imp.importances_std,
}).sort_values('importance_mean', ascending=False)

for _, row in imp_df.iterrows():
    print(f"  {row['feature']:20s}  {row['importance_mean']:+.2f} ± {row['importance_std']:.2f}")

# --- Collinearity ---
print("\nCorrelation Matrix (numeric features, training data):")
corr = df_train_clean[['position_rank', 'adp', 'average_cost', 'cost']].corr()
display(corr.round(3))

# --- Over-reliance check ---
# If simplified model (avg_cost only) matches full model within 1 MAE dollar, 
# the extra features aren't helping much
print("\nOver-reliance Assessment:")
full_mae = float(summary_df[summary_df['Variant'].str.startswith('Full')]['MAE'].values[0].replace('$', ''))
simp_mae = float(summary_df[summary_df['Variant'].str.startswith('Simp')]['MAE'].values[0].replace('$', ''))
delta = simp_mae - full_mae
if abs(delta) <= 1.0:
    print(f"  ⚠️ Simplified model within ${abs(delta):.1f} MAE of full model — average_cost alone may suffice.")
    print(f"  → Consider dropping position_rank and adp for parsimony.")
elif delta > 1.0:
    print(f"  ✓ Full model improves MAE by ${delta:.1f} over simplified — additional features contribute value.")
    print(f"  → Keep position_rank + adp alongside average_cost.")
else:
    print(f"  ✓ Full model is ${abs(delta):.1f} worse — simplified model is preferable (less overfitting).")

# COMMAND ----------

# --- Feature Importance Analysis ---
# Check whether average_cost dominates or complements position_rank/adp

from sklearn.inspection import permutation_importance

# Train the full-feature GBR on clean training data for importance analysis
prep_full = ColumnTransformer([
    ('pos_encode', OneHotEncoder(drop='first', sparse_output=False), ['player_position'])
], remainder='passthrough')

X_tr_full_enc = prep_full.fit_transform(df_train_clean[['position_rank', 'adp', 'average_cost', 'player_position']])
X_ho_full_enc = prep_full.transform(df_hold_clean[['position_rank', 'adp', 'average_cost', 'player_position']])

gb_full = GradientBoostingRegressor(
    n_estimators=200, max_depth=3, learning_rate=0.05,
    min_samples_leaf=5, random_state=42
)
gb_full.fit(X_tr_full_enc, y_train)

# Permutation importance on holdout
perm_imp = permutation_importance(gb_full, X_ho_full_enc, y_hold, n_repeats=20, random_state=42, scoring='neg_mean_absolute_error')

# Feature names after encoding
pos_encoder = prep_full.named_transformers_['pos_encode']
pos_features = [f"position_{c}" for c in pos_encoder.categories_[0][1:]]  # drop='first'
feature_names = pos_features + ['position_rank', 'adp', 'average_cost']

print("Feature Importance (permutation, holdout MAE impact):")
print("-" * 50)
imp_df = pd.DataFrame({
    'feature': feature_names,
    'importance_mean': perm_imp.importances_mean,
    'importance_std': perm_imp.importances_std,
}).sort_values('importance_mean', ascending=False)

for _, row in imp_df.iterrows():
    print(f"  {row['feature']:20s}  {row['importance_mean']:+.2f} ± {row['importance_std']:.2f}")

# --- Collinearity ---
print("\nCorrelation Matrix (numeric features, training data):")
corr = df_train_clean[['position_rank', 'adp', 'average_cost', 'cost']].corr()
display(corr.round(3))

# --- Over-reliance check ---
# If simplified model (avg_cost only) matches full model within 1 MAE dollar, 
# the extra features aren't helping much
print("\nOver-reliance Assessment:")
full_mae = float(summary_df[summary_df['Variant'].str.startswith('Full')]['MAE'].values[0].replace('$', ''))
simp_mae = float(summary_df[summary_df['Variant'].str.startswith('Simp')]['MAE'].values[0].replace('$', ''))
delta = simp_mae - full_mae
if abs(delta) <= 1.0:
    print(f"  ⚠️ Simplified model within ${abs(delta):.1f} MAE of full model — average_cost alone may suffice.")
    print(f"  → Consider dropping position_rank and adp for parsimony.")
elif delta > 1.0:
    print(f"  ✓ Full model improves MAE by ${delta:.1f} over simplified — additional features contribute value.")
    print(f"  → Keep position_rank + adp alongside average_cost.")
else:
    print(f"  ✓ Full model is ${abs(delta):.1f} worse — simplified model is preferable (less overfitting).")

# COMMAND ----------

