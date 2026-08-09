"""Shared storage adapters for all NFL fantasy data sources.

Provides unified persistence to:
- Local Polars files (Parquet/CSV/NDJSON)
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
