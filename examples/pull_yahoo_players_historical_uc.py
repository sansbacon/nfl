# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# dependencies = [
#   "polars",
#   "requests_oauthlib",
# ]
# ///
# DBTITLE 1,Pull Yahoo Players Historical → UC
# MAGIC %md
# MAGIC # Pull Yahoo Players Historical → Unity Catalog
# MAGIC
# MAGIC Fetches the full Yahoo Fantasy player pool for seasons 2021–2023 using the
# MAGIC `/game/{game_id}/players` endpoint (not league-scoped) and persists to `nfl.yh.player`.

# COMMAND ----------

# MAGIC %pip install polars requests_oauthlib

# COMMAND ----------

# DBTITLE 1,Setup & Imports
import json
import os
import sys
from pathlib import Path

import polars as pl

# Resolve project root and ensure src is importable
notebook_dir = Path.cwd()
candidates = [notebook_dir.parent, Path("/Workspace/Users/etruett@alas.com/nfl")]
project_root = next((p for p in candidates if (p / "pyproject.toml").exists()), notebook_dir)
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from nfl.yahoo_fantasy.auth import build_oauth_session, load_token
from nfl.yahoo_fantasy.api import YahooApiClient
from nfl.storage_uc import UCTableConfig, persist_to_uc_tables

print(f"project_root={project_root}")

# COMMAND ----------

# DBTITLE 1,Inputs
START_SEASON = 2024
END_SEASON = 2025
SPORT = "nfl"

# API tuning
PLAYER_PAGE_SIZE = 25
REQUEST_INTERVAL = 0.4
MAX_RETRIES = 5
BACKOFF_BASE = 1.2
USE_CACHE = True

# UC target
CATALOG = "nfl"
SCHEMA = "yh"
WRITE_MODE = "merge"  # upsert on player_key to avoid duplicates on re-runs
MERGE_KEYS = ("player_key",)
DRY_RUN = False

assert all((CATALOG, SCHEMA)), f'ERROR: {CATALOG=} and {SCHEMA=} must be set'

# COMMAND ----------

# DBTITLE 1,Auth (from .secrets)
credentials_path = project_root / ".secrets" / "credentials.json"
token_path = project_root / ".secrets" / "yahoo_token.json"

assert credentials_path.exists(), f"ERROR: {credentials_path} not found"
assert token_path.exists(), f"ERROR: {token_path} not found"

with open(credentials_path) as f:
    creds = json.load(f)

oauth = build_oauth_session(
    client_id=creds["client_id"],
    client_secret=creds["client_secret"],
    redirect_uri=creds["redirect_uri"],
    token_path=token_path,
    auth_code=None,
    open_browser=False,
)

cached_token = load_token(token_path)
print(f"OAuth session ready (token_type={cached_token.get('token_type', 'unknown')})")

# COMMAND ----------

# DBTITLE 1,Fetch Players for Season Range
client = YahooApiClient(
    oauth_session=oauth,
    cache_dir=project_root / ".cache",
    use_cache=USE_CACHE,
    validate_contracts=True,
    request_interval_seconds=REQUEST_INTERVAL,
    max_request_retries=MAX_RETRIES,
    backoff_base_seconds=BACKOFF_BASE,
    player_page_size=PLAYER_PAGE_SIZE,
)

print(f"Fetching {SPORT} players for seasons {START_SEASON}–{END_SEASON}...")
rows = client.get_players_for_season_range(
    start_season=START_SEASON,
    end_season=END_SEASON,
    sport=SPORT,
)
print(f"Fetched {len(rows)} players across {START_SEASON}–{END_SEASON}")

df = pl.from_dicts(rows)
columns = df.columns  # compute schema once (avoids SCPAP001 lint)
game_ids = df["game_id"].unique().sort().to_list() if "game_id" in columns else []
print(f"game_ids in result: {game_ids}")
print(f"Shape: {df.shape}")
print(df.head(5))

# COMMAND ----------

# DBTITLE 1,Persist to Unity Catalog
uc_config = UCTableConfig(
    catalog=CATALOG,
    schema=SCHEMA,
    write_mode=WRITE_MODE,
    merge_keys=MERGE_KEYS,
)

results = persist_to_uc_tables(
    frames={"player": df},
    config=uc_config,
    dry_run=DRY_RUN,
)

for r in results:
    status = "DRY RUN" if DRY_RUN else "WRITTEN"
    print(f"  [{status}] {r.target}: {r.written_rows} rows ({r.mode})")

# COMMAND ----------

# DBTITLE 1,Verify
fq = f"{CATALOG}.{SCHEMA}.player"
df_verify = spark.table(fq)
total = df_verify.count()
print(f"{fq}: {total} total rows")
df_verify.groupBy("game_id").count().orderBy("game_id").show()
df_verify.show(5, truncate=False)

# COMMAND ----------

# DBTITLE 1,Deduplicate for Matching
from pyspark.sql import Window
from pyspark.sql import functions as F

# One row per player_id — keep the most recent season (highest game_id)
w = Window.partitionBy("player_id").orderBy(F.col("game_id").desc())

df_deduped = (
    spark.table(f"{CATALOG}.{SCHEMA}.player")
    .withColumn("_rn", F.row_number().over(w))
    .filter("_rn = 1")
    .drop("_rn")
)

print(f"Deduplicated: {df_deduped.count()} unique players (from {df_verify.count()} total rows)")
df_deduped.show(5, truncate=False)

# Write as a separate table for matching joins
df_deduped.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{CATALOG}.{SCHEMA}.player_deduped")
print(f"Written to {CATALOG}.{SCHEMA}.player_deduped")