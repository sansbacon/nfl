"""Canonical player identity crosswalk management.

Loads and refreshes `dim_ff_player_ids` from nflreadpy, which serves as
the universal join key (`mfl_id`) across all fantasy data sources.
"""

from __future__ import annotations


def load_canonical_crosswalk(spark, catalog: str, schema: str) -> None:
    """Load nflreadpy player IDs into the canonical crosswalk table.

    Overwrites ``{catalog}.{schema}.dim_ff_player_ids`` with the latest
    data from nflreadpy.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session.
    catalog : str
        Unity Catalog name (e.g. 'nfl').
    schema : str
        Schema name (e.g. 'common').
    """
    import nflreadpy as nflread

    ids_df = nflread.load_ff_playerids()
    spark_df = spark.createDataFrame(ids_df.to_pandas())

    fq_table = f"{catalog}.{schema}.dim_ff_player_ids"
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
    spark_df.write.format("delta").mode("overwrite").option(
        "overwriteSchema", "true"
    ).saveAsTable(fq_table)

    count = spark.table(fq_table).count()
    print(f"  \u2713 {fq_table}: {count} players loaded from nflreadpy")
