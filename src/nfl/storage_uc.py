"""Convenience re-export of Unity Catalog storage utilities.

This module exists so notebooks and scripts can use the short import path::

    from nfl.storage_uc import UCTableConfig, persist_to_uc_tables

instead of the full path::

    from nfl.common.storage import UCTableConfig, persist_to_uc_tables

All symbols are re-exported from :mod:`nfl.common.storage`.
"""

from nfl.common.storage import (
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
