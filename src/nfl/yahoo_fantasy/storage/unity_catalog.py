"""Unity Catalog persistence adapter for Yahoo Fantasy datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

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

SportCode = Literal["nfl", "nba"]


@dataclass(frozen=True, slots=True)
class YahooUCTableConfig:
    """Yahoo-specific UC table configuration with sport-based schema routing."""

    catalog: str = "nfl"
    nfl_schema: str = "yh"
    nba_schema: str = "yh_nba"
    common_schema: str = "yh"
    write_mode: WriteMode = "overwrite"
    merge_keys: tuple[str, ...] = ()
    table_prefix: str = ""
    table_properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class YahooUCVolumeConfig:
    """Yahoo-specific UC volume configuration."""

    catalog: str = "nfl"
    schema: str = "yh"
    volume: str = "yh_volume"
    file_format: VolumeFileFormat = "parquet"
    subdirectory: str = "pipeline_output"


def _parse_entity_and_sport(frame_name: str) -> tuple[str, SportCode | None]:
    """Extract entity name and sport from prefixed frame name."""
    if frame_name.startswith("nfl_"):
        return frame_name.removeprefix("nfl_"), "nfl"
    if frame_name.startswith("nba_"):
        return frame_name.removeprefix("nba_"), "nba"
    return frame_name, None


def _resolve_schema(sport: SportCode | None, config: YahooUCTableConfig) -> str:
    """Route to the correct UC schema based on sport."""
    if sport == "nfl":
        return config.nfl_schema
    if sport == "nba":
        return config.nba_schema
    return config.common_schema


def persist_yahoo_to_uc_tables(
    frames: Mapping[str, pl.DataFrame],
    config: YahooUCTableConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write Yahoo Fantasy DataFrames as UC Delta tables with sport-based schema routing."""
    cfg = config or YahooUCTableConfig()
    results: list[UCWriteResult] = []

    # Group frames by resolved schema
    schema_groups: dict[str, dict[str, pl.DataFrame]] = {}
    for frame_name, frame in frames.items():
        entity, sport = _parse_entity_and_sport(frame_name)
        schema = _resolve_schema(sport, cfg)
        schema_groups.setdefault(schema, {})[entity] = frame

    for schema, entity_frames in schema_groups.items():
        table_config = UCTableConfig(
            catalog=cfg.catalog,
            schema=schema,
            write_mode=cfg.write_mode,
            merge_keys=cfg.merge_keys,
            table_prefix=cfg.table_prefix,
            table_properties=cfg.table_properties,
        )
        results.extend(persist_to_uc_tables(entity_frames, config=table_config, dry_run=dry_run))

    return results


def persist_yahoo_to_uc_volume(
    frames: Mapping[str, pl.DataFrame],
    config: YahooUCVolumeConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write Yahoo Fantasy DataFrames as files to a UC Volume."""
    cfg = config or YahooUCVolumeConfig()
    volume_config = UCVolumeConfig(
        catalog=cfg.catalog,
        schema=cfg.schema,
        volume=cfg.volume,
        file_format=cfg.file_format,
        subdirectory=cfg.subdirectory,
    )
    return persist_to_uc_volume(frames, config=volume_config, dry_run=dry_run)
