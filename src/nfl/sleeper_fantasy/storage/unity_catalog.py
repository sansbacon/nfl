"""Unity Catalog persistence adapter for Sleeper Fantasy datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import polars as pl

from nfl.common.storage import (
    UCTableConfig,
    UCVolumeConfig,
    UCWriteResult,
    WriteMode,
    VolumeFileFormat,
    persist_to_uc_tables,
    persist_to_uc_volume,
)


@dataclass(frozen=True, slots=True)
class SleeperUCTableConfig:
    """Sleeper-specific UC table configuration."""

    catalog: str = "nfl"
    schema: str = "sl"
    write_mode: WriteMode = "overwrite"
    merge_keys: tuple[str, ...] = ()
    table_prefix: str = ""
    table_properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SleeperUCVolumeConfig:
    """Sleeper-specific UC volume configuration."""

    catalog: str = "nfl"
    schema: str = "sl"
    volume: str = "sl_volume"
    file_format: VolumeFileFormat = "parquet"
    subdirectory: str = "pipeline_output"


def persist_sleeper_to_uc_tables(
    frames: Mapping[str, pl.DataFrame],
    config: SleeperUCTableConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write Sleeper DataFrames as UC Delta tables."""
    cfg = config or SleeperUCTableConfig()
    table_config = UCTableConfig(
        catalog=cfg.catalog,
        schema=cfg.schema,
        write_mode=cfg.write_mode,
        merge_keys=cfg.merge_keys,
        table_prefix=cfg.table_prefix,
        table_properties=cfg.table_properties,
    )
    return persist_to_uc_tables(frames, config=table_config, dry_run=dry_run)


def persist_sleeper_to_uc_volume(
    frames: Mapping[str, pl.DataFrame],
    config: SleeperUCVolumeConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write Sleeper DataFrames as files to a UC Volume."""
    cfg = config or SleeperUCVolumeConfig()
    volume_config = UCVolumeConfig(
        catalog=cfg.catalog,
        schema=cfg.schema,
        volume=cfg.volume,
        file_format=cfg.file_format,
        subdirectory=cfg.subdirectory,
    )
    return persist_to_uc_volume(frames, config=volume_config, dry_run=dry_run)
