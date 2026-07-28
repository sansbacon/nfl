# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# dependencies = [
#   "nflreadpy",
# ]
# ///
# DBTITLE 1,Load ETR Data + Player Matching → UC
# MAGIC %md
# MAGIC # Load ETR Data + Player Matching → Unity Catalog
# MAGIC
# MAGIC Loads ETR (Establish the Run) subscription CSV exports from a UC Volume,
# MAGIC matches players to the canonical `nfl.common.dim_ff_player_ids` crosswalk
# MAGIC (sourced from `nflreadpy.load_ff_playerids()`), and persists results to
# MAGIC `nfl.etr`.
# MAGIC
# MAGIC **Architecture:**
# MAGIC - `nfl.common.dim_ff_player_ids` — canonical player identity crosswalk (`mfl_id` = primary key)
# MAGIC - `nfl.etr.dim_etr_players` — ETR player dimension (from ETR's `id` column)
# MAGIC - `nfl.etr.fact_etr_ranks` — SCD2 rankings by (season, player, position, scoring_format)
# MAGIC - `nfl.etr.etr_player_map` — persisted mapping of `etr_id → mfl_id`
# MAGIC
# MAGIC **Matching approach:**
# MAGIC 1. Normalize ETR player names to `merge_name` format (lowercase, strip suffixes/punctuation)
# MAGIC 2. Join to `dim_ff_player_ids` on `merge_name` + `position` (+ `team` as tiebreaker)
# MAGIC 3. Persist matched pairs; only re-match unmapped players on subsequent runs
# MAGIC 4. Log unmatched players for manual review
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - ETR CSV files uploaded to the configured Volume path
# MAGIC - `nfl.common.dim_ff_player_ids` table populated (Cell 5 handles this)
# MAGIC
# MAGIC ## Run Order
# MAGIC 1. Setup & Install
# MAGIC 2. Inputs and Run Controls
# MAGIC 3. Library Functions (→ `nfl.common.matching` / `nfl.etr.loader`)
# MAGIC 4. Load Canonical Crosswalk
# MAGIC 5. Load ETR Ranks
# MAGIC 6. Match ETR → Crosswalk
# MAGIC 7. Verify

# COMMAND ----------

# DBTITLE 1,Install Dependencies
# MAGIC %pip install nflreadpy

# COMMAND ----------

# DBTITLE 1,Setup & Imports
from datetime import date
from pathlib import Path
import re
import unicodedata

import nflreadpy as nflread
import pyspark.sql.functions as F
import pyspark.sql.types as T
from delta.tables import DeltaTable

# COMMAND ----------

# DBTITLE 1,Widgets
dbutils.widgets.text('CATALOG', 'nfl')
dbutils.widgets.text('ETR_SCHEMA', 'etr')
dbutils.widgets.text('COMMON_SCHEMA', 'common')
dbutils.widgets.text('SEASON', '2026')
dbutils.widgets.text('SOURCE_PATH', '/Volumes/nfl/etr/etr_volume/incoming/ranks')
dbutils.widgets.text('ARCHIVE_PATH', '/Volumes/nfl/etr/etr_volume/processed/ranks')

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
CATALOG = dbutils.widgets.get('CATALOG')
ETR_SCHEMA = dbutils.widgets.get('ETR_SCHEMA')
COMMON_SCHEMA = dbutils.widgets.get('COMMON_SCHEMA')
SEASON = int(dbutils.widgets.get('SEASON'))
SOURCE_PATH = dbutils.widgets.get('SOURCE_PATH')
ARCHIVE_PATH = dbutils.widgets.get('ARCHIVE_PATH')

assert all((CATALOG, ETR_SCHEMA, COMMON_SCHEMA, SEASON, SOURCE_PATH, ARCHIVE_PATH)), (
    f'ERROR: {CATALOG=} {ETR_SCHEMA=} {COMMON_SCHEMA=} {SEASON=} {SOURCE_PATH=} {ARCHIVE_PATH=} must be set'
)

print(f"ETR target: {CATALOG}.{ETR_SCHEMA}")
print(f"Crosswalk: {CATALOG}.{COMMON_SCHEMA}.dim_ff_player_ids")
print(f"Season: {SEASON}")
print(f"Source: {SOURCE_PATH}")

# COMMAND ----------

# DBTITLE 1,Library Functions
# MAGIC %md ## Library Functions
# MAGIC
# MAGIC These functions will be extracted into library modules:
# MAGIC - `nfl.common.crosswalk` — canonical crosswalk loading/refresh
# MAGIC - `nfl.common.matching` — name normalization, match-to-crosswalk utilities
# MAGIC - `nfl.etr.loader` — ETR-specific CSV parsing and SCD2 logic

# COMMAND ----------

# DBTITLE 1,nfl.common.matching — Name Normalization
# ---------------------------------------------------------------------------
# nfl.common.matching
# ---------------------------------------------------------------------------

def normalize_name(name: str) -> str:
    """Normalize a player name to match nflreadpy's merge_name format.

    Converts to lowercase, strips accents, removes suffixes (Jr., Sr., III, etc.),
    removes all non-alphanumeric characters except hyphens and spaces, and
    collapses whitespace. Preserves hyphens to match nflreadpy's merge_name format.

    Args:
        name: Raw player name (e.g. "Patrick Mahomes II", "D'Andre Swift")

    Returns:
        Normalized name (e.g. "patrick mahomes", "dandre swift")
    """
    if not name:
        return ""
    # Lowercase
    s = name.lower().strip()
    # Strip accents (NFD decompose, drop combining chars)
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    # Remove common suffixes
    suffix_pattern = r'\b(jr\.?|sr\.?|ii|iii|iv|v)\s*$'
    s = re.sub(suffix_pattern, '', s).strip()
    # Remove all non-alphanumeric except hyphens and spaces
    s = re.sub(r"[^a-z0-9\- ]", '', s)
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s


# Quick validation
assert normalize_name("Patrick Mahomes II") == "patrick mahomes"
assert normalize_name("D'Andre Swift") == "dandre swift"
assert normalize_name("Marvin Harrison Jr.") == "marvin harrison"
assert normalize_name("Amon-Ra St. Brown") == "amon-ra st brown"
print("✓ normalize_name tests passed")

# COMMAND ----------

# DBTITLE 1,nfl.common.crosswalk — Load Canonical Crosswalk
# ---------------------------------------------------------------------------
# nfl.common.crosswalk
# ---------------------------------------------------------------------------

def load_canonical_crosswalk(catalog: str, schema: str) -> None:
    """Load nflreadpy player IDs into the canonical crosswalk table.

    Overwrites `dim_ff_player_ids` on each run since nflreadpy is the
    source of truth and updates as rookies are added.

    Args:
        catalog: Unity Catalog catalog name.
        schema: Schema name (e.g. 'common').
    """
    fqn = f"{catalog}.{schema}.dim_ff_player_ids"
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

    # Load from nflreadpy (returns polars DataFrame)
    player_ids_pl = nflread.load_ff_playerids()
    player_ids_pd = player_ids_pl.to_pandas()

    # Convert to Spark DataFrame
    crosswalk_df = spark.createDataFrame(player_ids_pd)

    # Write with overwrite (nflreadpy is source of truth)
    (
        crosswalk_df
        .write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(fqn)
    )

    row_count = spark.table(fqn).count()
    print(f"  ✓ {fqn}: {row_count} players loaded from nflreadpy")

# COMMAND ----------

# DBTITLE 1,nfl.etr.loader — CSV Parsing
# ---------------------------------------------------------------------------
# nfl.etr.loader
# ---------------------------------------------------------------------------

def parse_scoring_format(file_name: str) -> str:
    """Extract scoring format from an ETR export file name.

    Expects names like 'NFL ETR Rankings \u2013 Full PPR.csv' and returns the
    segment after the dash (en dash, em dash, or hyphen), e.g. 'Full PPR'.

    Args:
        file_name: Base name of the ETR CSV file.

    Returns:
        Scoring format string.

    Raises:
        ValueError: If no dash separator found in file name.
    """
    # Match en dash, em dash, or regular hyphen
    pattern = r'[\u2013\u2014-]\s*(.+?)\s*\.csv$'
    match = re.search(pattern, file_name, re.IGNORECASE)
    if not match:
        raise ValueError(
            f"Cannot parse scoring format from '{file_name}'. "
            f"Expected format: 'NFL ETR Rankings \u2013 <format>.csv'"
        )
    return match.group(1).strip()


def load_etr_csvs(source_path: str, season: int) -> "pyspark.sql.DataFrame":
    """Read all ETR rank CSVs from source_path into a single DataFrame.

    Adds `scoring_format` (parsed from filename), `season`, and
    `ingestion_date` columns. Normalizes column names to snake_case.

    Args:
        source_path: Volume path containing ETR CSV files.
        season: NFL season year.

    Returns:
        Spark DataFrame with all ETR rank records.
    """
    import os

    files = dbutils.fs.ls(source_path)
    csv_files = [f for f in files if f.name.endswith('.csv')]

    if not csv_files:
        print(f"  \u26a0 No CSV files found in {source_path}")
        return spark.createDataFrame([], T.StructType([]))

    all_dfs = []
    for file_info in csv_files:
        scoring_format = parse_scoring_format(file_info.name)
        df = (
            spark.read
            .option("header", "true")
            .option("inferSchema", "true")
            .csv(file_info.path)
            .withColumn("scoring_format", F.lit(scoring_format))
            .withColumn("season", F.lit(season))
            .withColumn("ingestion_date", F.current_date())
            .withColumn("source_file", F.lit(file_info.name))
        )
        all_dfs.append(df)
        print(f"  \u2713 {file_info.name} \u2192 scoring_format='{scoring_format}', {df.count()} rows")

    from functools import reduce
    combined = reduce(lambda a, b: a.unionByName(b, allowMissingColumns=True), all_dfs)

    # Normalize column names: 'ETR Rank' -> 'etr_rank', 'Player' -> 'player'
    for col_name in combined.columns:
        snake_name = re.sub(r'\s+', '_', col_name.strip()).lower()
        if snake_name != col_name:
            combined = combined.withColumnRenamed(col_name, snake_name)

    return combined


# Quick validation
assert parse_scoring_format("NFL ETR Rankings \u2013 Full PPR.csv") == "Full PPR"
assert parse_scoring_format("NFL ETR Rankings - Half PPR.csv") == "Half PPR"
print("\u2713 parse_scoring_format tests passed")

# COMMAND ----------

# DBTITLE 1,nfl.common.matching — Match ETR to Crosswalk
# ---------------------------------------------------------------------------
# nfl.common.matching (ETR-specific orchestration)
# ---------------------------------------------------------------------------

def match_etr_to_crosswalk(
    catalog: str,
    etr_schema: str,
    common_schema: str,
) -> None:
    """Match ETR players to the canonical crosswalk via name + position.

    Only processes ETR players not already in etr_player_map. Uses:
      1. Exact merge_name + position match
      2. Exact merge_name only (position mismatch tiebroken by team)
      3. Logs unmatched players for manual review

    Results are MERGE'd into `etr_player_map` (etr_id \u2192 mfl_id).

    Args:
        catalog: Unity Catalog catalog name.
        etr_schema: ETR schema name.
        common_schema: Common schema containing dim_ff_player_ids.
    """
    etr_prefix = f"{catalog}.{etr_schema}"
    common_prefix = f"{catalog}.{common_schema}"
    map_table = f"{etr_prefix}.etr_player_map"

    # Ensure mapping table exists
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {map_table} (
            etr_id STRING NOT NULL,
            mfl_id BIGINT NOT NULL,
            match_method STRING,
            matched_at TIMESTAMP
        )
        USING DELTA
        COMMENT 'ETR player ID to canonical mfl_id crosswalk'
    """)

    # Get unmapped ETR players
    # (assumes fact_etr_ranks has been loaded with etr_id = the 'id' column from CSV)
    unmapped_etr = spark.sql(f"""
        SELECT DISTINCT
            r.etr_player_id AS etr_id,
            r.player,
            r.position,
            r.team
        FROM {etr_prefix}.fact_etr_ranks r
        WHERE r.is_current = true
          AND r.etr_player_id IS NOT NULL
          AND r.etr_player_id NOT IN (SELECT etr_id FROM {map_table})
    """)

    unmapped_count = unmapped_etr.count()
    if unmapped_count == 0:
        print("  \u23ed etr_player_map: no new players to match")
        return

    print(f"  Attempting to match {unmapped_count} unmapped ETR players...")

    # Register as temp view with normalized name
    (
        unmapped_etr
        .withColumn("etr_merge_name", F.udf(normalize_name, T.StringType())(F.col("player")))
        .createOrReplaceTempView("_tmp_unmapped_etr")
    )

    # --- Step 1: Exact merge_name + position ---
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW _tmp_exact_match AS
        SELECT
            etr.etr_id,
            xw.mfl_id,
            'exact_name_pos' AS match_method
        FROM _tmp_unmapped_etr etr
        INNER JOIN {common_prefix}.dim_ff_player_ids xw
            ON etr.etr_merge_name = xw.merge_name
            AND LOWER(etr.position) = LOWER(xw.position)
    """)

    # --- Step 2: Exact merge_name only (for position mismatches) ---
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW _tmp_name_only_match AS
        SELECT
            etr.etr_id,
            xw.mfl_id,
            'exact_name_team' AS match_method
        FROM _tmp_unmapped_etr etr
        INNER JOIN {common_prefix}.dim_ff_player_ids xw
            ON etr.etr_merge_name = xw.merge_name
            AND LOWER(etr.team) = LOWER(xw.team)
        WHERE etr.etr_id NOT IN (SELECT etr_id FROM _tmp_exact_match)
    """)

    # --- Combine and enforce 1:1 (deduplicate by mfl_id and etr_id) ---
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW _tmp_all_candidates AS
        SELECT *, 1 AS method_priority FROM _tmp_exact_match
        UNION ALL
        SELECT *, 2 AS method_priority FROM _tmp_name_only_match
    """)

    spark.sql("""
        CREATE OR REPLACE TEMP VIEW _tmp_dedup AS
        SELECT etr_id, mfl_id, match_method
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY etr_id ORDER BY method_priority) AS rn_etr,
                ROW_NUMBER() OVER (PARTITION BY mfl_id ORDER BY method_priority) AS rn_mfl
            FROM _tmp_all_candidates
        )
        WHERE rn_etr = 1
    """)

    # Final: only keep bidirectional 1:1 matches
    final_df = spark.sql("""
        SELECT etr_id, mfl_id, match_method, current_timestamp() AS matched_at
        FROM _tmp_dedup
        WHERE mfl_id NOT IN (
            SELECT mfl_id FROM _tmp_dedup GROUP BY mfl_id HAVING COUNT(*) > 1
        )
        AND etr_id NOT IN (
            SELECT etr_id FROM _tmp_dedup GROUP BY etr_id HAVING COUNT(*) > 1
        )
    """)

    # Collect counts BEFORE merge (candidate views filter on map_table)
    match_counts = {
        row["match_method"]: row["n"]
        for row in final_df.groupBy("match_method").count().withColumnRenamed("count", "n").collect()
    }
    matched_total = sum(match_counts.values())

    if matched_total == 0:
        print("  \u26a0 No matches found")
    else:
        final_df.createOrReplaceTempView("_tmp_new_matches")
        spark.sql(f"""
            MERGE INTO {map_table} AS target
            USING _tmp_new_matches AS source
            ON target.etr_id = source.etr_id
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """)
        print(f"  \u2713 etr_player_map: merged {match_counts} ({matched_total} total)")

    # Report unmatched
    still_unmapped = spark.sql(f"""
        SELECT etr_id, player, position, team
        FROM _tmp_unmapped_etr
        WHERE etr_id NOT IN (SELECT etr_id FROM {map_table})
    """)
    unmatched_count = still_unmapped.count()
    if unmatched_count > 0:
        print(f"  \u26a0 {unmatched_count} ETR players unmatched (review below):")
        still_unmapped.show(20, truncate=False)

# COMMAND ----------

# DBTITLE 1,Execution
# MAGIC %md ## Execution
# MAGIC
# MAGIC Below is the actual run sequence. Each cell calls one library function.

# COMMAND ----------

# DBTITLE 1,Load Canonical Crosswalk
# Step 1: Load/refresh the canonical crosswalk from nflreadpy
load_canonical_crosswalk(CATALOG, COMMON_SCHEMA)

# COMMAND ----------

# DBTITLE 1,Load ETR Ranks from Volume
# Step 2: Load ETR CSV files from Volume
etr_ranks_df = load_etr_csvs(SOURCE_PATH, SEASON)

if etr_ranks_df.columns:  # non-empty schema
    print(f"\nTotal ETR rows loaded: {etr_ranks_df.count()}")
    print(f"Columns: {etr_ranks_df.columns}")
    display(etr_ranks_df.limit(5))

# COMMAND ----------

# DBTITLE 1,Persist ETR Ranks (SCD2)
# Step 3: Persist ETR ranks to fact_etr_ranks (SCD2 merge)
# This cell creates dim_etr_players + fact_etr_ranks if they don't exist,
# then merges the new data using the (season, player, position, scoring_format) key.

etr_prefix = f"{CATALOG}.{ETR_SCHEMA}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {etr_prefix}")

# Create fact table if not exists
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {etr_prefix}.fact_etr_ranks (
        etr_player_id STRING,
        player STRING,
        position STRING,
        team STRING,
        etr_rank INT,
        adp DOUBLE,
        ranking_diff DOUBLE,
        etr_pos_rank INT,
        adp_pos_rank INT,
        pos_rank_diff DOUBLE,
        scoring_format STRING,
        season INT,
        ingestion_date DATE,
        end_date DATE,
        is_current BOOLEAN,
        source_file STRING
    )
    USING DELTA
    COMMENT 'ETR rankings SCD2 - natural key: (season, player, position, scoring_format)'
""")

# SCD2 merge: close existing current rows that have changed, insert new
etr_ranks_df.createOrReplaceTempView("_tmp_etr_incoming")

# Close changed rows
spark.sql(f"""
    MERGE INTO {etr_prefix}.fact_etr_ranks AS target
    USING _tmp_etr_incoming AS source
    ON target.season = source.season
        AND target.player = source.player
        AND target.position = source.position
        AND target.scoring_format = source.scoring_format
        AND target.is_current = true
    WHEN MATCHED AND (
        target.etr_rank != source.etr_rank
        OR target.adp != source.adp
        OR target.etr_pos_rank != source.etr_pos_rank
        OR target.team != source.team
    ) THEN UPDATE SET
        target.end_date = current_date(),
        target.is_current = false
    WHEN NOT MATCHED THEN INSERT (
        etr_player_id, player, position, team, etr_rank, adp, ranking_diff,
        etr_pos_rank, adp_pos_rank, pos_rank_diff,
        scoring_format, season, ingestion_date, end_date, is_current, source_file
    ) VALUES (
        source.id, source.player, source.position, source.team,
        source.etr_rank, source.adp, source.ranking_diff,
        source.etr_pos_rank, source.adp_pos_rank, source.pos_rank_diff,
        source.scoring_format, source.season, source.ingestion_date,
        NULL, true, source.source_file
    )
""")

fact_count = spark.table(f"{etr_prefix}.fact_etr_ranks").filter("is_current = true").count()
print(f"  \u2713 {etr_prefix}.fact_etr_ranks: {fact_count} current rows")

# COMMAND ----------

# DBTITLE 1,Match ETR → Canonical Crosswalk
# Step 4: Match ETR players to canonical crosswalk
match_etr_to_crosswalk(CATALOG, ETR_SCHEMA, COMMON_SCHEMA)

# COMMAND ----------

# DBTITLE 1,Archive Processed Files
# Step 5: Archive processed files
import os

files = dbutils.fs.ls(SOURCE_PATH)
csv_files = [f for f in files if f.name.endswith('.csv')]

for file_info in csv_files:
    dest = f"{ARCHIVE_PATH}/{file_info.name}"
    dbutils.fs.mv(file_info.path, dest)
    print(f"  \u2713 Archived: {file_info.name} \u2192 {ARCHIVE_PATH}/")

if not csv_files:
    print("  \u23ed No files to archive")

# COMMAND ----------

# DBTITLE 1,Verification
# MAGIC %md ## Verification

# COMMAND ----------

# DBTITLE 1,Verify Matching Coverage
# Verify: show crosswalk coverage for ETR players
etr_prefix = f"{CATALOG}.{ETR_SCHEMA}"
common_prefix = f"{CATALOG}.{COMMON_SCHEMA}"

print("=== ETR Player Matching Summary ===")
print()

# Total ETR players vs matched
total_etr = spark.sql(f"""
    SELECT COUNT(DISTINCT etr_player_id) FROM {etr_prefix}.fact_etr_ranks WHERE is_current = true AND etr_player_id IS NOT NULL
""").collect()[0][0]

matched = spark.table(f"{etr_prefix}.etr_player_map").count()

print(f"Total current ETR players: {total_etr}")
print(f"Matched to crosswalk:      {matched} ({100*matched/max(total_etr,1):.1f}%)")
print(f"Unmatched:                 {total_etr - matched}")
print()

# Match method breakdown
print("Match method breakdown:")
spark.table(f"{etr_prefix}.etr_player_map").groupBy("match_method").count().show()

# Sample: show an ETR player joined through to Yahoo ID via crosswalk
print("\nSample cross-source join (ETR \u2192 crosswalk \u2192 Yahoo ID):")
spark.sql(f"""
    SELECT
        r.player,
        r.position,
        r.team,
        r.etr_rank,
        m.mfl_id,
        xw.yahoo_id,
        xw.espn_id,
        xw.fantasypros_id
    FROM {etr_prefix}.fact_etr_ranks r
    INNER JOIN {etr_prefix}.etr_player_map m ON r.etr_player_id = m.etr_id
    INNER JOIN {common_prefix}.dim_ff_player_ids xw ON m.mfl_id = xw.mfl_id
    WHERE r.is_current = true
    ORDER BY r.etr_rank
    LIMIT 15
""").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Exit
dbutils.notebook.exit(f'Success - ETR load and match complete for season {SEASON}')