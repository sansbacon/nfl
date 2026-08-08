# Databricks notebook source
# DBTITLE 1,Query Tables (Unity Catalog)
# MAGIC %md
# MAGIC # Query Yahoo & FantasyPros Tables (Unity Catalog)
# MAGIC
# MAGIC Demonstrates querying NFL fantasy data from Unity Catalog Delta tables using both Spark SQL and Polars.
# MAGIC
# MAGIC Tables are stored under:
# MAGIC - `nfl.yh.*` — Yahoo Fantasy league data
# MAGIC - `nfl.fp.*` — FantasyPros ADP and player data

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

from nfl.yahoo_fantasy.queries import (
    average_scoring_by_position_by_team,
    enrich_weekly_team_points,
    league_average_by_position,
    league_team_info,
    player_points_health,
    standings_summary as query_standings_summary,
    unified_draft_price_analysis,
    weekly_team_points_resolved,
)
from nfl.yahoo_fantasy.presentation import format_table_for_display
from nfl.common.storage import load_uc_table as _load_uc_table

pl.Config.set_tbl_rows(50)
pl.Config.set_fmt_str_lengths(100)

# COMMAND ----------

# DBTITLE 1,Configuration & Helpers
CATALOG = "nfl"
YH_SCHEMA = "yh"
FP_SCHEMA = "fp"

assert all((CATALOG, YH_SCHEMA)), f'ERROR: {CATALOG=} and {YH_SCHEMA=} must be set'

def load_uc_table(schema: str, table: str) -> pl.DataFrame:
    """Load a UC table as a Polars DataFrame."""
    return _load_uc_table(f"{CATALOG}.{schema}.{table}")

def show_table(df: pl.DataFrame, drop_keys: bool = True):
    """Display a table with display formatting."""
    display(format_table_for_display(df, drop_keys=drop_keys))

print(f"UC Source: {CATALOG}.{YH_SCHEMA}.* / {CATALOG}.{FP_SCHEMA}.*")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Available Tables

# COMMAND ----------

# DBTITLE 1,List Available Tables
# List all tables in Yahoo and FP schemas
for schema in [YH_SCHEMA, FP_SCHEMA]:
    tables = [row.tableName for row in spark.sql(f"SHOW TABLES IN {CATALOG}.{schema}").collect()]
    print(f"\n{CATALOG}.{schema}:")
    for t in sorted(tables):
        count = spark.table(f"{CATALOG}.{schema}.{t}").count()
        print(f"  {t}: {count} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## League & Team Information

# COMMAND ----------

# DBTITLE 1,League & Team Info
league_df = load_uc_table(YH_SCHEMA, "league")
team_df = load_uc_table(YH_SCHEMA, "team")

league_team = league_team_info(league_df=league_df, team_df=team_df)
print("League and Team Information:")
show_table(league_team)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Standings Summary

# COMMAND ----------

# DBTITLE 1,Standings
standings_df = load_uc_table(YH_SCHEMA, "standings")

standings = query_standings_summary(standings_df=standings_df, team_df=team_df)
print("Standings:")
show_table(standings)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Weekly Scoring Analysis

# COMMAND ----------

# DBTITLE 1,Weekly Scoring
player_stats_df = load_uc_table(YH_SCHEMA, "player_stats_weekly")
player_df = load_uc_table(YH_SCHEMA, "player")
roster_df = load_uc_table(YH_SCHEMA, "roster_entries")
matchup_df = load_uc_table(YH_SCHEMA, "matchups")

# Player points health check
health = player_points_health(player_stats_df)
print("Player Points Health:")
show_table(health)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Position Scoring Averages

# COMMAND ----------

# DBTITLE 1,Position Averages
# Average scoring by position across the league
pos_avg = league_average_by_position(
    player_stats_df=player_stats_df,
    player_df=player_df,
    roster_entries_df=roster_df,
)
print("League Average by Position:")
show_table(pos_avg)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Draft Price Analysis (Yahoo + FantasyPros ADP)

# COMMAND ----------

# DBTITLE 1,Draft Price Analysis
# Combine Yahoo draft data with FantasyPros ADP for value analysis
draft_df = load_uc_table(YH_SCHEMA, "draft_pick")

try:
    fp_adp_df = load_uc_table(FP_SCHEMA, "nfl_fp_current_adp")
    fp_crosswalk_df = load_uc_table(FP_SCHEMA, "nfl_fp_yahoo_player_map")

    draft_analysis = unified_draft_price_analysis(
        draft_df=draft_df,
        player_df=player_df,
        fp_adp_df=fp_adp_df,
        fp_crosswalk_df=fp_crosswalk_df,
    )
    print("Draft Price Analysis (Yahoo + FP ADP):")
    show_table(draft_analysis)
except Exception as e:
    print(f"Draft analysis skipped (FP tables may not be loaded yet): {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Direct SQL Queries
# MAGIC
# MAGIC You can also query UC tables directly with SQL:

# COMMAND ----------

# DBTITLE 1,Top Scorers (SQL)
# MAGIC %sql
# MAGIC -- Top 20 scorers by total fantasy points
# MAGIC SELECT
# MAGIC     p.full_name,
# MAGIC     p.display_position,
# MAGIC     p.editorial_team_abbr AS team,
# MAGIC     SUM(ps.fantasy_points) AS total_points,
# MAGIC     COUNT(ps.week) AS weeks_played,
# MAGIC     ROUND(AVG(ps.fantasy_points), 2) AS avg_ppg
# MAGIC FROM nfl.yh.player_stats_weekly ps
# MAGIC JOIN nfl.yh.player p ON ps.player_key = p.player_key
# MAGIC WHERE ps.fantasy_points > 0
# MAGIC GROUP BY p.full_name, p.display_position, p.editorial_team_abbr
# MAGIC ORDER BY total_points DESC
# MAGIC LIMIT 20