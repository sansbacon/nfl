"""Library workflow orchestration interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import polars as pl
from requests_oauthlib import OAuth2Session

from nfl.yahoo_fantasy.api import YahooApiClient
from nfl.yahoo_fantasy.storage.iceberg import (
    IcebergCatalogConfig,
    IcebergNamespaceConfig,
    IcebergWriteResult,
    WriteMode,
    persist_to_iceberg,
)
from nfl.yahoo_fantasy.storage.polars import persist_with_polars
from nfl.yahoo_fantasy.transforms import transform
from nfl.yahoo_fantasy.views import AVAILABLE_VIEWS, build_materialized_views
from nfl.entity_standardization.pipeline import EntityStandardizer, StandardizationConfig, StandardizationResult

StorageTarget = Literal["none", "polars", "iceberg", "both"]
SportCode = Literal["nfl", "nba"]


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    timeout_seconds: int = 30
    cache_dir: str | Path = ".cache"
    use_cache: bool = True
    validate_contracts: bool = True
    start_week: int | None = None
    end_week: int | None = None
    storage_target: StorageTarget = "none"
    polars_output_dir: str | Path = "./output/polars"
    polars_file_format: str = "parquet"
    iceberg_catalog: IcebergCatalogConfig = field(default_factory=IcebergCatalogConfig)
    iceberg_namespaces: IcebergNamespaceConfig = field(default_factory=IcebergNamespaceConfig)
    iceberg_mode: WriteMode = "upsert"
    iceberg_idempotency_store: str | Path = ".iceberg/write_log.json"
    iceberg_dry_run: bool = True
    materialized_views_enabled: bool = False
    materialized_views: tuple[str, ...] = AVAILABLE_VIEWS
    standardization_enabled: bool = False
    standardization_config: StandardizationConfig | None = None


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    league_key: str
    sport: SportCode
    frames: dict[str, pl.DataFrame]
    polars_outputs: dict[str, Path]
    iceberg_outputs: list[IcebergWriteResult]
    standardization_result: StandardizationResult | None = None


def _build_client(oauth_session: OAuth2Session, config: PipelineConfig) -> YahooApiClient:
    return YahooApiClient(
        oauth_session=oauth_session,
        timeout_seconds=config.timeout_seconds,
        cache_dir=config.cache_dir,
        use_cache=config.use_cache,
        validate_contracts=config.validate_contracts,
    )


def _collect_common_entities(client: Any, league_key: str) -> dict[str, list[dict[str, Any]]]:
    league = client.get_league_metadata(league_key)
    return {
        "league": [league],
        "team": client.get_teams(league_key),
        "player": client.get_players(league_key),
        "draft_pick": client.get_draft_picks(league_key, season=league["season"]),
        "transaction": client.get_transactions(league_key, season=league["season"]),
        "stat_category": client.get_stat_categories(league_key, game_id=int(league["game_id"])),
        "scoring_rule": client.get_scoring_rules(league_key, season=int(league["season"])),
    }


def _resolve_weeks(league: dict[str, Any], config: PipelineConfig) -> list[int]:
    start_week = config.start_week
    end_week = config.end_week

    if start_week is None:
        start_week = int(league.get("start_week") or 1)
    if end_week is None:
        end_week = int(league.get("end_week") or league.get("current_week") or start_week)

    if start_week <= 0 or end_week <= 0:
        return [1]
    if end_week < start_week:
        start_week, end_week = end_week, start_week

    return list(range(start_week, end_week + 1))


def _collect_sport_entities(
    client: Any,
    league_key: str,
    sport: SportCode,
    league: dict[str, Any],
    teams: list[dict[str, Any]],
    config: PipelineConfig,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    standings = client.get_standings(league_key, sport=sport)
    if sport == "nfl":
        weeks = _resolve_weeks(league, config)
        team_keys = sorted({str(team.get("team_key") or "") for team in teams if team.get("team_key")})
        roster_entries = client.get_roster_entries(
            league_key,
            season=int(league.get("season") or 0),
            weeks=weeks,
            team_keys=team_keys,
        )
        player_stats_weekly = client.get_player_stats_weekly(
            league_key,
            season=int(league.get("season") or 0),
            roster_entries=roster_entries,
        )
        matchups = client.get_matchups(
            league_key,
            season=int(league.get("season") or 0),
            weeks=weeks,
        )
        return (
            {
                "standings": standings,
                "matchups": matchups,
                "roster_entries": roster_entries,
                "player_stats_weekly": player_stats_weekly,
            },
            {},
        )
    return ({}, {"standings": standings, "standing_category_scores": [], "roster_entries": [], "player_projections": []})


def run_pipeline(
    league_key: str,
    sport: SportCode,
    oauth_session: OAuth2Session | None = None,
    config: PipelineConfig | None = None,
    api_client: Any | None = None,
) -> PipelineRunResult:
    cfg = config or PipelineConfig()
    if api_client is None and oauth_session is None:
        raise ValueError("oauth_session is required when api_client is not provided")

    client = api_client if api_client is not None else _build_client(oauth_session, cfg)

    common_entities = _collect_common_entities(client, league_key)
    league_record = common_entities.get("league", [{}])[0]
    nfl_entities, nba_entities = _collect_sport_entities(
        client,
        league_key,
        sport,
        league=league_record,
        teams=common_entities.get("team", []),
        config=cfg,
    )

    frames = transform(common_entities=common_entities, nfl_entities=nfl_entities, nba_entities=nba_entities)

    standardization_result: StandardizationResult | None = None
    if cfg.standardization_enabled:
        standardizer = EntityStandardizer(config=cfg.standardization_config or StandardizationConfig())
        std_records = [
            {
                "source_system": "yahoo",
                "source_entity_id": str(team.get("team_key") or ""),
                "raw_player_name": "",
                "raw_team_name": str(team.get("team_name") or ""),
                "raw_position": "",
                "season": common_entities["league"][0]["season"] if common_entities.get("league") else 0,
            }
            for team in common_entities.get("team", [])
        ]
        standardization_result = standardizer.standardize_batch(std_records)
        frames.update(
            {
                key: value
                for key, value in standardization_result.tables.items()
                if key in {"std_standardized_outputs", "std_match_queue", "std_rescued_records", "std_source_to_canonical_map"}
            }
        )

    if cfg.materialized_views_enabled:
        frames.update(build_materialized_views(frames, requested_views=cfg.materialized_views))

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
        league_key=league_key,
        sport=sport,
        frames=frames,
        polars_outputs=polars_outputs,
        iceberg_outputs=iceberg_outputs,
        standardization_result=standardization_result,
    )
