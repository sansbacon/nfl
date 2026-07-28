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
# Combine CSV files (for actual ADP) with API data (for min/max/std_dev)
import io
import re
import requests as _req
from nfl.fantasypros_fantasy.storage.unity_catalog import FantasyProsUCTableConfig, persist_fp_to_uc_tables

_FP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

VOLUME_PATH = "/Volumes/nfl/default/nfl_volume"

# --- Source 1: CSVs (actual ADP + per-platform values) ---
def load_fp_adp_csv(season: int) -> pl.DataFrame:
    """Load FantasyPros ADP CSV from volume. Parses player/team/position from raw columns."""
    path = f"{VOLUME_PATH}/FantasyPros_{season}_Overall_ADP_Rankings.csv"
    df = pl.read_csv(path, truncate_ragged_lines=True, null_values=["—"])
    # Parse "Player (Bye)" → player_name, team
    # Format: "Christian McCaffrey   SF (9)" or just "Tyreek Hill"
    player_col = "Player (Bye)" if "Player (Bye)" in df.columns else "Player"
    df = df.with_columns(
        pl.col(player_col)
          .str.replace(r"\s*\(\d+\)\s*$", "")  # strip bye week
          .str.strip_chars()
          .alias("_cleaned")
    )
    df = df.with_columns(
        # Team is last whitespace-separated token IF it's 2-3 uppercase chars
        pl.col("_cleaned").str.extract(r"\s+([A-Z]{2,3})$").alias("team"),
        # Player name is everything before the team abbrev
        pl.col("_cleaned").str.replace(r"\s+[A-Z]{2,3}$", "").str.strip_chars().alias("player_name"),
    )
    # Parse "POS" → position (strip positional rank number, e.g. "RB1" → "RB")
    df = df.with_columns(
        pl.col("POS").str.extract(r"^([A-Z]+)").alias("position")
    )
    # Cast platform columns to Float64 for consistency across years
    platform_cols = [c for c in df.columns if c in ("ESPN", "Sleeper", "CBS", "NFL", "RTSports", "Fantrax")]
    df = df.with_columns([pl.col(c).cast(pl.Float64, strict=False) for c in platform_cols])
    df = df.rename({"Rank": "rank", "AVG": "adp", **{c: c.lower() for c in platform_cols}})
    df = df.with_columns(pl.lit(season).alias("season"))
    lowered_cols = [c.lower() for c in platform_cols]
    keep = ["rank", "player_name", "team", "position", "adp"] + lowered_cols + ["season"]
    return df.select([c for c in keep if c in df.columns])


# --- Source 2: API (min/max/std_dev) ---
def fetch_fp_adp_api(season: int) -> pl.DataFrame | None:
    """Fetch ADP spread data from FantasyPros partners API. Returns None on failure."""
    url = (
        f"https://partners.fantasypros.com/api/v1/consensus-rankings.php"
        f"?sport=NFL&year={season}&week=0&id=0&position=ALL&type=ADP&scoring=PPR&export=xls"
    )
    try:
        resp = _req.get(url, headers=_FP_HEADERS, timeout=30)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        csv_text = "\n".join(lines[4:])
        df = pl.read_csv(io.StringIO(csv_text), truncate_ragged_lines=True)
        df = df.rename({c: c.strip().lower().replace(" ", "_") for c in df.columns})
        # Keep only rank + spread columns
        spread_cols = [c for c in df.columns if c in ("rank", "min", "max", "std_dev")]
        df = df.select(spread_cols)
        df = df.with_columns(pl.lit(season).alias("season"))
        return df
    except Exception as e:
        print(f"  ⚠ API unavailable for {season}: {e}")
        return None


# --- Combine both sources ---
all_frames: list[pl.DataFrame] = []

for season in SEASONS:
    csv_df = load_fp_adp_csv(season)
    api_df = fetch_fp_adp_api(season)

    if api_df is not None:
        # Join on rank + season to attach min/max/std_dev
        combined = csv_df.join(api_df, on=["rank", "season"], how="left")
    else:
        # CSV only — no spread data
        combined = csv_df.with_columns(
            pl.lit(None).cast(pl.Int64).alias("min"),
            pl.lit(None).cast(pl.Int64).alias("max"),
            pl.lit(None).cast(pl.Float64).alias("std_dev"),
        )

    all_frames.append(combined)
    print(f"  Season {season}: {combined.height} rows (API spread: {'✓' if api_df is not None else '✗'})")

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

