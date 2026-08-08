# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# dependencies = [
#   "polars",
#   "lxml",
# ]
# ///
# DBTITLE 1,Load FantasyPros ADP → Unity Catalog
# MAGIC %md
# MAGIC # Load FantasyPros ADP → Unity Catalog
# MAGIC
# MAGIC Pulls FantasyPros NFL ADP snapshots for multiple seasons and writes them as Delta tables in `nfl.fp`.

# COMMAND ----------

# DBTITLE 1,Cell 2
# MAGIC %pip install polars lxml

# COMMAND ----------

# DBTITLE 1,Restart Python
dbutils.library.restartPython()

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

from nfl.fantasypros_fantasy import FantasyProsApiClient, PipelineConfig, run_pipeline
from nfl.fantasypros_fantasy.storage.unity_catalog import FantasyProsUCTableConfig

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
SEASONS = list(range(2020, 2026))

# --- Unity Catalog Target ---
CATALOG = "nfl"
SCHEMA = "fp"
WRITE_MODE = "append"  # overwrite | append | merge
UC_DRY_RUN = False

assert all((CATALOG, SCHEMA)), f'ERROR: {CATALOG=} and {SCHEMA=} must be set'

print("Seasons:", SEASONS)
print(f"UC Target: {CATALOG}.{SCHEMA} (mode={WRITE_MODE}, dry_run={UC_DRY_RUN})")

# COMMAND ----------

# DBTITLE 1,Run Pipeline Per Season → UC
# Use FantasyProsApiClient.parse_adp_volume_csv() to parse CSV files from UC Volume.
# The library handles "Player (Bye)" parsing, team/position extraction, and ADP formatting.
from nfl.fantasypros_fantasy.storage.unity_catalog import FantasyProsUCTableConfig, persist_fp_to_uc_tables

VOLUME_PATH = "/Volumes/nfl/default/nfl_volume"
fp_client = FantasyProsApiClient(validate_contracts=False)

all_frames: list[pl.DataFrame] = []

for season in SEASONS:
    csv_path = f"{VOLUME_PATH}/FantasyPros_{season}_Overall_ADP_Rankings.csv"
    data = fp_client.parse_adp_volume_csv(csv_path, season=season)
    adp_df = pl.DataFrame(data.adp_rows)
    player_df = pl.DataFrame(data.players)
    # Attach player_name for convenience when querying in UC
    combined = adp_df.join(
        player_df.select(["fp_player_id", "full_name", "position", "team"]),
        on="fp_player_id",
        how="left",
    ).rename({"full_name": "player_name"})
    all_frames.append(combined)
    print(f"  Season {season}: {combined.height} rows")

# Combine all seasons
final = pl.concat(all_frames, how="diagonal")
print(f"\nTotal combined: {final.height} rows x {final.width} cols")
print(f"Columns: {final.columns}")

# Persist to UC
uc_results = persist_fp_to_uc_tables(
    frames={"fp_adp": final},
    config=FantasyProsUCTableConfig(
        catalog=CATALOG,
        schema=SCHEMA,
        write_mode="overwrite",
    ),
    dry_run=UC_DRY_RUN,
)
for wr in uc_results:
    print(f"  {wr.target}: {wr.written_rows} rows")

# COMMAND ----------

# DBTITLE 1,Verify UC Tables
# Validate: row counts per season
fq = f"{CATALOG}.{SCHEMA}.fp_adp"
df = spark.table(fq)
print(f"{fq}: {df.count()} total rows")
df.groupBy("season").count().orderBy("season").show()
df.show(5, truncate=False)

# COMMAND ----------

