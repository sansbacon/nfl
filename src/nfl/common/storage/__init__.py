"""Shared storage adapters for all NFL fantasy data sources.

Provides unified persistence to:
- Unity Catalog Delta tables (via PySpark)
- Unity Catalog Volumes (as Parquet/CSV/NDJSON files)
- Local Polars files (Parquet/CSV/NDJSON)
- PyIceberg tables (SQLite catalog, local dev only)
"""

from nfl.common.storage.unity_catalog import (
    UCTableConfig,
    UCVolumeConfig,
    UCWriteResult,
    WriteMode,
    VolumeFileFormat,
    persist_to_uc_tables,
    persist_to_uc_volume,
)
from nfl.common.storage.polars import persist_with_polars
from nfl.common.storage.iceberg import (
    IcebergCatalogConfig,
    IcebergNamespaceConfig,
    IcebergWriteResult,
    IcebergWriteMode,
    IdempotencyStore,
    persist_to_iceberg,
)

__all__ = [
    # Unity Catalog
    "UCTableConfig",
    "UCVolumeConfig",
    "UCWriteResult",
    "WriteMode",
    "VolumeFileFormat",
    "persist_to_uc_tables",
    "persist_to_uc_volume",
    # Polars
    "persist_with_polars",
    # Iceberg
    "IcebergCatalogConfig",
    "IcebergNamespaceConfig",
    "IcebergWriteResult",
    "IcebergWriteMode",
    "IdempotencyStore",
    "persist_to_iceberg",
]
