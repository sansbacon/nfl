# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# dependencies = [
#   "polars",
#   "requests_oauthlib",
# ]
# ///
# DBTITLE 1,Yahoo Pipeline → Unity Catalog
# MAGIC %md
# MAGIC # Yahoo Pipeline → Unity Catalog
# MAGIC
# MAGIC Runs the Yahoo Fantasy pipeline and persists all frames as **Delta tables** in Unity Catalog (`nfl.yh`).
# MAGIC
# MAGIC This notebook is designed for **Databricks serverless** — no local Iceberg catalog or warehouse directory needed.
# MAGIC
# MAGIC ## Run Order
# MAGIC 1. Setup & Imports
# MAGIC 2. Inputs and Run Controls
# MAGIC 3. Auth (Databricks Secrets)
# MAGIC 4. Full Pipeline Run with UC Persist

# COMMAND ----------

# DBTITLE 1,Install Dependencies
# MAGIC %pip install polars requests-oauthlib

# COMMAND ----------

# DBTITLE 1,Setup & Imports
import json
import os
from pathlib import Path
import sys

import polars as pl

# Ensure src is importable (workspace path resolution)
notebook_dir = Path.cwd()
candidates = [
    notebook_dir.parent,                          # /Workspace/Users/.../nfl
    Path("/Workspace/Users/etruett@alas.com/nfl"),
]
project_root = next((p for p in candidates if (p / "pyproject.toml").exists()), notebook_dir)
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print(f"project_root={project_root}")
print(f"src_path={src_path}")

from nfl.yahoo_fantasy.pipeline import (
    PipelineConfig,
    PipelineDiagnosticsConfig,
    run_pipeline,
)
from nfl.yahoo_fantasy.storage.unity_catalog import YahooUCTableConfig, YahooUCVolumeConfig
from nfl.yahoo_fantasy.auth import build_oauth_session, load_token
from nfl.yahoo_fantasy.transforms import transform

# COMMAND ----------

pl.Config.set_tbl_rows(25)
pl.Config.set_fmt_str_lengths(100)

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
# --- Required Inputs ---
LEAGUE_KEY = "449.l.327657"
SPORT = "nfl"

# --- Run Controls ---
TARGET_SEASON = 2024
START_WEEK = 1
END_WEEK = 17
USE_CACHE = False
INCLUDE_UNROSTERED_PLAYER_STATS = True

# --- Unity Catalog Target ---
CATALOG = "nfl"
SCHEMA = "yh"
WRITE_MODE = "overwrite"  # overwrite | append | merge
UC_DRY_RUN = False

assert all((CATALOG, SCHEMA)), f'ERROR: {CATALOG=} and {SCHEMA=} must be set'

print(f"League: {LEAGUE_KEY} | Sport: {SPORT}")
print(f"Season: {TARGET_SEASON}, Weeks: {START_WEEK}-{END_WEEK}")
print(f"UC Target: {CATALOG}.{SCHEMA} (mode={WRITE_MODE}, dry_run={UC_DRY_RUN})")

# COMMAND ----------

# DBTITLE 1,Auth (Databricks Secrets)
# Load credentials from project .secrets directory
credentials_path = project_root / ".secrets" / "credentials.json"
token_path = project_root / ".secrets" / "yahoo_token.json"

assert credentials_path.exists(), f"ERROR: {credentials_path} not found"
assert token_path.exists(), f"ERROR: {token_path} not found"

with open(credentials_path) as f:
    creds = json.load(f)

client_id = creds["client_id"]
client_secret = creds["client_secret"]
redirect_uri = creds["redirect_uri"]

oauth_session = build_oauth_session(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    token_path=token_path,
    auth_code=None,
    open_browser=False,
)

cached_token = load_token(token_path)
print("OAuth session ready")
print(f"  token_type={cached_token.get('token_type', 'unknown')}")

# COMMAND ----------

# DBTITLE 1,Run Pipeline → UC Tables
# Reload to pick up UC fields added to PipelineConfig
import importlib
import nfl.yahoo_fantasy.pipeline as _yp
importlib.reload(_yp)
from nfl.yahoo_fantasy.pipeline import PipelineConfig, PipelineDiagnosticsConfig, run_pipeline

# Full pipeline run with Unity Catalog persistence
uc_table_config = YahooUCTableConfig(
    catalog=CATALOG,
    nfl_schema=SCHEMA,
    nba_schema=f"{SCHEMA}_nba",
    common_schema=SCHEMA,
    write_mode=WRITE_MODE,
)

full_cfg = PipelineConfig(
    storage_target="unity_catalog",
    use_cache=USE_CACHE,
    validate_contracts=True,
    require_nfl_player_points=False,
    include_nfl_unrostered_player_stats=INCLUDE_UNROSTERED_PLAYER_STATS,
    start_week=START_WEEK,
    end_week=END_WEEK,
    uc_table_config=uc_table_config,
    uc_dry_run=UC_DRY_RUN,
    diagnostics=PipelineDiagnosticsConfig(
        enabled=True,
        emit_stage_progress=True,
        capture_frame_summaries=True,
        capture_request_stats=True,
    ),
)

result = run_pipeline(
    league_key=LEAGUE_KEY,
    sport=SPORT,
    oauth_session=oauth_session,
    config=full_cfg,
)

print("Pipeline completed")
print(f"  Frames: {sorted(result.frames.keys())}")
if result.diagnostics:
    print(result.diagnostics.summary)
    for stage in result.diagnostics.stages:
        print(f"  - {stage.stage_name}: {stage.status}, {stage.duration_ms} ms")

# COMMAND ----------

# DBTITLE 1,Verify UC Tables
# Persist to UC (run_pipeline does not yet have a UC persist stage)
from nfl.yahoo_fantasy.storage.unity_catalog import persist_yahoo_to_uc_tables

uc_results = persist_yahoo_to_uc_tables(
    frames=result.frames,
    config=uc_table_config,
    dry_run=UC_DRY_RUN,
)

print("\nUC Write Results:")
for wr in uc_results:
    print(f"  {wr.target}: {wr.written_rows} rows ({wr.mode})")

# Quick validation read-back on the largest frame
# Table name has sport prefix stripped by persist function
print(f"\n--- Validation: {CATALOG}.{SCHEMA}.player_stats_weekly ---")
df = spark.table(f"{CATALOG}.{SCHEMA}.player_stats_weekly")
print(f"  Row count: {df.count()}")
df.show(5, truncate=False)