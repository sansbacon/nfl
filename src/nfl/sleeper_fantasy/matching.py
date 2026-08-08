"""Sleeper player matching to canonical crosswalk.

Matches SleeperPlayer records to nfl.common.dim_ff_player_ids
via normalized name + position. Persists sl_player_map
(sleeper_id → mfl_id) for downstream joins.
"""

from __future__ import annotations

import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql.window import Window

from nfl.common.matching import normalize_name


def match_sleeper_to_crosswalk(
    spark,
    catalog: str,
    sleeper_schema: str,
    common_schema: str,
) -> None:
    """Match Sleeper players to canonical crosswalk via name + position.

    Reads dim_sl_players, normalizes names, and joins to
    dim_ff_player_ids.merge_name + position. Persists the result
    as sl_player_map (sleeper_id → mfl_id).

    Parameters
    ----------
    spark : SparkSession
        Active Spark session.
    catalog : str
        Unity Catalog name (e.g. 'nfl').
    sleeper_schema : str
        Sleeper schema name (e.g. 'sl').
    common_schema : str
        Common schema name (e.g. 'common').
    """
    sl_prefix = f"{catalog}.{sleeper_schema}"
    common_prefix = f"{catalog}.{common_schema}"

    # Load distinct Sleeper players
    sl_players = spark.table(f"{sl_prefix}.dim_sl_players").filter(
        F.col("full_name").isNotNull() & F.col("position").isNotNull()
    )

    crosswalk = spark.table(f"{common_prefix}.dim_ff_player_ids").filter(
        F.col("merge_name").isNotNull()
    )

    # UDF for name normalization
    normalize_name_udf = F.udf(normalize_name, T.StringType())

    # Method 1: Normalized name + position
    sl_norm = sl_players.withColumn(
        "merge_name", normalize_name_udf(F.col("full_name"))
    ).filter(F.col("merge_name") != "")

    name_match = (
        sl_norm.alias("s")
        .join(
            crosswalk.alias("c"),
            (F.col("s.merge_name") == F.col("c.merge_name"))
            & (F.col("s.position") == F.col("c.position")),
            "inner",
        )
        .select(
            F.col("s.sleeper_player_id").alias("sleeper_id"),
            F.col("c.mfl_id"),
            F.lit("name_position").alias("match_method"),
        )
    )

    # Method 2: Name-only fallback (last + first 3 chars) for remaining
    matched_ids = name_match.select("sleeper_id")
    unmatched = sl_norm.join(matched_ids, sl_norm.sleeper_player_id == matched_ids.sleeper_id, "left_anti")

    # Build first_name / last_name normalized components for fuzzy
    unmatched_parts = unmatched.withColumn(
        "norm_last", normalize_name_udf(F.col("last_name"))
    ).withColumn(
        "norm_first_prefix", F.substring(normalize_name_udf(F.col("first_name")), 1, 3)
    ).filter(
        (F.col("norm_last") != "") & (F.col("norm_first_prefix") != "")
    )

    # For crosswalk: extract last name portion (everything after first space)
    # merge_name is already "firstname lastname" normalized
    crosswalk_split = crosswalk.withColumn(
        "name_parts", F.split(F.col("merge_name"), " ")
    ).withColumn(
        "cw_first_prefix", F.substring(F.col("name_parts")[0], 1, 3)
    ).withColumn(
        "cw_last",
        F.when(F.size("name_parts") > 1, F.col("name_parts")[F.size("name_parts") - 1])
        .otherwise(F.col("name_parts")[0]),
    ).filter(
        (F.col("cw_last") != "") & (F.col("cw_first_prefix") != "")
    )

    fuzzy_match = (
        unmatched_parts.alias("s")
        .join(
            crosswalk_split.alias("c"),
            (F.col("s.norm_last") == F.col("c.cw_last"))
            & (F.col("s.norm_first_prefix") == F.col("c.cw_first_prefix"))
            & (F.col("s.position") == F.col("c.position")),
            "inner",
        )
        .select(
            F.col("s.sleeper_player_id").alias("sleeper_id"),
            F.col("c.mfl_id"),
            F.lit("fuzzy_name_position").alias("match_method"),
        )
    )

    # Combine and deduplicate (one mfl_id per sleeper_id, prefer name_position)
    all_matches = name_match.unionByName(fuzzy_match)
    w = Window.partitionBy("sleeper_id").orderBy(
        F.when(F.col("match_method") == "name_position", 1).otherwise(2)
    )
    deduped = (
        all_matches.withColumn("rn", F.row_number().over(w))
        .filter("rn = 1")
        .drop("rn")
    )

    # Persist to sl_player_map
    map_table = f"{sl_prefix}.sl_player_map"
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {map_table} (
            sleeper_id STRING,
            mfl_id BIGINT,
            match_method STRING
        ) USING DELTA
    """)

    deduped.createOrReplaceTempView("_sl_map_source")
    spark.sql(f"""
        MERGE INTO {map_table} AS target
        USING _sl_map_source AS source
        ON target.sleeper_id = source.sleeper_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)
    spark.catalog.dropTempView("_sl_map_source")

    total = spark.table(map_table).count()
    name_count = name_match.count()
    fuzzy_count = fuzzy_match.count()
    total_sl = sl_players.count()
    print(
        f"  \u2713 sl_player_map: {total} matched "
        f"(name_position={name_count}, fuzzy={fuzzy_count})"
    )
    print(f"  \u26a0 {total_sl - total} Sleeper players unmatched")
