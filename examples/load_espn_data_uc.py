# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Load ESPN Projections + Rankings → UC
# MAGIC %md
# MAGIC # Load ESPN Projections + Rankings → Unity Catalog
# MAGIC
# MAGIC Fetches season-long and weekly projections plus draft rankings from ESPN's
# MAGIC public fantasy football API (no auth, no league required), matches players
# MAGIC via direct `espn_id` join to the canonical crosswalk, and persists results
# MAGIC to `nfl.espn`.
# MAGIC
# MAGIC **Architecture:**
# MAGIC - `nfl.common.dim_ff_player_ids` — canonical player identity crosswalk (`mfl_id` = primary key)
# MAGIC - `nfl.espn.fact_espn_ranks` — SCD2 draft rankings (PPR + Standard rank, auction values)
# MAGIC - `nfl.espn.fact_espn_projections` — SCD2 full-season stat projections
# MAGIC - `nfl.espn.fact_espn_weekly_projections` — SCD2 per-week stat projections
# MAGIC - `nfl.espn.espn_player_map` — `espn_id → mfl_id` (direct crosswalk join, no fuzzy matching)
# MAGIC
# MAGIC **Matching approach:**
# MAGIC 1. Direct `espn_id` join to `dim_ff_player_ids.espn_id` (65% coverage)
# MAGIC 2. Fallback: normalized name + position match for players missing from crosswalk
# MAGIC 3. No manual aliases expected (ESPN uses canonical NFL names)
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - `nfl.common.dim_ff_player_ids` must exist (run crosswalk load first)
# MAGIC - Internet access for ESPN API calls

# COMMAND ----------

# DBTITLE 1,Install Dependencies
# MAGIC %pip install nflreadpy
# MAGIC
# MAGIC import sys
# MAGIC sys.path.insert(0, '/Workspace/Users/etruett@alas.com/nfl/src')

# COMMAND ----------

# DBTITLE 1,Setup & Imports
from datetime import date

import pyspark.sql.functions as F
from delta.tables import DeltaTable

from nfl.common.crosswalk import load_canonical_crosswalk
from nfl.common.matching import normalize_name
from nfl.espn_fantasy.api import EspnFantasyClient, EspnPlayer
from nfl.espn_fantasy.constants import STAT_MAP
from nfl.espn_fantasy.transforms import (
    players_to_ranks_rows,
    players_to_season_projection_rows,
    players_to_weekly_projection_rows,
)
from nfl.espn_fantasy.matching import match_espn_to_crosswalk


def fetch_espn_players(season: int) -> list[EspnPlayer]:
    """Convenience wrapper around EspnFantasyClient."""
    client = EspnFantasyClient()
    return client.fetch_all_players(season)

# COMMAND ----------

# DBTITLE 1,Widgets
dbutils.widgets.text('CATALOG', 'nfl')
dbutils.widgets.text('ESPN_SCHEMA', 'espn')
dbutils.widgets.text('COMMON_SCHEMA', 'common')
dbutils.widgets.text('SEASON', '2025')

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
CATALOG = dbutils.widgets.get('CATALOG')
ESPN_SCHEMA = dbutils.widgets.get('ESPN_SCHEMA')
COMMON_SCHEMA = dbutils.widgets.get('COMMON_SCHEMA')
SEASON = int(dbutils.widgets.get('SEASON'))

assert all((CATALOG, ESPN_SCHEMA, COMMON_SCHEMA, SEASON)), (
    f'ERROR: {CATALOG=} {ESPN_SCHEMA=} {COMMON_SCHEMA=} {SEASON=} must be set'
)

print(f"ESPN target: {CATALOG}.{ESPN_SCHEMA}")
print(f"Crosswalk: {CATALOG}.{COMMON_SCHEMA}.dim_ff_player_ids")
print(f"Season: {SEASON}")

# COMMAND ----------

# DBTITLE 1,Execution
# MAGIC %md ## Execution
# MAGIC
# MAGIC Below is the actual run sequence. Each cell calls one library function.

# COMMAND ----------

# DBTITLE 1,Load Canonical Crosswalk
# Step 1: Load/refresh the canonical crosswalk from nflreadpy
load_canonical_crosswalk(spark, CATALOG, COMMON_SCHEMA)

# COMMAND ----------

# DBTITLE 1,Fetch ESPN Projections + Rankings
# Step 2: Fetch all ESPN players with projections from the public API
espn_players = fetch_espn_players(SEASON)

print(f"\nPlayers with rankings: {sum(1 for p in espn_players if p.rank_ppr)}")
print(f"Players with season projections: {sum(1 for p in espn_players if p.season_projection)}")
print(f"Players with weekly projections: {sum(1 for p in espn_players if p.weekly_projections)}")

# COMMAND ----------

# DBTITLE 1,Persist ESPN Ranks (SCD2)
# Step 3: Persist rankings to fact_espn_ranks (SCD2)
espn_prefix = f"{CATALOG}.{ESPN_SCHEMA}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {espn_prefix}")

ranks_rows = players_to_ranks_rows(espn_players, SEASON)
ranks_schema = "espn_id INT, player STRING, position STRING, team STRING, rank_ppr INT, rank_standard INT, auction_value_ppr INT, auction_value_standard INT, percent_owned DOUBLE, percent_started DOUBLE, season INT, ingestion_date DATE, end_date DATE, is_current BOOLEAN"
ranks_df = spark.createDataFrame(ranks_rows, schema=ranks_schema)

# Create table if not exists
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {espn_prefix}.fact_espn_ranks (
        espn_id INT,
        player STRING,
        position STRING,
        team STRING,
        rank_ppr INT,
        rank_standard INT,
        auction_value_ppr INT,
        auction_value_standard INT,
        percent_owned DOUBLE,
        percent_started DOUBLE,
        season INT,
        ingestion_date DATE,
        end_date DATE,
        is_current BOOLEAN
    ) USING DELTA
    COMMENT 'ESPN draft rankings SCD2 - natural key: (season, espn_id)'
""")

# SCD2 Merge: expire changed rows
ranks_df.createOrReplaceTempView("_espn_ranks_incoming")

spark.sql(f"""
    MERGE INTO {espn_prefix}.fact_espn_ranks AS target
    USING _espn_ranks_incoming AS source
    ON target.espn_id = source.espn_id
       AND target.season = source.season
       AND target.is_current = true
    WHEN MATCHED AND (
        target.rank_ppr != source.rank_ppr OR
        target.rank_standard != source.rank_standard OR
        target.auction_value_ppr != source.auction_value_ppr
    ) THEN UPDATE SET
        end_date = source.ingestion_date,
        is_current = false
    WHEN NOT MATCHED THEN INSERT *
""")

# Insert new current rows for expired keys
spark.sql(f"""
    INSERT INTO {espn_prefix}.fact_espn_ranks
    SELECT source.*
    FROM _espn_ranks_incoming source
    JOIN {espn_prefix}.fact_espn_ranks target
      ON target.espn_id = source.espn_id
      AND target.season = source.season
      AND target.end_date = source.ingestion_date
      AND target.is_current = false
    WHERE NOT EXISTS (
        SELECT 1 FROM {espn_prefix}.fact_espn_ranks existing
        WHERE existing.espn_id = source.espn_id
          AND existing.season = source.season
          AND existing.ingestion_date = source.ingestion_date
          AND existing.is_current = true
    )
""")

spark.catalog.dropTempView("_espn_ranks_incoming")
current_ranks = spark.sql(f"SELECT COUNT(*) FROM {espn_prefix}.fact_espn_ranks WHERE is_current = true").collect()[0][0]
print(f"  \u2713 {espn_prefix}.fact_espn_ranks: {current_ranks} current rows")

# COMMAND ----------

# DBTITLE 1,Persist Season Projections (SCD2)
# Step 4: Persist season-long projections
season_rows = players_to_season_projection_rows(espn_players, SEASON)
stat_cols = ", ".join(f"{col} DOUBLE" for col in STAT_MAP.values())
season_schema = f"espn_id INT, player STRING, position STRING, team STRING, season INT, projected_total DOUBLE, ingestion_date DATE, end_date DATE, is_current BOOLEAN, {stat_cols}"
season_df = spark.createDataFrame(season_rows, schema=season_schema)

# Create table dynamically from the DataFrame schema
season_df.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{espn_prefix}.fact_espn_projections")

count = spark.table(f"{espn_prefix}.fact_espn_projections").count()
print(f"  \u2713 {espn_prefix}.fact_espn_projections: {count} rows")

# COMMAND ----------

# DBTITLE 1,Persist Weekly Projections (SCD2)
# Step 5: Persist weekly projections
weekly_rows = players_to_weekly_projection_rows(espn_players, SEASON)
stat_cols = ", ".join(f"{col} DOUBLE" for col in STAT_MAP.values())
weekly_schema = f"espn_id INT, player STRING, position STRING, team STRING, season INT, week INT, projected_total DOUBLE, ingestion_date DATE, end_date DATE, is_current BOOLEAN, {stat_cols}"
weekly_df = spark.createDataFrame(weekly_rows, schema=weekly_schema)

weekly_df.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{espn_prefix}.fact_espn_weekly_projections")

count = spark.table(f"{espn_prefix}.fact_espn_weekly_projections").count()
weeks = spark.sql(f"SELECT DISTINCT week FROM {espn_prefix}.fact_espn_weekly_projections ORDER BY week").collect()
week_list = [r[0] for r in weeks]
print(f"  \u2713 {espn_prefix}.fact_espn_weekly_projections: {count} rows across weeks {week_list[0]}-{week_list[-1]}")

# COMMAND ----------

# DBTITLE 1,Match ESPN → Canonical Crosswalk
# Step 6: Match ESPN players to canonical crosswalk
match_espn_to_crosswalk(spark, CATALOG, ESPN_SCHEMA, COMMON_SCHEMA)

# COMMAND ----------

# DBTITLE 1,Verification
# MAGIC %md ## Verification

# COMMAND ----------

# DBTITLE 1,Verify Matching Coverage
# Verify: show crosswalk coverage for ESPN players
espn_prefix = f"{CATALOG}.{ESPN_SCHEMA}"
common_prefix = f"{CATALOG}.{COMMON_SCHEMA}"

print("=== ESPN Player Matching Summary ===")
print()

# Total ESPN players vs matched
total_espn = spark.sql(f"""
    SELECT COUNT(DISTINCT espn_id) FROM {espn_prefix}.fact_espn_ranks WHERE is_current = true
""").collect()[0][0]

matched = spark.table(f"{espn_prefix}.espn_player_map").count()

print(f"Total current ESPN players: {total_espn}")
print(f"Matched to crosswalk:       {matched} ({100*matched/max(total_espn,1):.1f}%)")
print(f"Unmatched:                  {total_espn - matched}")
print()

# Match method breakdown
print("Match method breakdown:")
spark.sql(f"""
    SELECT match_method, COUNT(*) as count
    FROM {espn_prefix}.espn_player_map
    GROUP BY match_method
    ORDER BY count DESC
""").show()

# Sample cross-source join
print("\nSample cross-source join (ESPN → crosswalk → Yahoo ID):")
spark.sql(f"""
    SELECT
        r.player, r.position, r.team, r.rank_ppr,
        m.mfl_id, c.yahoo_id, c.fantasypros_id
    FROM {espn_prefix}.fact_espn_ranks r
    JOIN {espn_prefix}.espn_player_map m ON r.espn_id = m.espn_id
    JOIN {common_prefix}.dim_ff_player_ids c ON m.mfl_id = c.mfl_id
    WHERE r.is_current = true
    ORDER BY r.rank_ppr
    LIMIT 10
""").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Exit
dbutils.notebook.exit(f'Success - ESPN load and match complete for season {SEASON}')