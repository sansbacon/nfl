# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC ## Batch Inference
# MAGIC
# MAGIC Load the registered model and generate predictions for the current season.

# COMMAND ----------

# MAGIC %md ## Setup

# COMMAND ----------

import mlflow.pyfunc
import pandas as pd
import pyspark.sql.functions as F
from pyspark.sql.window import Window

# COMMAND ----------

dbutils.widgets.text("SEASON", "2026", "Inference Season")
dbutils.widgets.text("MODEL_NAME", "nfl.default.auction_price_ensemble")

# COMMAND ----------

SEASON = int(dbutils.widgets.get("SEASON"))
MODEL_NAME = dbutils.widgets.get("MODEL_NAME")
assert all((SEASON, MODEL_NAME)), 'Specify all parameters'

# COMMAND ----------

# MAGIC %md ## Load Model and Data

# COMMAND ----------

loaded_model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")

# COMMAND ----------

# Combine auction data from vw_draft_picks with Yahoo ADP
w_pick = Window.partitionBy('position').orderBy('average_pick')          # low pick = high rank
w_cost = Window.partitionBy('position').orderBy(F.desc('average_cost'))  # high cost = high rank

df = (
  spark.table('nfl.yh.vw_adp')
  .where(F.col('season') == SEASON)
  .where(F.col('position').isin(['QB', 'RB', 'WR', 'TE']))
  .withColumn('rank_by_pick', F.row_number().over(w_pick))
  .withColumn('rank_by_cost', F.row_number().over(w_cost))
  .withColumn('avg_rank', (F.col('rank_by_pick') + F.col('rank_by_cost')) / 2)
  .withColumn('position_rank', F.row_number().over(Window.partitionBy('position').orderBy('avg_rank')))
).toPandas()

# COMMAND ----------

# MAGIC %md ## Get Predictions

# COMMAND ----------

# Build inference input from current season's ADP data
if df.empty:
    print(f"No data found for season {SEASON}")
    dbutils.notebook.exit(f"No data for season {SEASON}")

inference_input = df[['position', 'position_rank', 'average_cost']].copy()
inference_input.index = df['player_key']
inference_input.index.name = 'player_key'

# COMMAND ----------

# Get predictions — model returns results in input row order
projections = loaded_model.predict(inference_input)
projections.index = inference_input.index

# COMMAND ----------

# Join predictions back on player_key index
result = (
  df
  .set_index('player_key')
  .join(projections, how='left')
  .sort_values(['position', 'position_rank']).reset_index()
  .assign(**{'range': lambda x: x.low.astype('str') + ' - ' + x.high.astype(str)})
  .assign(player_id=lambda x: x['player_key'].str.split('.').str[-1])
)

print(f"\n{SEASON} Auction Price Projections ({len(result)} players)")
print("=" * 60)
#display(result.loc[:, ['player', 'position', 'average_cost', 'low', 'median', 'high']])

# COMMAND ----------

# --- Persist projections to Delta table ---
fqn = 'nfl.default.auction_price_projections'

(
  spark.createDataFrame(result)
  .write
  .mode("overwrite")
  .option("overwriteSchema", "true")
  .saveAsTable(fqn)
)

print(f"\u2713 Wrote {len(result)} projections to {fqn}")

# COMMAND ----------

