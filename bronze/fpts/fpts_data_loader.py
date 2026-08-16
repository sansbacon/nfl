# Databricks notebook source
# DBTITLE 1,Load Fantasy Points Rankings → Unity Catalog
# MAGIC %md
# MAGIC # Load Fantasy Points Rankings → Unity Catalog
# MAGIC
# MAGIC Loads Fantasy Points subscription CSV exports from a UC Volume,
# MAGIC matches players to the canonical `nfl.common.dim_ff_player_ids` crosswalk,
# MAGIC and persists results to `nfl.fpts`.
# MAGIC
# MAGIC Uses the `nfl.fantasypoints_fantasy` library package for parsing, matching,
# MAGIC and transforms.
# MAGIC
# MAGIC **Architecture:**
# MAGIC - `nfl.common.dim_ff_player_ids` — canonical player identity crosswalk (`mfl_id` = primary key)
# MAGIC - `nfl.fpts.fact_fpts_ranks` — SCD2 rankings by (season, player, position)
# MAGIC - `nfl.fpts.fpts_player_map` — persisted mapping of `merge_name → mfl_id`
# MAGIC
# MAGIC **Run Order:**
# MAGIC 1. Install & Import
# MAGIC 2. Widgets & Inputs
# MAGIC 3. Run Pipeline
# MAGIC 4. Archive Processed Files
# MAGIC 5. Verification

# COMMAND ----------

# DBTITLE 1,Install Dependencies
# MAGIC %pip install -e /Workspace/Users/etruett@alas.com/nfl

# COMMAND ----------

# DBTITLE 1,Setup & Imports
from pathlib import Path

from nfl.fantasypoints_fantasy.pipeline import PipelineConfig, run_pipeline
from nfl.fantasypoints_fantasy.parser import parse_rankings_csv

# COMMAND ----------

# DBTITLE 1,Widgets
dbutils.widgets.text('CATALOG', 'nfl')
dbutils.widgets.text('FPTS_SCHEMA', 'fpts')
dbutils.widgets.text('COMMON_SCHEMA', 'common')
dbutils.widgets.text('SEASON', '2026')
dbutils.widgets.text('SOURCE_PATH', '/Volumes/nfl/fpts/fpts_volume/incoming/ranks')
dbutils.widgets.text('ARCHIVE_PATH', '/Volumes/nfl/fpts/fpts_volume/processed/ranks')

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
CATALOG = dbutils.widgets.get('CATALOG')
FPTS_SCHEMA = dbutils.widgets.get('FPTS_SCHEMA')
COMMON_SCHEMA = dbutils.widgets.get('COMMON_SCHEMA')
SEASON = int(dbutils.widgets.get('SEASON'))
SOURCE_PATH = dbutils.widgets.get('SOURCE_PATH')
ARCHIVE_PATH = dbutils.widgets.get('ARCHIVE_PATH')

assert all((CATALOG, FPTS_SCHEMA, COMMON_SCHEMA, SEASON, SOURCE_PATH, ARCHIVE_PATH)), (
    f'ERROR: {CATALOG=} {FPTS_SCHEMA=} {COMMON_SCHEMA=} {SEASON=} {SOURCE_PATH=} {ARCHIVE_PATH=} must be set'
)

print(f"FPTS target: {CATALOG}.{FPTS_SCHEMA}")
print(f"Crosswalk: {CATALOG}.{COMMON_SCHEMA}.dim_ff_player_ids")
print(f"Season: {SEASON}")
print(f"Source: {SOURCE_PATH}")

# COMMAND ----------

# DBTITLE 1,Discover CSV Files
files = dbutils.fs.ls(SOURCE_PATH)
csv_files = [f for f in files if f.name.endswith('.csv')]

if not csv_files:
    dbutils.notebook.exit(f'No CSV files found in {SOURCE_PATH} — nothing to process')

print(f"Found {len(csv_files)} CSV file(s):")
for f in csv_files:
    print(f"  • {f.name}")

# COMMAND ----------

# DBTITLE 1,Run Pipeline
# Parse all CSVs in the incoming directory
all_records: list[dict] = []
for file_info in csv_files:
    local_path = file_info.path.replace("dbfs:", "/dbfs")
    records = parse_rankings_csv(local_path)
    print(f"  ✓ {file_info.name}: {len(records)} players")
    all_records.extend(records)

print(f"\nTotal records: {len(all_records)}")

# Run the pipeline (dry_run=False for real persistence)
result = run_pipeline(
    PipelineConfig(
        season=SEASON,
        rankings_csv_path="",  # bypassed — we pass csv_records directly
        backend="duckdb",
        dry_run=False,
        pyspark_catalog=CATALOG,
        pyspark_schema=FPTS_SCHEMA,
    ),
    csv_records=all_records,
)

print(f"\n=== Pipeline Result ===")
print(f"Rankings: {result.rankings_count} rows")
print(f"Player map: {result.player_map_count} entries")
print(f"Matching: {result.matching_summary}")

# COMMAND ----------

# DBTITLE 1,Persist to Unity Catalog (Delta)
import pyspark.sql.functions as F

fpts_prefix = f"{CATALOG}.{FPTS_SCHEMA}"

# --- fact_fpts_ranks ---
ranks_pdf = result.tables.fact_fpts_ranks.execute()
ranks_sdf = spark.createDataFrame(ranks_pdf)

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {fpts_prefix}.fact_fpts_ranks (
        season INT,
        player STRING,
        position STRING,
        team STRING,
        bye INT,
        overall_rank INT,
        auction_value INT,
        exodia BOOLEAN,
        scoring_format STRING,
        ingestion_date DATE,
        end_date DATE,
        is_current BOOLEAN
    )
    USING DELTA
    COMMENT 'Fantasy Points rankings SCD2 - natural key: (season, player, position)'
""")

# SCD2 merge: close changed rows, insert new
ranks_sdf.createOrReplaceTempView("_tmp_fpts_incoming")

spark.sql(f"""
    MERGE INTO {fpts_prefix}.fact_fpts_ranks AS target
    USING _tmp_fpts_incoming AS source
    ON target.season = source.season
        AND target.player = source.player
        AND target.position = source.position
        AND target.is_current = true
    WHEN MATCHED AND (
        target.overall_rank != source.overall_rank
        OR target.auction_value != source.auction_value
        OR target.team != source.team
        OR target.exodia != source.exodia
    ) THEN UPDATE SET
        target.end_date = current_date(),
        target.is_current = false
    WHEN NOT MATCHED THEN INSERT *
""")

fact_count = spark.table(f"{fpts_prefix}.fact_fpts_ranks").filter("is_current = true").count()
print(f"  ✓ {fpts_prefix}.fact_fpts_ranks: {fact_count} current rows")

# --- fpts_player_map ---
map_pdf = result.tables.fpts_player_map.execute()
map_sdf = spark.createDataFrame(map_pdf)

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {fpts_prefix}.fpts_player_map (
        player STRING,
        position STRING,
        team STRING,
        merge_name STRING,
        mfl_id STRING,
        match_method STRING
    )
    USING DELTA
    COMMENT 'Fantasy Points player to canonical mfl_id crosswalk'
""")

map_sdf.createOrReplaceTempView("_tmp_fpts_map")

spark.sql(f"""
    MERGE INTO {fpts_prefix}.fpts_player_map AS target
    USING _tmp_fpts_map AS source
    ON target.merge_name = source.merge_name
        AND target.position = source.position
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")

map_count = spark.table(f"{fpts_prefix}.fpts_player_map").count()
print(f"  ✓ {fpts_prefix}.fpts_player_map: {map_count} entries")

# COMMAND ----------

# DBTITLE 1,Archive Processed Files
for file_info in csv_files:
    dest = f"{ARCHIVE_PATH}/{file_info.name}"
    dbutils.fs.mv(file_info.path, dest)
    print(f"  ✓ Archived: {file_info.name} → {ARCHIVE_PATH}/")

# COMMAND ----------

# DBTITLE 1,Verification
fpts_prefix = f"{CATALOG}.{FPTS_SCHEMA}"
common_prefix = f"{CATALOG}.{COMMON_SCHEMA}"

print("=== Fantasy Points Player Matching Summary ===")
print()

total_fpts = spark.table(f"{fpts_prefix}.fpts_player_map").count()
matched = spark.table(f"{fpts_prefix}.fpts_player_map").filter("mfl_id IS NOT NULL").count()

print(f"Total FPTS players: {total_fpts}")
print(f"Matched to crosswalk: {matched} ({100*matched/max(total_fpts,1):.1f}%)")
print(f"Unmatched: {total_fpts - matched}")
print()

# Match method breakdown
print("Match method breakdown:")
spark.table(f"{fpts_prefix}.fpts_player_map").groupBy("match_method").count().show()

# Sample: top-ranked players joined to crosswalk
print("\nSample cross-source join (FPTS → crosswalk):")
spark.sql(f"""
    SELECT
        r.player,
        r.position,
        r.team,
        r.overall_rank,
        r.auction_value,
        m.mfl_id,
        xw.yahoo_id,
        xw.espn_id
    FROM {fpts_prefix}.fact_fpts_ranks r
    INNER JOIN {fpts_prefix}.fpts_player_map m
        ON r.player = m.player AND r.position = m.position
    INNER JOIN {common_prefix}.dim_ff_player_ids xw ON CAST(m.mfl_id AS BIGINT) = xw.mfl_id
    WHERE r.is_current = true
    ORDER BY r.overall_rank
    LIMIT 15
""").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Exit
dbutils.notebook.exit(f'Success - Fantasy Points load complete for season {SEASON}')