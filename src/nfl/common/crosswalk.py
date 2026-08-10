"""Canonical player identity crosswalk management.

Loads and refreshes `dim_ff_player_ids` from nflreadpy, which serves as
the universal join key (`mfl_id`) across all fantasy data sources.

Supports two backends:
- **Ibis (preferred):** `load_crosswalk()` — works with any Ibis backend
- **PySpark (legacy):** `load_canonical_crosswalk()` — deprecated, kept for
  backward compatibility with existing Databricks notebooks
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ibis

_TABLE_NAME = "dim_ff_player_ids"


def _load_nflreadpy_arrow():
    """Load player IDs from nflreadpy and return as a PyArrow table.

    Shared by both the Ibis and legacy PySpark paths.
    """
    import nflreadpy as nflread

    ids_df = nflread.load_ff_playerids()
    return ids_df.to_arrow()


def load_crosswalk(
    backend: ibis.BaseBackend,
    *,
    database: str = "main",
    table_name: str = _TABLE_NAME,
) -> ibis.Table:
    """Load nflreadpy player IDs into the crosswalk table via Ibis.

    Overwrites ``{database}.{table_name}`` with the latest data from
    nflreadpy. Returns the resulting table expression.

    Parameters
    ----------
    backend : ibis.BaseBackend
        Active Ibis backend connection.
    database : str
        Schema/database to write into (e.g. 'main' for DuckDB,
        'nfl.common' for PySpark/UC).
    table_name : str
        Table name (default: 'dim_ff_player_ids').

    Returns
    -------
    ibis.Table
        The persisted crosswalk table.
    """
    import ibis as _ibis

    arrow_table = _load_nflreadpy_arrow()
    source = _ibis.memtable(arrow_table)

    # Use the _parse_table_name pattern for schema-qualified names
    backend.create_table(
        table_name,
        source,
        database=database,
        overwrite=True,
    )

    result = backend.table(table_name, database=database)
    count = result.count().execute()
    print(f"  \u2713 {database}.{table_name}: {count} players loaded from nflreadpy")
    return result


def read_crosswalk(
    backend: ibis.BaseBackend,
    *,
    database: str = "main",
    table_name: str = _TABLE_NAME,
) -> ibis.Table:
    """Read the existing crosswalk table from the backend.

    Parameters
    ----------
    backend : ibis.BaseBackend
        Active Ibis backend connection.
    database : str
        Schema/database containing the table.
    table_name : str
        Table name (default: 'dim_ff_player_ids').

    Returns
    -------
    ibis.Table
        The crosswalk table expression.

    Raises
    ------
    ibis.common.exceptions.IbisError
        If the table does not exist.
    """
    return backend.table(table_name, database=database)


# ---------------------------------------------------------------------------
# Legacy PySpark interface (deprecated)
# ---------------------------------------------------------------------------


def load_canonical_crosswalk(spark, catalog: str, schema: str) -> None:
    """Load nflreadpy player IDs into the canonical crosswalk table.

    .. deprecated::
        Use :func:`load_crosswalk` with an Ibis backend instead.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session.
    catalog : str
        Unity Catalog name (e.g. 'nfl').
    schema : str
        Schema name (e.g. 'common').
    """
    warnings.warn(
        "load_canonical_crosswalk() is deprecated. "
        "Use load_crosswalk(backend, database='catalog.schema') instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    import nflreadpy as nflread

    ids_df = nflread.load_ff_playerids()
    spark_df = spark.createDataFrame(ids_df.to_pandas())

    fq_table = f"{catalog}.{schema}.{_TABLE_NAME}"
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
    spark_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        fq_table
    )

    count = spark.table(fq_table).count()
    print(f"  \u2713 {fq_table}: {count} players loaded from nflreadpy")
