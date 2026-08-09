# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC ## Draft Pick Availability Model
# MAGIC
# MAGIC Parametric location-scale model (logistic distribution) trained on Best Ball Mania drafts 2021-2024.
# MAGIC
# MAGIC Predicts P(player still available at pick X) given ADP, position, and positional ADP rank.
# MAGIC
# MAGIC **Outputs:**
# MAGIC - Coefficient table: `nfl.ud.draft_availability_coefficients`
# MAGIC - UC Python UDF: `nfl.ud.p_available(adp, position, pos_adp_rank, target_pick)`

# COMMAND ----------

# DBTITLE 1,Imports
import numpy as np
import pandas as pd
from pyspark.sql import functions as F, Window
from scipy.optimize import minimize
from scipy.special import expit

# COMMAND ----------

# DBTITLE 1,Model Functions
FEATURE_NAMES = ["intercept", "adp", "log_adp", "pos_adp_rank", "is_QB", "is_RB", "is_TE"]
N_FEATURES = len(FEATURE_NAMES)
MAX_PICK = 216  # BBM draft size


def build_features(data):
    """Build feature matrix for the location-scale model."""
    X = pd.DataFrame({
        "intercept": 1.0,
        "adp": data["adp"] / MAX_PICK,
        "log_adp": np.log(data["adp"].clip(lower=1)) / np.log(MAX_PICK),
        "pos_adp_rank": data["pos_adp_rank"] / 50.0,
        "is_QB": (data["position_name"] == "QB").astype(float),
        "is_RB": (data["position_name"] == "RB").astype(float),
        "is_TE": (data["position_name"] == "TE").astype(float),
    })
    return X.values


def neg_log_likelihood(params, X, y):
    """Negative log-likelihood for Logistic(mu, s) location-scale model.

    params[:N_FEATURES] = beta (location coefficients)
    params[N_FEATURES:] = gamma (log-scale coefficients)
    """
    beta = params[:N_FEATURES]
    gamma = params[N_FEATURES:]

    mu = X @ beta
    log_s = X @ gamma
    s = np.exp(log_s)

    # Logistic log-PDF: -z - log(s) - 2*log(1 + exp(-z))
    z = (y - mu) / s
    log_pdf = -z - log_s - 2 * np.log(1 + np.exp(-z))

    return -np.mean(log_pdf)

# COMMAND ----------

# DBTITLE 1,Data Load
raw = (
    spark.table("nfl.ud.bbm_drafts")
    .select(
        "draft_id",
        F.col("draft_time").cast("timestamp").alias("draft_time"),
        "player_id",
        "player_name",
        F.when(F.col("position_name") == "FB", "RB")
         .otherwise(F.col("position_name"))
         .alias("position_name"),
        F.col("projection_adp").cast("double").alias("adp"),
        F.col("overall_pick_number").cast("int").alias("overall_pick"),
    )
    .filter(
        F.col("projection_adp").isNotNull()
        & (F.col("projection_adp") != "NA")
        & F.col("overall_pick_number").isNotNull()
        & (F.col("overall_pick_number") != "NA")
    )
    .withColumn("year", F.year("draft_time"))
    .withColumn("pick_diff", F.col("overall_pick") - F.col("adp"))
)

# Position ADP rank per draft
pos_window = Window.partitionBy("draft_id", "position_name").orderBy("adp")
df = raw.withColumn("pos_adp_rank", F.row_number().over(pos_window))

# COMMAND ----------

# DBTITLE 1,Year-Balanced Sample + Train/Test Split
df_clean = df.filter(
    F.col("position_name").isin("QB", "RB", "WR", "TE")
    & (F.col("adp") > 0)
    & (F.col("adp") <= MAX_PICK)
)

# Cap each year at the smallest year's count for balance
min_year_count = df_clean.groupBy("year").count().agg(F.min("count")).collect()[0][0]
print(f"Sampling {min_year_count:,} rows per year")

sampled = (
    df_clean
    .withColumn("row_num", F.row_number().over(Window.partitionBy("year").orderBy(F.rand(seed=42))))
    .filter(F.col("row_num") <= min_year_count)
    .drop("row_num")
)

pdf = sampled.select(
    "adp", "overall_pick", "pick_diff", "position_name", "pos_adp_rank", "year"
).toPandas()

print(f"Total sampled: {len(pdf):,}")
print(f"\nYear distribution:\n{pdf['year'].value_counts().sort_index()}")
print(f"\nPosition distribution:\n{pdf['position_name'].value_counts()}")

# 80/20 split stratified by year
from sklearn.model_selection import train_test_split

train_pdf, test_pdf = train_test_split(pdf, test_size=0.2, random_state=42, stratify=pdf["year"])
print(f"\nTrain: {len(train_pdf):,} | Test: {len(test_pdf):,}")

# COMMAND ----------

# DBTITLE 1,Fit MLE
X_train = build_features(train_pdf)
y_train = train_pdf["pick_diff"].values

# Initial params: intercept-only location (0), scale ~ log(4.5) from EDA
init_beta = np.zeros(N_FEATURES)
init_gamma = np.zeros(N_FEATURES)
init_gamma[0] = np.log(4.5)

init_params = np.concatenate([init_beta, init_gamma])

print(f"Fitting {2 * N_FEATURES} parameters on {len(y_train):,} observations...")
result = minimize(
    neg_log_likelihood,
    init_params,
    args=(X_train, y_train),
    method="L-BFGS-B",
    options={"maxiter": 500, "disp": True},
)

assert result.success, f"ERROR: Optimization failed: {result.message}"

beta_hat = result.x[:N_FEATURES]
gamma_hat = result.x[N_FEATURES:]

print("\n--- Location (mu) coefficients ---")
for name, b in zip(FEATURE_NAMES, beta_hat):
    print(f"  {name:15s}: {b:+.4f}")

print("\n--- Log-Scale (log s) coefficients ---")
for name, g in zip(FEATURE_NAMES, gamma_hat):
    print(f"  {name:15s}: {g:+.4f} (scale: {np.exp(g):.3f})")

# COMMAND ----------

# DBTITLE 1,Validation
from sklearn.metrics import log_loss
from sklearn.calibration import calibration_curve


def predict_availability_batch(data, beta, gamma, target_picks):
    """Predict P(available at target_pick) using truncated logistic."""
    X = build_features(data)
    mu = X @ beta
    log_s = X @ gamma
    s = np.exp(log_s)

    adp = data["adp"].values
    threshold = target_picks - adp
    lower = 1 - adp
    upper = MAX_PICK - adp

    def logistic_cdf(x, mu_arr, s_arr):
        return expit((x - mu_arr) / s_arr)

    F_upper = logistic_cdf(upper, mu, s)
    F_lower = logistic_cdf(lower, mu, s)
    F_thresh = logistic_cdf(threshold, mu, s)

    denom = F_upper - F_lower
    denom = np.where(denom < 1e-12, 1e-12, denom)
    p = (F_upper - F_thresh) / denom
    return np.clip(p, 0.0, 1.0)


# Evaluate: for each test row, predict P(available at actual pick)
# If actual_pick == overall_pick, the player was NOT available at that pick
# (they were taken). Use pick - 1 as the "still available" threshold.
test_target = test_pdf["overall_pick"].values
y_true = np.zeros(len(test_pdf))  # was player available at their pick? No — they were taken there.

# Instead: check availability at pick - 1 (should be ~1) and pick + 1 (should be ~0)
p_before = predict_availability_batch(test_pdf, beta_hat, gamma_hat, test_target - 1)
p_at = predict_availability_batch(test_pdf, beta_hat, gamma_hat, test_target)

print(f"Mean P(available at pick before taken): {p_before.mean():.4f} (ideal: ~1.0)")
print(f"Mean P(available at pick where taken):  {p_at.mean():.4f} (ideal: ~0.5)")

# Binary test: was player available at pick X (where X < actual_pick)?
# Create binary labels: available if actual_pick > target_pick
np.random.seed(42)
random_picks = np.random.randint(1, MAX_PICK + 1, size=len(test_pdf))
y_binary = (test_pdf["overall_pick"].values > random_picks).astype(float)
p_pred = predict_availability_batch(test_pdf, beta_hat, gamma_hat, random_picks)

print(f"\nBinary availability prediction (random target picks):")
print(f"  Log-loss: {log_loss(y_binary, p_pred):.4f}")
print(f"  Accuracy: {(np.round(p_pred) == y_binary).mean():.4f}")

# COMMAND ----------

# DBTITLE 1,Persist Coefficients
from datetime import datetime, timezone

coeff_rows = []
for name, b, g in zip(FEATURE_NAMES, beta_hat, gamma_hat):
    coeff_rows.append({"param_type": "beta", "feature_name": name, "value": float(b)})
    coeff_rows.append({"param_type": "gamma", "feature_name": name, "value": float(g)})

coeff_df = spark.createDataFrame(coeff_rows).withColumn(
    "fitted_at", F.lit(datetime.now(timezone.utc))
)

coeff_df.write.mode("overwrite").saveAsTable("nfl.ud.draft_availability_coefficients")
print("Coefficients written to nfl.ud.draft_availability_coefficients")
coeff_df.display()

# COMMAND ----------

# DBTITLE 1,Register UC Python UDF
# Format coefficient arrays as Python literals for embedding in UDF body
beta_str = ", ".join(f"{v:.10f}" for v in beta_hat)
gamma_str = ", ".join(f"{v:.10f}" for v in gamma_hat)

create_udf_sql = f"""
CREATE OR REPLACE FUNCTION nfl.ud.p_available(
    adp DOUBLE COMMENT 'Player ADP (1-216)',
    position STRING COMMENT 'Position: QB, RB, WR, or TE',
    pos_adp_rank INT COMMENT 'ADP rank within position (e.g. WR12 = 12)',
    target_pick INT COMMENT 'Overall pick number to check availability at (1-216)'
)
RETURNS DOUBLE
COMMENT 'Probability that a player is still available at target_pick, based on a truncated logistic location-scale model trained on BBM 2021-2024.'
LANGUAGE PYTHON
AS $$
import math

BETA = [{beta_str}]
GAMMA = [{gamma_str}]
MAX_PICK = 216

def sigmoid(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    else:
        ex = math.exp(x)
        return ex / (1.0 + ex)

# Build feature vector (same normalization as training)
x = [
    1.0,
    adp / MAX_PICK,
    math.log(max(adp, 1)) / math.log(MAX_PICK),
    pos_adp_rank / 50.0,
    float(position == "QB"),
    float(position == "RB"),
    float(position == "TE"),
]

mu = sum(xi * bi for xi, bi in zip(x, BETA))
s = math.exp(sum(xi * gi for xi, gi in zip(x, GAMMA)))

# Truncated logistic: P(available at Y) = [F(upper) - F(threshold)] / [F(upper) - F(lower)]
lower = 1 - adp
upper = MAX_PICK - adp
threshold = target_pick - adp

if target_pick <= 0:
    return 1.0
if target_pick > MAX_PICK:
    return 0.0

def logistic_cdf(val):
    return sigmoid((val - mu) / s)

F_upper = logistic_cdf(upper)
F_lower = logistic_cdf(lower)
F_thresh = logistic_cdf(threshold)

denom = F_upper - F_lower
if denom < 1e-12:
    return 0.5

p = (F_upper - F_thresh) / denom
return max(0.0, min(1.0, p))
$$
"""

spark.sql(create_udf_sql)
print("Registered UC function: nfl.ud.p_available()")

# COMMAND ----------

# DBTITLE 1,Smoke Test
# Quick sanity checks
result = spark.sql("""
    SELECT
        nfl.ud.p_available(12.0, 'RB', 3, 5) AS rb3_at_5,
        nfl.ud.p_available(12.0, 'RB', 3, 12) AS rb3_at_12,
        nfl.ud.p_available(12.0, 'RB', 3, 24) AS rb3_at_24,
        nfl.ud.p_available(100.0, 'WR', 25, 80) AS wr25_at_80,
        nfl.ud.p_available(100.0, 'WR', 25, 100) AS wr25_at_100,
        nfl.ud.p_available(100.0, 'WR', 25, 120) AS wr25_at_120
""")
result.display()
