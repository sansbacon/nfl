"""Pipeline orchestration for NFLverse ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import polars as pl

from nfl.entity_standardization.pipeline import EntityStandardizer, StandardizationConfig, StandardizationResult
from nfl.nflverse_fantasy.api import NflverseApiClient
from nfl.nflverse_fantasy.storage.iceberg import IcebergNamespaceConfig, IcebergWriteResult, persist_to_iceberg
from nfl.nflverse_fantasy.storage.polars import persist_with_polars
from nfl.nflverse_fantasy.transforms import transform


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    seasons: list[int] | None = None
    enabled_entities: list[str] | None = None
    storage_target: str = "none"
    polars_output_dir: str | Path = "./output/nflverse_polars"
    polars_file_format: str = "parquet"
    iceberg_namespaces: IcebergNamespaceConfig = field(default_factory=IcebergNamespaceConfig)
    iceberg_idempotency_store: str | Path = ".iceberg/nflverse_write_log.json"
    iceberg_dry_run: bool = True
    standardization_enabled: bool = False
    standardization_config: StandardizationConfig | None = None


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    frames: dict[str, pl.DataFrame]
    polars_outputs: dict[str, Path]
    iceberg_outputs: list[IcebergWriteResult]
    standardization_result: StandardizationResult | None = None


def _build_client() -> NflverseApiClient:
    return NflverseApiClient(validate_contracts=True)


def _collect_entities(client: Any, seasons: list[int] | None, enabled_entities: set[str] | None) -> dict[str, list[dict[str, Any]]]:
    getter_map = {
        "pbp": lambda: client.get_pbp(seasons=seasons),
        "player_stats": lambda: client.get_player_stats(seasons=seasons),
        "team_stats": lambda: client.get_team_stats(seasons=seasons),
        "schedules": lambda: client.get_schedules(seasons=seasons),
        "players": lambda: client.get_players(),
        "rosters": lambda: client.get_rosters(seasons=seasons),
        "rosters_weekly": lambda: client.get_rosters_weekly(seasons=seasons),
        "snap_counts": lambda: client.get_snap_counts(seasons=seasons),
        "nextgen_stats": lambda: client.get_nextgen_stats(seasons=seasons),
        "ftn_charting": lambda: client.get_ftn_charting(seasons=seasons),
        "participation": lambda: client.get_participation(seasons=seasons),
        "draft_picks": lambda: client.get_draft_picks(seasons=seasons),
        "injuries": lambda: client.get_injuries(seasons=seasons),
        "contracts": lambda: client.get_contracts(),
        "officials": lambda: client.get_officials(seasons=seasons),
        "combine": lambda: client.get_combine(),
        "depth_charts": lambda: client.get_depth_charts(seasons=seasons),
        "trades": lambda: client.get_trades(seasons=seasons),
        "ff_playerids": lambda: client.get_ff_playerids(),
        "ff_rankings": lambda: client.get_ff_rankings(seasons=seasons),
        "ff_opportunity": lambda: client.get_ff_opportunity(seasons=seasons),
    }

    entities: dict[str, list[dict[str, Any]]] = {}
    for name, loader in getter_map.items():
        if enabled_entities is not None and name not in enabled_entities:
            continue
        entities[name] = loader()
    return entities


def _build_standardization_records(players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in players:
        player_id = str(row.get("gsis_id") or row.get("player_id") or row.get("pfr_id") or row.get("_record_hash") or "")
        display_name = str(row.get("display_name") or row.get("player_name") or "").strip()
        if not display_name:
            first = str(row.get("first_name") or "").strip()
            last = str(row.get("last_name") or "").strip()
            display_name = f"{first} {last}".strip()
        out.append(
            {
                "source_system": "nflverse",
                "source_entity_id": player_id,
                "raw_player_name": display_name,
                "raw_team_name": str(row.get("recent_team") or row.get("team") or ""),
                "raw_position": str(row.get("position") or ""),
                "season": int(row.get("season", 0) or 0),
            }
        )
    return out


def run_pipeline(
    config: PipelineConfig | None = None,
    api_client: Any | None = None,
) -> PipelineRunResult:
    cfg = config or PipelineConfig()
    client = api_client or _build_client()
    enabled = set(cfg.enabled_entities) if cfg.enabled_entities else None

    entities = _collect_entities(client, seasons=cfg.seasons, enabled_entities=enabled)
    frames = transform(entities)

    standardization_result: StandardizationResult | None = None
    if cfg.standardization_enabled and "players" in entities:
        standardizer = EntityStandardizer(config=cfg.standardization_config or StandardizationConfig())
        std_records = _build_standardization_records(entities["players"])
        standardization_result = standardizer.standardize_batch(std_records)
        frames.update(
            {
                key: value
                for key, value in standardization_result.tables.items()
                if key in {
                    "std_standardized_outputs",
                    "std_match_queue",
                    "std_rescued_records",
                    "std_source_to_canonical_map",
                }
            }
        )

    polars_outputs: dict[str, Path] = {}
    iceberg_outputs: list[IcebergWriteResult] = []

    if cfg.storage_target in {"polars", "both"}:
        polars_outputs = persist_with_polars(frames, output_dir=cfg.polars_output_dir, file_format=cfg.polars_file_format)

    if cfg.storage_target in {"iceberg", "both"}:
        iceberg_outputs = persist_to_iceberg(
            frames=frames,
            namespace_config=cfg.iceberg_namespaces,
            idempotency_store_path=cfg.iceberg_idempotency_store,
            dry_run=cfg.iceberg_dry_run,
        )

    return PipelineRunResult(
        frames=frames,
        polars_outputs=polars_outputs,
        iceberg_outputs=iceberg_outputs,
        standardization_result=standardization_result,
    )
