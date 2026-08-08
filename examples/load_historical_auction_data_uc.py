# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# dependencies = [
#   "polars",
#   "requests-oauthlib",
# ]
# ///
# DBTITLE 1,Load Historical Auction → UC
# MAGIC %md
# MAGIC # Load Historical Auction Data → Unity Catalog
# MAGIC
# MAGIC Reads `historical_auction_values.csv` from a UC Volume, resolves player names against the `nfl.yh.player` UC table, and writes the result to `nfl.yh` Delta tables.
# MAGIC
# MAGIC **Prerequisite:** Run `load_yahoo_data_uc` first to populate `nfl.yh.player`.

# COMMAND ----------

# MAGIC %pip install polars requests-oauthlib

# COMMAND ----------

# DBTITLE 1,Setup & Imports
import sys
from pathlib import Path

import polars as pl

from nfl.common.utils import find_project_root

project_root = find_project_root()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from nfl.yahoo_fantasy.historical_auction import (
    load_historical_auction_values,
    resolve_historical_players,
)
from nfl.storage_uc import UCTableConfig, persist_to_uc_tables

pl.Config.set_tbl_rows(50)
pl.Config.set_fmt_str_lengths(100)

# COMMAND ----------

# DBTITLE 1,Configuration
# --- Configuration ---
CATALOG = "nfl"
SCHEMA = "yh"
VOLUME_PATH = "/Volumes/nfl/yh/yh_volume"
CSV_FILENAME = "historical_auction_values.csv"

MIN_CONFIDENCE = 0.97
REVIEW_CONFIDENCE = 0.90
WRITE_MODE = "overwrite"
UC_DRY_RUN = False

assert all((CATALOG, SCHEMA)), f'ERROR: {CATALOG=} and {SCHEMA=} must be set'

CSV_PATH = Path('/Volumes/nfl/default/nfl_volume/historical_auction_values.csv')
print(f"CSV source: {CSV_PATH}")
print(f"UC Target: {CATALOG}.{SCHEMA} (mode={WRITE_MODE})")

# COMMAND ----------

# DBTITLE 1,Load Yahoo Players from UC
# Load Yahoo player table from UC for name resolution
yahoo_player_spark = spark.table(f"{CATALOG}.{SCHEMA}.player")
yahoo_player_df = pl.from_pandas(yahoo_player_spark.toPandas())

print(f"Yahoo players from UC: {yahoo_player_df.height}")

# COMMAND ----------

# DBTITLE 1,Resolve Player Names
# Load and resolve historical auction data
historical_raw = load_historical_auction_values(CSV_PATH)

historical_import = resolve_historical_players(
    raw_df=historical_raw,
    yahoo_player_df=yahoo_player_df,
    min_confidence=MIN_CONFIDENCE,
    review_confidence=REVIEW_CONFIDENCE,
)

resolved_df = historical_import.resolved
queue_df = historical_import.match_queue

print("Import summary")
print(f"  raw rows: {historical_raw.height}")
print(f"  resolved rows: {resolved_df.height}")
print(f"  queue rows: {queue_df.height}")

if queue_df.height > 0:
    print("\nUnresolved rows needing review:")
    print(queue_df.head(20))

# COMMAND ----------

# DBTITLE 1,Persist to UC Tables
# Write historical auction tables to Unity Catalog
frames_to_write = {
    "historical_auction_values_raw": historical_raw,
    "historical_auction_values_resolved": resolved_df,
    "historical_auction_values_match_queue": queue_df,
}

uc_config = UCTableConfig(
    catalog=CATALOG,
    schema=SCHEMA,
    write_mode=WRITE_MODE,
)

results = persist_to_uc_tables(frames_to_write, config=uc_config, dry_run=UC_DRY_RUN)

print("UC Write Results:")
for wr in results:
    print(f"  {wr.target}: {wr.written_rows} rows ({wr.mode})")

# COMMAND ----------

# DBTITLE 1,Verify UC Tables
# Verify: read back from UC
for table_name in ["historical_auction_values_raw", "historical_auction_values_resolved"]:
    fq = f"{CATALOG}.{SCHEMA}.{table_name}"
    count = spark.table(fq).count()
    print(f"{fq}: {count} rows")

# COMMAND ----------

