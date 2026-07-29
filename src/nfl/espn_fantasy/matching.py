"""ESPN-specific player matching to canonical crosswalk.

Primary match is a direct espn_id join (65%+ coverage in crosswalk).
Fallback is normalized name + position for remaining players.
"""

from __future__ import annotations

import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql.window import Window

from nfl.common.matching import normalize_name


def match_espn_to_crosswalk(spark, catalog: str, espn_schema: str, common_schema: str) -> None:
    """Match ESPN players to canonical crosswalk via espn_id.

    Primary: direct join on espn_id (already in dim_ff_player_ids).
    Fallback: normalize_name + position match for players without espn_id coverage.
    Persists result to espn_player_map.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session.
    catalog : str
        Unity Catalog name (e.g. 'nfl').
    espn_schema : str
        ESPN schema name (e.g. 'espn').
    common_schema : str
        Common schema name (e.g. 'common').
    """
    espn_prefix = f"{catalog}.{espn_schema}"
    common_prefix = f"{catalog}.{common_schema}"

    # Get distinct ESPN players from ranks table
    espn_players = spark.sql(f"""
        SELECT DISTINCT espn_id, player, position, team
        FROM {espn_prefix}.fact_espn_ranks
        WHERE is_current = true AND espn_id IS NOT NULL
    """)

    crosswalk = spark.table(f"{common_prefix}.dim_ff_player_ids")

    # Method 1: Direct espn_id join
    direct_match = (
        espn_players.alias("e")
        .join(
            crosswalk.alias("c"),
            F.col("e.espn_id") == F.col("c.espn_id").cast("int"),
            "inner",
        )
        .select(
            F.col("e.espn_id").alias("espn_id"),
            F.col("c.mfl_id"),
            F.lit("direct_espn_id").alias("match_method"),
        )
    )
    direct_count = direct_match.count()

    # Method 2: Name + position fallback for unmatched
    matched_ids = direct_match.select("espn_id")
    unmatched = espn_players.join(matched_ids, "espn_id", "left_anti")

    normalize_name_udf = F.udf(normalize_name, T.StringType())

    unmatched_norm = unmatched.withColumn(
        "merge_name", normalize_name_udf(F.col("player"))
    )
    crosswalk_norm = crosswalk.filter(F.col("merge_name").isNotNull())

    name_match = (
        unmatched_norm.alias("e")
        .join(
            crosswalk_norm.alias("c"),
            (F.col("e.merge_name") == F.col("c.merge_name"))
            & (F.col("e.position") == F.col("c.position")),
            "inner",
        )
        .select(
            F.col("e.espn_id").alias("espn_id"),
            F.col("c.mfl_id"),
            F.lit("name_position").alias("match_method"),
        )
    )
    name_count = name_match.count()

    # Combine and deduplicate (one mfl_id per espn_id)
    all_matches = direct_match.unionByName(name_match)
    w = Window.partitionBy("espn_id").orderBy(
        F.when(F.col("match_method") == "direct_espn_id", 1).otherwise(2)
    )
    deduped = (
        all_matches.withColumn("rn", F.row_number().over(w))
        .filter("rn = 1")
        .drop("rn")
    )

    # Persist to espn_player_map
    map_table = f"{espn_prefix}.espn_player_map"
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {map_table} (
            espn_id INT,
            mfl_id BIGINT,
            match_method STRING
        ) USING DELTA
    """)

    deduped.createOrReplaceTempView("_espn_map_source")
    spark.sql(f"""
        MERGE INTO {map_table} AS target
        USING _espn_map_source AS source
        ON target.espn_id = source.espn_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)
    spark.catalog.dropTempView("_espn_map_source")

    total = spark.table(map_table).count()
    total_espn = espn_players.count()
    print(
        f"  \u2713 espn_player_map: {total} matched "
        f"(direct_espn_id={direct_count}, name_position={name_count})"
    )
    print(f"  \u26a0 {total_espn - total} ESPN players unmatched")
