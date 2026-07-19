"""Library workflow orchestration for FantasyPros datasets."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal

import polars as pl

from nfl.fantasypros_fantasy.api import FantasyProsApiClient
from nfl.fantasypros_fantasy.matching import build_fp_yahoo_crosswalk
from nfl.fantasypros_fantasy.storage.iceberg import (
    IcebergCatalogConfig,
    IcebergNamespaceConfig,
    IcebergWriteResult,
    WriteMode,
    persist_to_iceberg,
)
from nfl.fantasypros_fantasy.storage.polars import persist_with_polars
from nfl.fantasypros_fantasy.transforms import transform
from nfl.fantasypros_fantasy.validation import get_contract, validate_polars_frame
from nfl.entity_standardization.pipeline import EntityStandardizer, StandardizationConfig, StandardizationResult

StorageTarget = Literal["none", "polars", "iceberg", "both"]
SportCode = Literal["nfl"]


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    timeout_seconds: int = 30
    validate_contracts: bool = True
    effective_date: date | None = None
    storage_target: StorageTarget = "none"
    polars_output_dir: str | Path = "./output/fantasypros_polars"
    polars_file_format: str = "parquet"
    iceberg_catalog: IcebergCatalogConfig = field(default_factory=IcebergCatalogConfig)
    iceberg_namespaces: IcebergNamespaceConfig = field(default_factory=IcebergNamespaceConfig)
    iceberg_mode: WriteMode = "upsert"
    iceberg_idempotency_store: str | Path = ".iceberg/fantasypros_write_log.json"
    iceberg_dry_run: bool = True
    standardization_enabled: bool = False
    standardization_config: StandardizationConfig | None = None


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    season: int
    sport: SportCode
    frames: dict[str, pl.DataFrame]
    polars_outputs: dict[str, Path]
    iceberg_outputs: list[IcebergWriteResult]
    standardization_result: StandardizationResult | None = None


def _build_client(config: PipelineConfig) -> FantasyProsApiClient:
    return FantasyProsApiClient(
        timeout_seconds=config.timeout_seconds,
        validate_contracts=config.validate_contracts,
    )


def _materialize_current_adp_table(frames: dict[str, pl.DataFrame]) -> pl.DataFrame:
    players = frames.get("fp_player", pl.DataFrame())
    adp = frames.get("nfl_fp_adp_snapshot", pl.DataFrame())

    if players.is_empty() or adp.is_empty():
        contract = get_contract(entity="fp_current_adp", sport="nfl")
        empty = pl.DataFrame({col: [] for col in contract.required + contract.optional})
        validate_polars_frame(empty, contract)
        return empty

    current_adp = adp.filter(pl.col("is_current") == True)

    materialized = (
        current_adp.join(players, on="fp_player_id", how="inner")
        .with_columns(
            pl.col("adp")
            .rank(method="dense")
            .over(["season", "position"])
            .cast(pl.Int64)
            .alias("position_rank")
        )
        .select(
            [
                "fp_player_id",
                "full_name",
                "position",
                "team",
                "season",
                "rank",
                "position_rank",
                "adp",
                "adp_espn",
                "adp_sleeper",
                "adp_cbs",
                "adp_nfl",
                "adp_rtsports",
                "adp_fantrax",
                "adp_realtime",
                "adp_formatted",
                "high",
                "low",
                "stdev",
                "bye_week",
                "effective_date",
            ]
        )
        .sort(["season", "rank", "fp_player_id"])
    )

    contract = get_contract(entity="fp_current_adp", sport="nfl")
    validate_polars_frame(materialized, contract)
    return materialized


def run_pipeline(
    season: int,
    sport: SportCode = "nfl",
    config: PipelineConfig | None = None,
    api_client: Any | None = None,
    yahoo_players: list[dict[str, Any]] | None = None,
) -> PipelineRunResult:
    cfg = config or PipelineConfig()
    client = api_client if api_client is not None else _build_client(cfg)

    players = client.get_players(season)
    adp_rows = client.get_adp_snapshots(season, effective_date=cfg.effective_date)

    crosswalk_rows: list[dict[str, Any]] = []
    if yahoo_players:
        crosswalk_rows = build_fp_yahoo_crosswalk(
            fp_players=players,
            yahoo_players=yahoo_players,
            adp_rows=adp_rows,
        )

    frames = transform(
        common_entities={"fp_player": players},
        nfl_entities={
            "fp_adp_snapshot": adp_rows,
            "fp_yahoo_player_map": crosswalk_rows,
        },
    )
    frames["nfl_fp_current_adp"] = _materialize_current_adp_table(frames)

    standardization_result: StandardizationResult | None = None
    if cfg.standardization_enabled:
        standardizer = EntityStandardizer(config=cfg.standardization_config or StandardizationConfig())
        std_records = [
            {
                "source_system": "fantasypros",
                "source_entity_id": str(player.get("fp_player_id") or ""),
                "raw_player_name": str(player.get("full_name") or ""),
                "raw_team_name": str(player.get("team") or ""),
                "raw_position": str(player.get("position") or ""),
                "season": season,
            }
            for player in players
        ]
        standardization_result = standardizer.standardize_batch(std_records)
        frames.update(
            {
                key: value
                for key, value in standardization_result.tables.items()
                if key in {"std_standardized_outputs", "std_match_queue", "std_rescued_records", "std_source_to_canonical_map"}
            }
        )

    polars_outputs: dict[str, Path] = {}
    iceberg_outputs: list[IcebergWriteResult] = []

    if cfg.storage_target in {"polars", "both"}:
        polars_outputs = persist_with_polars(frames, output_dir=cfg.polars_output_dir, file_format=cfg.polars_file_format)

    if cfg.storage_target in {"iceberg", "both"}:
        iceberg_outputs = persist_to_iceberg(
            frames=frames,
            catalog_config=cfg.iceberg_catalog,
            namespace_config=cfg.iceberg_namespaces,
            default_mode=cfg.iceberg_mode,
            idempotency_store_path=cfg.iceberg_idempotency_store,
            dry_run=cfg.iceberg_dry_run,
        )

    return PipelineRunResult(
        season=season,
        sport=sport,
        frames=frames,
        polars_outputs=polars_outputs,
        iceberg_outputs=iceberg_outputs,
        standardization_result=standardization_result,
    )
