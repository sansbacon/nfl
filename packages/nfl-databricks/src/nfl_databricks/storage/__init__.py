"""Unity Catalog storage adapters for persisting Polars DataFrames.

Provides write utilities for:
- Unity Catalog Delta tables (via PySpark)
- Unity Catalog Volumes (as Parquet/CSV/NDJSON files)
"""

from nfl_databricks.storage.unity_catalog import (
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
    "UCTableConfig",
    "UCVolumeConfig",
    "UCWriteResult",
    "VolumeFileFormat",
    "WriteMode",
    "load_uc_table",
    "persist_to_uc_tables",
    "persist_to_uc_volume",
]
