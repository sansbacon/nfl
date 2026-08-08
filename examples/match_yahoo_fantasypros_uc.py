# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# dependencies = [
#   "polars",
#   "lxml",
# ]
# ///
# DBTITLE 1,Match Yahoo ↔ FantasyPros → UC
# MAGIC %md
# MAGIC # Match Yahoo ↔ FantasyPros Players → Unity Catalog
# MAGIC
# MAGIC Builds a Yahoo↔FantasyPros player crosswalk by reading the Yahoo player table from UC (`nfl.yh.player`), running the FantasyPros matching pipeline, and writing the crosswalk to `nfl.fp`.
# MAGIC
# MAGIC **Prerequisite:** Run `load_yahoo_data_uc` first to populate `nfl.yh.player`.

# COMMAND ----------

# MAGIC %pip install polars lxml

# COMMAND ----------

# DBTITLE 1,Setup & Imports
import sys
from datetime import date
from pathlib import Path

import polars as pl

from nfl.common.utils import find_project_root

project_root = find_project_root()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from nfl.fantasypros_fantasy import PipelineConfig, fp_adp_records_to_fp_players, run_pipeline
from nfl.fantasypros_fantasy.storage.unity_catalog import FantasyProsUCTableConfig
from nfl.storage_uc import UCTableConfig, persist_to_uc_tables

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
SEASON = 2025

# UC configuration
CATALOG = "nfl"
YAHOO_SCHEMA = "yh"
FP_SCHEMA = "fp"
WRITE_MODE = "overwrite"
UC_DRY_RUN = False

# Backfill prior seasons to catch players no longer active
BACKFILL_SEASONS = [2021, 2022, 2023, 2024]

assert all((CATALOG, YAHOO_SCHEMA, FP_SCHEMA)), f'ERROR: {CATALOG=}, {YAHOO_SCHEMA=}, {FP_SCHEMA=} must be set'

print(f"Season: {SEASON}")
print(f"Yahoo source: {CATALOG}.{YAHOO_SCHEMA}.player_deduped")
print(f"FP target: {CATALOG}.{FP_SCHEMA} (mode={WRITE_MODE})")

# COMMAND ----------

# DBTITLE 1,Load Yahoo Players from UC
# Read deduplicated Yahoo players (one row per player_id, latest season)
yahoo_player_spark = spark.table(f"{CATALOG}.{YAHOO_SCHEMA}.player_deduped")
yahoo_players = yahoo_player_spark.toPandas().to_dict(orient="records")

print(f"Yahoo players loaded from UC (deduped): {len(yahoo_players)}")

# COMMAND ----------

# DBTITLE 1,Run Matching Pipeline → UC
# Read FP players from UC (already loaded by load_fantasypros_adp_uc)
from nfl.fantasypros_fantasy.matching import build_fp_yahoo_crosswalk

fp_adp_spark = spark.table(f"{CATALOG}.{FP_SCHEMA}.fp_adp")
fp_adp_records = fp_adp_spark.filter(f"season = {SEASON}").toPandas().to_dict(orient="records")
print(f"FP ADP players from UC (season={SEASON}): {len(fp_adp_records)}")

# Convert FP ADP table records to fp_player format for the crosswalk builder
fp_players = fp_adp_records_to_fp_players(fp_adp_records)

# Build crosswalk
crosswalk_records = build_fp_yahoo_crosswalk(
    fp_players=fp_players,
    yahoo_players=yahoo_players,
)
crosswalk_df = pl.DataFrame(crosswalk_records) if crosswalk_records else pl.DataFrame()

print(f"Crosswalk matches: {crosswalk_df.height}")
if crosswalk_df.height > 0 and "match_method" in crosswalk_df.columns:
    print("\nMatch method breakdown:")
    print(crosswalk_df.group_by("match_method").agg(pl.len()))

# COMMAND ----------

# DBTITLE 1,Verify UC Crosswalk
# Verify crosswalk table in UC
fq_crosswalk = f"{CATALOG}.{FP_SCHEMA}.nfl_fp_yahoo_player_map"
try:
    count = spark.table(fq_crosswalk).count()
    print(f"{fq_crosswalk}: {count} rows")
    spark.table(fq_crosswalk).show(10, truncate=False)
except Exception as e:
    print(f"{fq_crosswalk}: not found ({e})")

# COMMAND ----------

# DBTITLE 1,Persist Crosswalk to UC
# Write crosswalk to Unity Catalog
uc_results = persist_to_uc_tables(
    frames={"nfl_fp_yahoo_player_map": crosswalk_df},
    config=UCTableConfig(
        catalog=CATALOG,
        schema=FP_SCHEMA,
        write_mode=WRITE_MODE,
    ),
    dry_run=UC_DRY_RUN,
)
for wr in uc_results:
    print(f"  {wr.target}: {wr.written_rows} rows ({wr.mode})")