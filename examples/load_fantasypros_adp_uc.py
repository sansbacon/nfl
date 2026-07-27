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

project_root = Path.cwd().parent if (Path.cwd().parent / "pyproject.toml").exists() else Path.cwd()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from nfl.fantasypros_fantasy import FantasyProsApiClient, PipelineConfig, run_pipeline
from nfl.fantasypros_fantasy.storage.unity_catalog import FantasyProsUCTableConfig

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
SEASONS = list(range(2021, 2026))

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
# HTML scraper only returns 5 rows due to FantasyPros registrationFence.
# Use the partners CSV export API which returns full data.
import io
import requests as _req
from nfl.fantasypros_fantasy.storage.unity_catalog import FantasyProsUCTableConfig, persist_fp_to_uc_tables

_FP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

def fetch_fp_adp_csv(season: int) -> pl.DataFrame:
    """Fetch full ADP data from FantasyPros partners CSV export."""
    url = (
        f"https://partners.fantasypros.com/api/v1/consensus-rankings.php"
        f"?sport=NFL&year={season}&week=0&id=0&position=ALL&type=ADP&scoring=PPR&export=xls"
    )
    resp = _req.get(url, headers=_FP_HEADERS, timeout=30)
    resp.raise_for_status()
    # CSV has 4 header/metadata lines, then real CSV starts at line 5
    lines = resp.text.splitlines()
    csv_text = "\n".join(lines[4:])
    df = pl.read_csv(io.StringIO(csv_text), truncate_ragged_lines=True)
    # Normalize columns and add season
    df = df.rename({c: c.strip().lower().replace(" ", "_") for c in df.columns})
    df = df.with_columns(pl.lit(season).alias("season"))
    return df

all_frames: dict[str, list[pl.DataFrame]] = {"fp_adp": []}

for season in SEASONS:
    df = fetch_fp_adp_csv(season)
    all_frames["fp_adp"].append(df)
    print(f"  Season {season}: {df.height} rows")

# Combine all seasons into one frame
combined = pl.concat(all_frames["fp_adp"])
print(f"\nTotal combined: {combined.height} rows x {combined.width} cols")
print(f"Columns: {combined.columns}")

# Persist to UC
uc_results = persist_fp_to_uc_tables(
    frames={"fp_adp": combined},
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

