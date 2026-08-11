# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# dependencies = [
#   "polars",
# ]
# ///
# DBTITLE 1,Load Sleeper ADP → UC
# MAGIC %md
# MAGIC # Load Sleeper ADP → Unity Catalog
# MAGIC
# MAGIC Fetches ADP data from Sleeper's public fantasy football API (no auth
# MAGIC required), matches players via direct `sleeper_id` join to the canonical
# MAGIC crosswalk, and persists results to `nfl.sl`.
# MAGIC
# MAGIC **Architecture:**
# MAGIC - `nfl.common.dim_ff_player_ids` — canonical player identity crosswalk (`mfl_id` = primary key)
# MAGIC - `nfl.sl.dim_sl_players` — Sleeper player dimension (SCD1 upsert)
# MAGIC - `nfl.sl.fact_sl_adp` — SCD2 ADP across 5 scoring formats (half-PPR, PPR, standard, 2QB, dynasty)
# MAGIC - `nfl.sl.vw_current_sl_adp` — convenience view filtering to current SCD2 rows
# MAGIC
# MAGIC **Matching approach:**
# MAGIC - Direct `sleeper_id` join to `dim_ff_player_ids.sleeper_id` (no fuzzy matching needed)
# MAGIC - DEF entries use team abbreviations as IDs and are excluded from the crosswalk check
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - `nfl.common.dim_ff_player_ids` must exist (run crosswalk load first)
# MAGIC - Internet access for Sleeper API calls

# COMMAND ----------

# MAGIC %pip install polars

# COMMAND ----------

# DBTITLE 1,Install Dependencies
import sys
sys.path.insert(0, '/Workspace/Users/etruett@alas.com/nfl/src')

# COMMAND ----------

# DBTITLE 1,Setup & Imports
from datetime import date

import pyspark.sql.functions as F

from nfl.sleeper_fantasy.api import SleeperClient
from nfl.sleeper_fantasy.transforms import players_to_adp_rows, players_to_dim_rows

# COMMAND ----------

# DBTITLE 1,Widgets
dbutils.widgets.text('CATALOG', 'nfl')
dbutils.widgets.text('SL_SCHEMA', 'sl')
dbutils.widgets.text('COMMON_SCHEMA', 'common')
dbutils.widgets.text('SEASON', '2026')

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
CATALOG = dbutils.widgets.get('CATALOG')
SL_SCHEMA = dbutils.widgets.get('SL_SCHEMA')
COMMON_SCHEMA = dbutils.widgets.get('COMMON_SCHEMA')
SEASON = int(dbutils.widgets.get('SEASON'))

assert all((CATALOG, SL_SCHEMA, COMMON_SCHEMA, SEASON)), (
    f'ERROR: {CATALOG=} {SL_SCHEMA=} {COMMON_SCHEMA=} {SEASON=} must be set'
)

print(f"Sleeper target: {CATALOG}.{SL_SCHEMA}")
print(f"Crosswalk: {CATALOG}.{COMMON_SCHEMA}.dim_ff_player_ids")
print(f"Season: {SEASON}")

# COMMAND ----------

# DBTITLE 1,Execution
# MAGIC %md ## Execution
# MAGIC
# MAGIC Below is the actual run sequence. Each cell calls one library function or
# MAGIC performs a single persistence step.

# COMMAND ----------

# DBTITLE 1,Fetch Sleeper Players + ADP
# Step 1: Fetch all players with ADP from the Sleeper public API
client = SleeperClient()
sl_players = client.fetch_players_with_adp(SEASON)

print(f"Players with ADP data: {len(sl_players):,}")
print(f"Top 5 by half-PPR ADP:")
for p in sl_players[:5]:
    print(f"  {p.adp_half_ppr:5.1f}  {p.full_name} ({p.position}, {p.team})")

# COMMAND ----------

# DBTITLE 1,Create Schema & Tables
# Step 2: Ensure schema and tables exist
sl_prefix = f"{CATALOG}.{SL_SCHEMA}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {sl_prefix}")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {sl_prefix}.dim_sl_players (
        sleeper_player_id STRING NOT NULL COMMENT 'Sleeper player identifier',
        full_name STRING,
        first_name STRING,
        last_name STRING,
        position STRING COMMENT 'Primary position (QB, RB, WR, TE, K, DEF)',
        team STRING COMMENT 'NFL team abbreviation',
        age INT COMMENT 'Player age',
        years_exp INT COMMENT 'Years of NFL experience',
        college STRING COMMENT 'College attended',
        status STRING COMMENT 'Player status (Active, Inactive, etc.)',
        CONSTRAINT pk_dim_sl_players PRIMARY KEY (sleeper_player_id)
    )
    COMMENT 'Sleeper player dimension table (SCD1 upsert from /players/nfl API)'
""")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {sl_prefix}.fact_sl_adp (
        season INT NOT NULL COMMENT 'NFL season year',
        sleeper_player_id STRING NOT NULL COMMENT 'Sleeper player identifier',
        adp_half_ppr DOUBLE COMMENT 'ADP in half-PPR scoring',
        adp_ppr DOUBLE COMMENT 'ADP in full-PPR scoring',
        adp_std DOUBLE COMMENT 'ADP in standard (non-PPR) scoring',
        adp_2qb DOUBLE COMMENT 'ADP in superflex/2QB scoring',
        adp_dynasty DOUBLE COMMENT 'ADP in dynasty scoring',
        ingestion_date DATE NOT NULL COMMENT 'SCD2: date this record became current',
        end_date DATE COMMENT 'SCD2: date this record was superseded (NULL if current)',
        is_current BOOLEAN NOT NULL COMMENT 'SCD2: true if this is the active record',
        last_refreshed_date DATE COMMENT 'Date this record was last verified by a load run',
        CONSTRAINT pk_fact_sl_adp PRIMARY KEY (season, sleeper_player_id, ingestion_date)
    )
    COMMENT 'Sleeper ADP fact table (SCD2 historized from projections API)'
""")

print(f"  \u2713 {sl_prefix} schema and tables ready")

# COMMAND ----------

# DBTITLE 1,Upsert dim_sl_players (SCD1)
# Step 3: Upsert player dimension
dim_rows = players_to_dim_rows(sl_players)
dim_df = spark.createDataFrame(dim_rows)
dim_df.createOrReplaceTempView("_sl_dim_incoming")

spark.sql(f"""
    MERGE INTO {sl_prefix}.dim_sl_players AS target
    USING _sl_dim_incoming AS source
    ON target.sleeper_player_id = source.sleeper_player_id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")

spark.catalog.dropTempView("_sl_dim_incoming")
dim_count = spark.table(f"{sl_prefix}.dim_sl_players").count()
print(f"  \u2713 {sl_prefix}.dim_sl_players: {dim_count:,} players")

# COMMAND ----------

# DBTITLE 1,Persist fact_sl_adp (SCD2)
# Step 4: SCD2 merge ADP data
adp_rows = players_to_adp_rows(sl_players, SEASON)
target_schema = spark.table(f"{sl_prefix}.fact_sl_adp").schema
# Exclude last_refreshed_date — not produced by players_to_adp_rows; added below
from pyspark.sql.types import StructType
create_schema = StructType([f for f in target_schema if f.name != 'last_refreshed_date'])
adp_df = spark.createDataFrame(adp_rows, schema=create_schema)
adp_df = adp_df.withColumn("last_refreshed_date", F.col("ingestion_date"))
adp_df.createOrReplaceTempView("_sl_adp_incoming")

tracked_cols = ["adp_half_ppr", "adp_ppr", "adp_std", "adp_2qb", "adp_dynasty"]
change_clause = " OR ".join(
    [f"COALESCE(target.{c}, -1) != COALESCE(source.{c}, -1)" for c in tracked_cols]
)

# Step 4a: expire changed rows, refresh unchanged rows, insert new keys
spark.sql(f"""
    MERGE INTO {sl_prefix}.fact_sl_adp AS target
    USING _sl_adp_incoming AS source
    ON target.season = source.season
        AND target.sleeper_player_id = source.sleeper_player_id
        AND target.is_current = true
    WHEN MATCHED AND ({change_clause}) THEN UPDATE SET
        target.end_date = source.ingestion_date,
        target.is_current = false
    WHEN MATCHED THEN UPDATE SET
        target.last_refreshed_date = source.last_refreshed_date
    WHEN NOT MATCHED THEN INSERT *
""")

# Step 4b: insert new current rows for expired keys
spark.sql(f"""
    INSERT INTO {sl_prefix}.fact_sl_adp
    SELECT source.*
    FROM _sl_adp_incoming source
    INNER JOIN {sl_prefix}.fact_sl_adp target
        ON target.season = source.season
        AND target.sleeper_player_id = source.sleeper_player_id
        AND target.end_date = source.ingestion_date
        AND target.is_current = false
    WHERE NOT EXISTS (
        SELECT 1 FROM {sl_prefix}.fact_sl_adp existing
        WHERE existing.season = source.season
            AND existing.sleeper_player_id = source.sleeper_player_id
            AND existing.ingestion_date = source.ingestion_date
            AND existing.is_current = true
    )
""")

spark.catalog.dropTempView("_sl_adp_incoming")
current_count = spark.sql(
    f"SELECT COUNT(*) FROM {sl_prefix}.fact_sl_adp WHERE is_current = true"
).collect()[0][0]
print(f"  \u2713 {sl_prefix}.fact_sl_adp: {current_count:,} current rows")

# COMMAND ----------

# DBTITLE 1,Create View
# Step 5: Create/refresh the current ADP view
spark.sql(f"""
    CREATE OR REPLACE VIEW {sl_prefix}.vw_current_sl_adp
    COMMENT 'Current Sleeper ADP snapshot \u2014 filters out SCD2 history rows'
    AS
    SELECT a.season, a.sleeper_player_id, p.full_name, p.position, p.team,
           a.adp_half_ppr, a.adp_ppr, a.adp_std, a.adp_2qb, a.adp_dynasty,
           a.ingestion_date, a.last_refreshed_date
    FROM {sl_prefix}.fact_sl_adp a
    INNER JOIN {sl_prefix}.dim_sl_players p
        ON a.sleeper_player_id = p.sleeper_player_id
    WHERE a.is_current = true
""")
print(f"  \u2713 {sl_prefix}.vw_current_sl_adp (created)")

# COMMAND ----------

# DBTITLE 1,Crosswalk Gap Check
# Step 6: Alert if any top-150 ADP players are missing from the crosswalk
crosswalk_table = f"{CATALOG}.{COMMON_SCHEMA}.dim_ff_player_ids"

gaps_df = spark.sql(f"""
    SELECT
        a.sleeper_player_id,
        p.full_name,
        p.position,
        p.team,
        a.adp_half_ppr
    FROM {sl_prefix}.fact_sl_adp a
    INNER JOIN {sl_prefix}.dim_sl_players p
        ON a.sleeper_player_id = p.sleeper_player_id
    LEFT JOIN {crosswalk_table} xw
        ON TRY_CAST(a.sleeper_player_id AS DOUBLE) = xw.sleeper_id
    WHERE a.is_current = true
        AND a.adp_half_ppr < 150
        AND p.position != 'DEF'
        AND xw.sleeper_id IS NULL
    ORDER BY a.adp_half_ppr
""")

gap_count = gaps_df.count()
if gap_count == 0:
    print("  \u2713 Crosswalk: all top-150 ADP players (excl. DEF) matched in dim_ff_player_ids")
else:
    print(f"  \u26a0 Crosswalk: {gap_count} player(s) with ADP < 150 NOT in dim_ff_player_ids:")
    gaps_df.show(gap_count, truncate=False)