"""Unity Catalog persistence adapter for FantasyPros datasets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import polars as pl

from nfl.common.storage import (
    UCTableConfig,
    UCVolumeConfig,
    UCWriteResult,
    VolumeFileFormat,
    WriteMode,
    persist_to_uc_tables,
    persist_to_uc_volume,
)


@dataclass(frozen=True, slots=True)
class FantasyProsUCTableConfig:
    """FantasyPros-specific UC table configuration."""

    catalog: str = "nfl"
    schema: str = "fp"
    write_mode: WriteMode = "overwrite"
    merge_keys: tuple[str, ...] = ()
    table_prefix: str = ""
    table_properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FantasyProsUCVolumeConfig:
    """FantasyPros-specific UC volume configuration."""

    catalog: str = "nfl"
    schema: str = "fp"
    volume: str = "fp_volume"
    file_format: VolumeFileFormat = "parquet"
    subdirectory: str = "pipeline_output"

    @property
    def base_path(self) -> str:
        parts = f"/Volumes/{self.catalog}/{self.schema}/{self.volume}"
        if self.subdirectory:
            parts = f"{parts}/{self.subdirectory.strip('/')}"
        return parts


def persist_fp_to_uc_tables(
    frames: Mapping[str, pl.DataFrame],
    config: FantasyProsUCTableConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write FantasyPros DataFrames as UC Delta tables."""
    cfg = config or FantasyProsUCTableConfig()
    table_config = UCTableConfig(
        catalog=cfg.catalog,
        schema=cfg.schema,
        write_mode=cfg.write_mode,
        merge_keys=cfg.merge_keys,
        table_prefix=cfg.table_prefix,
        table_properties=cfg.table_properties,
    )
    return persist_to_uc_tables(frames, config=table_config, dry_run=dry_run)


def persist_fp_to_uc_volume(
    frames: Mapping[str, pl.DataFrame],
    config: FantasyProsUCVolumeConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write FantasyPros DataFrames as files to a UC Volume."""
    cfg = config or FantasyProsUCVolumeConfig()
    volume_config = UCVolumeConfig(
        catalog=cfg.catalog,
        schema=cfg.schema,
        volume=cfg.volume,
        file_format=cfg.file_format,
        subdirectory=cfg.subdirectory,
    )
    return persist_to_uc_volume(frames, config=volume_config, dry_run=dry_run)
