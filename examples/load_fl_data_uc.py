# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# dependencies = [
#   "beautifulsoup4",
#   "lxml",
# ]
# ///
# DBTITLE 1,Load Fantasy Life Rankings → UC
# MAGIC %md
# MAGIC # Load Fantasy Life Rankings + Player Matching → Unity Catalog
# MAGIC
# MAGIC Loads Fantasy Life (FL) subscription ranking CSV exports and HTML pages
# MAGIC (for player ID extraction) from a UC Volume, matches players to the
# MAGIC canonical `nfl.common.dim_ff_player_ids` crosswalk, and persists results to
# MAGIC `nfl.fl`.
# MAGIC
# MAGIC **Architecture:**
# MAGIC - `nfl.common.dim_ff_player_ids` — canonical player identity crosswalk (`mfl_id` = primary key)
# MAGIC - `nfl.fl.fact_fl_ranks` — FL consensus rankings with expert columns
# MAGIC - `nfl.fl.fl_player_map` — persisted mapping of `fl_id → mfl_id`
# MAGIC
# MAGIC **Data sources (subscription — no API, user-uploaded files):**
# MAGIC - CSV export: `fantasy_life_fantasy_football_rankings.csv` — rankings with Tier, Player, Position, Team, expert ranks, Consensus, ADP, Utilization Score. **No player IDs.**
# MAGIC - HTML pages: `fl1.html` through `fl5.html` — paginated HTML table with player IDs embedded in `<a href="/nfl/players/{fl_id}/..." data-player="{fl_uuid}">` elements
# MAGIC
# MAGIC **Matching approach:**
# MAGIC 1. Parse HTML files to build `fl_id/fl_uuid → player name/position/team` lookup
# MAGIC 2. Join CSV to HTML by player name (exact match — same source, same names)
# MAGIC 3. Normalize FL names to nflreadpy `merge_name` format (keep hyphens, strip apostrophes/periods/suffixes)
# MAGIC 4. Match to `dim_ff_player_ids` on `merge_name` + `position`
# MAGIC 5. Apply known alias table for nickname mismatches (e.g. "Hollywood Brown" = "marquise brown")
# MAGIC 6. Log unmatched players for manual review
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - FL files uploaded to the configured Volume path
# MAGIC - `nfl.common.dim_ff_player_ids` table populated (see `load_etr_data_uc`)
# MAGIC
# MAGIC ## Run Order
# MAGIC 1. Setup & Install
# MAGIC 2. Inputs and Run Controls
# MAGIC 3. Library Functions (→ `nfl.fl.loader` / `nfl.common.matching`)
# MAGIC 4. Load FL Data (HTML + CSV)
# MAGIC 5. Match FL → Crosswalk
# MAGIC 6. Persist to UC
# MAGIC 7. Verify

# COMMAND ----------

# DBTITLE 1,Install Dependencies
# MAGIC %pip install beautifulsoup4 lxml

# COMMAND ----------

# DBTITLE 1,Setup & Imports
from datetime import date
from pathlib import Path
import re
import unicodedata
from functools import reduce

from bs4 import BeautifulSoup
import pyspark.sql.functions as F
import pyspark.sql.types as T
from delta.tables import DeltaTable

# COMMAND ----------

# DBTITLE 1,Widgets
dbutils.widgets.text('CATALOG', 'nfl')
dbutils.widgets.text('FL_SCHEMA', 'fl')
dbutils.widgets.text('COMMON_SCHEMA', 'common')
dbutils.widgets.text('SEASON', '2026')
dbutils.widgets.text('SOURCE_PATH', '/Volumes/nfl/fl/fl_volume/incoming/ranks')
dbutils.widgets.text('ARCHIVE_PATH', '/Volumes/nfl/fl/fl_volume/processed/ranks')

# COMMAND ----------

# DBTITLE 1,Inputs and Run Controls
CATALOG = dbutils.widgets.get('CATALOG')
FL_SCHEMA = dbutils.widgets.get('FL_SCHEMA')
COMMON_SCHEMA = dbutils.widgets.get('COMMON_SCHEMA')
SEASON = int(dbutils.widgets.get('SEASON'))
SOURCE_PATH = dbutils.widgets.get('SOURCE_PATH')
ARCHIVE_PATH = dbutils.widgets.get('ARCHIVE_PATH')

assert all((CATALOG, FL_SCHEMA, COMMON_SCHEMA, SEASON, SOURCE_PATH, ARCHIVE_PATH)), (
    f'ERROR: {CATALOG=} {FL_SCHEMA=} {COMMON_SCHEMA=} {SEASON=} {SOURCE_PATH=} {ARCHIVE_PATH=} must be set'
)

print(f"FL target: {CATALOG}.{FL_SCHEMA}")
print(f"Crosswalk: {CATALOG}.{COMMON_SCHEMA}.dim_ff_player_ids")
print(f"Season: {SEASON}")
print(f"Source: {SOURCE_PATH}")

# COMMAND ----------

# DBTITLE 1,Library Functions
# MAGIC %md ## Library Functions
# MAGIC
# MAGIC These functions will be extracted into library modules:
# MAGIC - `nfl.common.matching` — name normalization (hyphen-preserving to match nflreadpy `merge_name`)
# MAGIC - `nfl.fl.loader` — FL-specific HTML parsing and CSV loading
# MAGIC - `nfl.fl.aliases` — known nickname → canonical name mappings

# COMMAND ----------

# DBTITLE 1,nfl.common.matching — Name Normalization
# ---------------------------------------------------------------------------
# nfl.common.matching
# ---------------------------------------------------------------------------

def normalize_name(name: str) -> str:
    """Normalize a player name to match nflreadpy's merge_name format.

    The nflreadpy crosswalk preserves hyphens but strips apostrophes, periods,
    and suffixes (Jr., Sr., II, III, etc.). This function replicates that format.

    Args:
        name: Raw player name (e.g. "Amon-Ra St. Brown", "D'Andre Swift")

    Returns:
        Normalized name (e.g. "amon-ra st brown", "dandre swift")
    """
    if not name:
        return ""
    s = name.lower().strip()
    # Strip accents
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


# Validation against known crosswalk values
assert normalize_name("Amon-Ra St. Brown") == "amon-ra st brown"
assert normalize_name("Jaxon Smith-Njigba") == "jaxon smith-njigba"
assert normalize_name("D'Andre Swift") == "dandre swift"
assert normalize_name("Marvin Harrison Jr.") == "marvin harrison"
assert normalize_name("Nick Westbrook-Ikhine") == "nick westbrook-ikhine"
assert normalize_name("KeAndre Lambert-Smith") == "keandre lambert-smith"
print("✓ normalize_name tests passed")

# COMMAND ----------

# DBTITLE 1,nfl.fl.aliases — Known Aliases
# ---------------------------------------------------------------------------
# nfl.fl.aliases — Known nickname/abbreviation mappings
# ---------------------------------------------------------------------------

# Maps Fantasy Life display names to the nflreadpy merge_name when they differ.
# Only needed for players whose FL name doesn't normalize to the crosswalk entry.
FL_KNOWN_ALIASES = {
    "hollywood brown": "marquise brown",
    "chig okonkwo": "chigoziem okonkwo",
    "scotty miller": "scott miller",
    "gabe davis": "gabriel davis",
    "mike williams": "michael williams",
}


def apply_aliases(merge_name: str) -> str:
    """Apply known alias mapping. Returns canonical merge_name."""
    return FL_KNOWN_ALIASES.get(merge_name, merge_name)

# COMMAND ----------

# DBTITLE 1,nfl.fl.loader — HTML Parsing
# ---------------------------------------------------------------------------
# nfl.fl.loader — HTML Parsing
# ---------------------------------------------------------------------------

def parse_fl_html_files(source_path: str) -> list[dict]:
    """Parse Fantasy Life HTML ranking pages to extract player IDs.

    FL exports CSV rankings without player IDs. The HTML pages contain
    `<a href="/nfl/players/{fl_id}/{slug}" data-player="{fl_uuid}">` elements
    with the full player entity (name, position, team, IDs).

    Args:
        source_path: Volume path containing fl*.html files.

    Returns:
        List of dicts with keys: fl_id, fl_uuid, slug, full_name, position, team
    """
    files = dbutils.fs.ls(source_path)
    html_files = sorted([f for f in files if f.name.endswith('.html')])

    if not html_files:
        print(f"  \u26a0 No HTML files found in {source_path}")
        return []

    all_players = []
    for file_info in html_files:
        # On Serverless, /Volumes/ is directly accessible; /dbfs/ is not mounted
        local_path = file_info.path.replace('dbfs:', '')
        with open(local_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        player_links = soup.find_all('a', class_='player')
        for link in player_links:
            href = link.get('href', '')
            fl_uuid = link.get('data-player', '')

            id_match = re.search(r'/nfl/players/(\d+)/([^"]+)', href)
            fl_id = id_match.group(1) if id_match else None
            slug = id_match.group(2) if id_match else None

            name_div = link.find('div', class_='name')
            if name_div:
                first = name_div.find('span')
                last = name_div.find('strong')
                full_name = f"{first.get_text(strip=True) if first else ''} {last.get_text(strip=True) if last else ''}".strip()
            else:
                full_name = ''

            team_div = link.find('div', class_='team')
            position, team = '', ''
            if team_div:
                pos_span = team_div.find('span', class_='position')
                team_span = team_div.find('span', class_='teamname')
                position = pos_span.get_text(strip=True).upper() if pos_span else ''
                team = team_span.get_text(strip=True) if team_span else ''

            all_players.append({
                'fl_id': fl_id,
                'fl_uuid': fl_uuid,
                'slug': slug,
                'full_name': full_name,
                'position': position,
                'team': team,
            })

    # Deduplicate by fl_id (HTML pages are paginated, players may repeat)
    seen = set()
    unique = []
    for p in all_players:
        if p['fl_id'] and p['fl_id'] not in seen:
            seen.add(p['fl_id'])
            unique.append(p)

    print(f"  \u2713 Parsed {len(html_files)} HTML files: {len(unique)} unique players")
    return unique

# COMMAND ----------

# DBTITLE 1,nfl.fl.loader — CSV Loading
# ---------------------------------------------------------------------------
# nfl.fl.loader — CSV Loading
# ---------------------------------------------------------------------------

def load_fl_csv(
    source_path: str,
    season: int,
    fl_players: list[dict],
) -> "pyspark.sql.DataFrame":
    """Load Fantasy Life rankings CSV and join player IDs from HTML parse.

    Joins the CSV (which has no IDs) to the HTML-extracted player list by
    exact player name match. Normalizes column names to snake_case.

    Args:
        source_path: Volume path containing the FL CSV file.
        season: NFL season year.
        fl_players: Player list from parse_fl_html_files().

    Returns:
        Spark DataFrame with rankings + fl_id + fl_uuid columns.
    """
    files = dbutils.fs.ls(source_path)
    csv_files = [f for f in files if f.name.endswith('.csv')]

    if not csv_files:
        print(f"  \u26a0 No CSV files found in {source_path}")
        return spark.createDataFrame([], T.StructType([]))

    # Load CSV
    csv_file = csv_files[0]  # Expect one CSV per run
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(csv_file.path)
        .withColumn("season", F.lit(season))
        .withColumn("ingestion_date", F.current_date())
        .withColumn("source_file", F.lit(csv_file.name))
    )

    # Normalize column names
    for col_name in df.columns:
        snake_name = re.sub(r'\s+', '_', col_name.strip()).lower()
        snake_name = re.sub(r'[^a-z0-9_]', '', snake_name)
        if snake_name != col_name:
            df = df.withColumnRenamed(col_name, snake_name)

    # Drop the empty unnamed column (artifact of CSV export)
    unnamed_cols = [c for c in df.columns if c.startswith('unnamed')]
    if unnamed_cols:
        df = df.drop(*unnamed_cols)

    # Build player ID lookup from HTML parse
    fl_lookup = spark.createDataFrame(
        [(p['full_name'], p['fl_id'], p['fl_uuid']) for p in fl_players],
        ['_fl_name', 'fl_id', 'fl_uuid']
    )

    # Join on player name
    df = (
        df
        .join(fl_lookup, df['player'] == fl_lookup['_fl_name'], 'left')
        .drop('_fl_name')
    )

    row_count = df.count()
    id_count = df.filter(F.col('fl_id').isNotNull()).count()
    print(f"  \u2713 {csv_file.name}: {row_count} rows, {id_count} with FL IDs")

    return df

# COMMAND ----------

# DBTITLE 1,nfl.fl.matching — Match to Crosswalk
# ---------------------------------------------------------------------------
# nfl.fl.matching — Match FL to Canonical Crosswalk
# ---------------------------------------------------------------------------

def match_fl_to_crosswalk(
    catalog: str,
    fl_schema: str,
    common_schema: str,
    fl_players: list[dict],
) -> None:
    """Match Fantasy Life players to the canonical crosswalk via name + position.

    Processes all FL players from HTML parse, matches to dim_ff_player_ids,
    and persists fl_player_map (fl_id → mfl_id).

    Args:
        catalog: Unity Catalog catalog name.
        fl_schema: FL schema name.
        common_schema: Common schema containing dim_ff_player_ids.
        fl_players: Player list from parse_fl_html_files().
    """
    fl_prefix = f"{catalog}.{fl_schema}"
    common_prefix = f"{catalog}.{common_schema}"
    map_table = f"{fl_prefix}.fl_player_map"

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fl_prefix}")

    # Create mapping table
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {map_table} (
            fl_id STRING NOT NULL,
            fl_uuid STRING,
            mfl_id BIGINT NOT NULL,
            match_method STRING,
            matched_at TIMESTAMP
        )
        USING DELTA
        COMMENT 'Fantasy Life player ID to canonical mfl_id crosswalk'
    """)

    # Get already-mapped IDs
    existing_ids = set(
        row['fl_id']
        for row in spark.table(map_table).select('fl_id').collect()
    )

    # Filter to unmapped players
    unmapped = [p for p in fl_players if p['fl_id'] not in existing_ids]
    if not unmapped:
        print("  \u23ed fl_player_map: no new players to match")
        return

    print(f"  Attempting to match {len(unmapped)} unmapped FL players...")

    # Add normalized merge_name with alias resolution
    for p in unmapped:
        raw_merge = normalize_name(p['full_name'])
        p['merge_name'] = apply_aliases(raw_merge)

    # Create temp view
    unmapped_df = spark.createDataFrame(
        [(p['fl_id'], p['fl_uuid'], p['full_name'], p['position'], p['team'], p['merge_name'])
         for p in unmapped],
        ['fl_id', 'fl_uuid', 'full_name', 'position', 'team', 'fl_merge_name']
    )
    unmapped_df.createOrReplaceTempView('_tmp_unmapped_fl')

    # Step 1: Exact merge_name + position
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW _tmp_fl_exact AS
        SELECT
            fl.fl_id,
            fl.fl_uuid,
            xw.mfl_id,
            'exact_name_pos' AS match_method
        FROM _tmp_unmapped_fl fl
        INNER JOIN {common_prefix}.dim_ff_player_ids xw
            ON fl.fl_merge_name = xw.merge_name
            AND UPPER(fl.position) = UPPER(xw.position)
    """)

    # Step 2: Exact merge_name + team (for position mismatches)
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW _tmp_fl_name_team AS
        SELECT
            fl.fl_id,
            fl.fl_uuid,
            xw.mfl_id,
            'exact_name_team' AS match_method
        FROM _tmp_unmapped_fl fl
        INNER JOIN {common_prefix}.dim_ff_player_ids xw
            ON fl.fl_merge_name = xw.merge_name
            AND UPPER(fl.team) = UPPER(xw.team)
        WHERE fl.fl_id NOT IN (SELECT fl_id FROM _tmp_fl_exact)
    """)

    # Combine and enforce 1:1
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW _tmp_fl_candidates AS
        SELECT *, 1 AS priority FROM _tmp_fl_exact
        UNION ALL
        SELECT *, 2 AS priority FROM _tmp_fl_name_team
    """)

    final_df = spark.sql("""
        SELECT fl_id, fl_uuid, mfl_id, match_method, current_timestamp() AS matched_at
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY fl_id ORDER BY priority) AS rn_fl,
                ROW_NUMBER() OVER (PARTITION BY mfl_id ORDER BY priority) AS rn_mfl
            FROM _tmp_fl_candidates
        )
        WHERE rn_fl = 1 AND rn_mfl = 1
    """)

    # Collect counts before merge
    match_counts = {
        row['match_method']: row['n']
        for row in final_df.groupBy('match_method').count().withColumnRenamed('count', 'n').collect()
    }
    matched_total = sum(match_counts.values())

    if matched_total == 0:
        print("  \u26a0 No matches found")
    else:
        final_df.createOrReplaceTempView('_tmp_fl_new_matches')
        spark.sql(f"""
            MERGE INTO {map_table} AS target
            USING _tmp_fl_new_matches AS source
            ON target.fl_id = source.fl_id
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """)
        print(f"  \u2713 fl_player_map: merged {match_counts} ({matched_total} total)")

    # Report unmatched
    mapped_ids = set(
        row['fl_id'] for row in spark.table(map_table).select('fl_id').collect()
    )
    still_unmapped = [p for p in unmapped if p['fl_id'] not in mapped_ids]
    if still_unmapped:
        print(f"  \u26a0 {len(still_unmapped)} FL players unmatched:")
        for p in still_unmapped[:25]:
            print(f"    {p['fl_id']:>7} | {p['full_name']:<25} | {p['position']:<3} | {p['team']}")

# COMMAND ----------

# DBTITLE 1,Execution
# MAGIC %md ## Execution

# COMMAND ----------

# DBTITLE 1,Parse HTML for Player IDs
# Step 1: Parse HTML files for player IDs
fl_players = parse_fl_html_files(SOURCE_PATH)

# COMMAND ----------

# DBTITLE 1,Load CSV Rankings
# Step 2: Load CSV and join player IDs
fl_ranks_df = load_fl_csv(SOURCE_PATH, SEASON, fl_players)

if fl_ranks_df.columns:
    print(f"\nColumns: {fl_ranks_df.columns}")
    fl_ranks_df.show(5, truncate=False)

# COMMAND ----------

# DBTITLE 1,Persist FL Ranks
# Step 3: Persist rankings to fact_fl_ranks
fl_prefix = f"{CATALOG}.{FL_SCHEMA}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fl_prefix}")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {fl_prefix}.fact_fl_ranks (
        fl_id STRING,
        fl_uuid STRING,
        player STRING,
        position STRING,
        team STRING,
        bye INT,
        tier INT,
        consensus INT,
        adp DOUBLE,
        difference_vs_adp DOUBLE,
        utilization_score DOUBLE,
        last_week_difference INT,
        kendall_valenzuela DOUBLE,
        matthew_berry DOUBLE,
        matthew_freedman DOUBLE,
        dwain_mcfarland DOUBLE,
        season INT,
        ingestion_date DATE,
        source_file STRING
    )
    USING DELTA
    COMMENT 'Fantasy Life consensus rankings'
""")

# Overwrite for current season (FL rankings are a point-in-time snapshot)
(
    fl_ranks_df
    .select(
        'fl_id', 'fl_uuid', 'player', 'position', 'team', 'bye', 'tier',
        'consensus', 'adp', 'difference_vs_adp', 'utilization_score',
        'last_week_difference',
        'kendall_valenzuela', 'matthew_berry', 'matthew_freedman', 'dwain_mcfarland',
        'season', 'ingestion_date', 'source_file'
    )
    .write.format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable(f"{fl_prefix}.fact_fl_ranks")
)

fact_count = spark.table(f"{fl_prefix}.fact_fl_ranks").count()
print(f"  \u2713 {fl_prefix}.fact_fl_ranks: {fact_count} rows")

# COMMAND ----------

# DBTITLE 1,Match FL → Canonical Crosswalk
# Step 4: Match FL players to canonical crosswalk
match_fl_to_crosswalk(CATALOG, FL_SCHEMA, COMMON_SCHEMA, fl_players)

# COMMAND ----------

# DBTITLE 1,Archive Processed Files
# Step 5: Archive processed files
files = dbutils.fs.ls(SOURCE_PATH)
processed_files = [f for f in files if f.name.endswith('.csv') or f.name.endswith('.html')]

for file_info in processed_files:
    dest = f"{ARCHIVE_PATH}/{file_info.name}"
    dbutils.fs.mv(file_info.path, dest)
    print(f"  \u2713 Archived: {file_info.name}")

if not processed_files:
    print("  \u23ed No files to archive")

# COMMAND ----------

# DBTITLE 1,Verification
# MAGIC %md ## Verification

# COMMAND ----------

# DBTITLE 1,Verify Matching Coverage
# Verify: show crosswalk coverage and sample cross-source join
fl_prefix = f"{CATALOG}.{FL_SCHEMA}"
common_prefix = f"{CATALOG}.{COMMON_SCHEMA}"

print("=== Fantasy Life Player Matching Summary ===")
print()

total_fl = spark.table(f"{fl_prefix}.fact_fl_ranks").select('fl_id').distinct().count()
matched = spark.table(f"{fl_prefix}.fl_player_map").count()

print(f"Total FL players: {total_fl}")
print(f"Matched to crosswalk: {matched} ({100*matched/max(total_fl,1):.1f}%)")
print(f"Unmatched:            {total_fl - matched}")
print()

# Match method breakdown
print("Match method breakdown:")
spark.table(f"{fl_prefix}.fl_player_map").groupBy('match_method').count().show()

# Sample cross-source join (FL → crosswalk → Yahoo/ETR)
print("\nSample cross-source join (FL → crosswalk → Yahoo/ESPN):")
spark.sql(f"""
    SELECT
        r.player,
        r.position,
        r.team,
        r.consensus,
        r.tier,
        m.mfl_id,
        xw.yahoo_id,
        xw.espn_id,
        xw.fantasypros_id
    FROM {fl_prefix}.fact_fl_ranks r
    INNER JOIN {fl_prefix}.fl_player_map m ON r.fl_id = m.fl_id
    INNER JOIN {common_prefix}.dim_ff_player_ids xw ON m.mfl_id = xw.mfl_id
    ORDER BY r.consensus
    LIMIT 15
""").show(truncate=False)

# COMMAND ----------

# DBTITLE 1,Exit
dbutils.notebook.exit(f'Success - FL load and match complete for season {SEASON}')