"""Shared storage adapters for all NFL fantasy data sources.

Provides unified persistence to:
- Unity Catalog Delta tables (via PySpark)
- Unity Catalog Volumes (as Parquet/CSV/NDJSON files)
- Local Polars files (Parquet/CSV/NDJSON)
- PyIceberg tables (SQLite catalog, local dev only)
"""

from nfl.common.storage.iceberg import (
    IcebergCatalogConfig,
    IcebergNamespaceConfig,
    IcebergWriteMode,
    IcebergWriteResult,
    IdempotencyStore,
    persist_to_iceberg,
)
from nfl.common.storage.polars import persist_with_polars
from nfl.common.storage.unity_catalog import (
    UCTableConfig,
    UCVolumeConfig,
    UCWriteResult,
    VolumeFileFormat,
    WriteMode,
    load_uc_table,
    persist_to_uc_tables,
    persist_to_uc_volume,
)

__all__ = [
    # Iceberg
    "IcebergCatalogConfig",
    "IcebergNamespaceConfig",
    "IcebergWriteMode",
    "IcebergWriteResult",
    "IdempotencyStore",
    # Unity Catalog
    "UCTableConfig",
    "UCVolumeConfig",
    "UCWriteResult",
    "VolumeFileFormat",
    "WriteMode",
    "load_uc_table",
    "persist_to_iceberg",
    "persist_to_uc_tables",
    "persist_to_uc_volume",
    # Polars
    "persist_with_polars",
]
