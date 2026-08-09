"""Shared storage adapters for all NFL fantasy data sources.

Provides unified persistence to:
- Local Polars files (Parquet/CSV/NDJSON)
- DuckDB tables (embedded analytical DB) — requires ``nfl[duckdb]``
- PyIceberg tables (SQLite catalog, local dev only) — requires ``nfl[iceberg]``

For Unity Catalog Delta tables and Volumes, install ``nfl-databricks``.
"""

from nfl.common.storage.polars import persist_with_polars

__all__ = [
    "persist_with_polars",
]

try:
    from nfl.common.storage.iceberg import (
        IcebergCatalogConfig,
        IcebergNamespaceConfig,
        IcebergWriteMode,
        IcebergWriteResult,
        IdempotencyStore,
        persist_to_iceberg,
    )

    __all__ += [
        "IcebergCatalogConfig",
        "IcebergNamespaceConfig",
        "IcebergWriteMode",
        "IcebergWriteResult",
        "IdempotencyStore",
        "persist_to_iceberg",
    ]
except ModuleNotFoundError:
    # pyiceberg is not installed; iceberg symbols are unavailable.
    pass

try:
    from nfl.common.storage.duckdb import (
        DuckDBConfig,
        DuckDBWriteResult,
        compute_record_hash,
        get_connection,
        load_duckdb_table,
        merge_scd2,
        persist_to_duckdb,
        query_duckdb,
    )

    __all__ += [
        "DuckDBConfig",
        "DuckDBWriteResult",
        "compute_record_hash",
        "get_connection",
        "load_duckdb_table",
        "merge_scd2",
        "persist_to_duckdb",
        "query_duckdb",
    ]
except ImportError:
    # duckdb is not installed; duckdb symbols are unavailable.
    pass
