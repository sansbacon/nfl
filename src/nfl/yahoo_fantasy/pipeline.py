"""Library workflow orchestration interfaces."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import polars as pl
from requests_oauthlib import OAuth2Session

from nfl.common.storage import UCWriteResult
from nfl.entity_standardization.pipeline import (
    EntityStandardizer,
    StandardizationConfig,
    StandardizationResult,
)
from nfl.yahoo_fantasy.api import YahooApiClient
from nfl.yahoo_fantasy.storage.iceberg import (
    IcebergCatalogConfig,
    IcebergNamespaceConfig,
    IcebergWriteResult,
    WriteMode,
    persist_to_iceberg,
)
from nfl.yahoo_fantasy.storage.polars import persist_with_polars
from nfl.yahoo_fantasy.storage.unity_catalog import (
    YahooUCTableConfig,
    YahooUCVolumeConfig,
)
from nfl.yahoo_fantasy.transforms import transform
from nfl.yahoo_fantasy.views import AVAILABLE_VIEWS, build_materialized_views

StorageTarget = Literal["none", "polars", "iceberg", "both", "unity_catalog", "uc_volume"]
SportCode = Literal["nfl", "nba"]


@dataclass(frozen=True, slots=True)
class PipelineDiagnosticsConfig:
    enabled: bool = False
    include_stage_samples: bool = False
    sample_limit: int = 5
    capture_request_stats: bool = True
    capture_frame_summaries: bool = True
    emit_warnings: bool = True
    emit_stage_progress: bool = False


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    timeout_seconds: int = 30
    cache_dir: str | Path = ".cache"
    use_cache: bool = True
    validate_contracts: bool = True
    request_interval_seconds: float = 0.0
    max_request_retries: int = 2
    backoff_base_seconds: float = 1.0
    player_page_size: int = 25
    require_nfl_player_points: bool = False
    include_nfl_unrostered_player_stats: bool = False
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
    include_non_target_sport_frames: bool = False
    diagnostics: PipelineDiagnosticsConfig = field(default_factory=PipelineDiagnosticsConfig)
    uc_table_config: YahooUCTableConfig = field(default_factory=YahooUCTableConfig)
    uc_volume_config: YahooUCVolumeConfig = field(default_factory=YahooUCVolumeConfig)
    uc_dry_run: bool = True


@dataclass(frozen=True, slots=True)
class StageDiagnostic:
    stage_name: str
    status: Literal["ok", "warning", "error"]
    duration_ms: float
    entity_counts: dict[str, int] = field(default_factory=dict)
    frame_counts: dict[str, int] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class PipelineDiagnostics:
    started_at: str
    finished_at: str
    total_duration_ms: float
    league_key: str
    sport: SportCode
    season: int | None
    weeks: list[int]
    config_snapshot: dict[str, Any]
    request_stats: dict[str, Any] | None
    stages: list[StageDiagnostic]
    quality_checks: dict[str, Any]
    summary: str


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    league_key: str
    sport: SportCode
    frames: dict[str, pl.DataFrame]
    polars_outputs: dict[str, Path]
    iceberg_outputs: list[IcebergWriteResult]
    standardization_result: StandardizationResult | None = None
    uc_outputs: list[UCWriteResult] = field(default_factory=list)
    diagnostics: PipelineDiagnostics | None = None


def _build_client(oauth_session: OAuth2Session, config: PipelineConfig) -> YahooApiClient:
    return YahooApiClient(
        oauth_session=oauth_session,
        timeout_seconds=config.timeout_seconds,
        cache_dir=config.cache_dir,
        use_cache=config.use_cache,
        validate_contracts=config.validate_contracts,
        request_interval_seconds=config.request_interval_seconds,
        max_request_retries=config.max_request_retries,
        backoff_base_seconds=config.backoff_base_seconds,
        player_page_size=config.player_page_size,
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
        team_keys = sorted(
            {str(team.get("team_key") or "") for team in teams if team.get("team_key")}
        )
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
        if config.include_nfl_unrostered_player_stats:
            league_player_stats_weekly = client.get_player_stats_weekly_all_players(
                league_key,
                season=int(league.get("season") or 0),
                weeks=weeks,
            )
            player_stats_weekly = _merge_weekly_player_stats(
                base_rows=player_stats_weekly,
                additional_rows=league_player_stats_weekly,
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
    return (
        {},
        {
            "standings": standings,
            "standing_category_scores": [],
            "roster_entries": [],
            "player_projections": [],
        },
    )


def _merge_weekly_player_stats(
    base_rows: list[dict[str, Any]],
    additional_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_key: dict[tuple[str, int, str], dict[str, Any]] = {}

    for row in base_rows:
        key = (
            str(row.get("league_key") or ""),
            int(row.get("week") or 0),
            str(row.get("player_key") or ""),
        )
        rows_by_key[key] = row

    for row in additional_rows:
        key = (
            str(row.get("league_key") or ""),
            int(row.get("week") or 0),
            str(row.get("player_key") or ""),
        )
        existing = rows_by_key.get(key)
        if existing is None:
            rows_by_key[key] = row
            continue

        existing_points = float(existing.get("fantasy_points") or 0.0)
        row_points = float(row.get("fantasy_points") or 0.0)
        existing_has_stats = bool(existing.get("stats"))
        row_has_stats = bool(row.get("stats"))

        if (row_points != 0.0 and existing_points == 0.0) or (
            row_has_stats and not existing_has_stats
        ):
            merged = dict(existing)
            merged.update(row)
            rows_by_key[key] = merged

    rows = list(rows_by_key.values())
    rows.sort(key=lambda r: (int(r.get("week") or 0), str(r.get("player_key") or "")))
    return rows


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _entity_counts(entities: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return {key: len(value) for key, value in entities.items()}


def _frame_counts(frames: dict[str, pl.DataFrame]) -> dict[str, int]:
    return {key: int(frame.height) for key, frame in frames.items()}


def _config_snapshot(cfg: PipelineConfig) -> dict[str, Any]:
    return {
        "timeout_seconds": cfg.timeout_seconds,
        "use_cache": cfg.use_cache,
        "validate_contracts": cfg.validate_contracts,
        "request_interval_seconds": cfg.request_interval_seconds,
        "max_request_retries": cfg.max_request_retries,
        "backoff_base_seconds": cfg.backoff_base_seconds,
        "player_page_size": cfg.player_page_size,
        "require_nfl_player_points": cfg.require_nfl_player_points,
        "include_nfl_unrostered_player_stats": cfg.include_nfl_unrostered_player_stats,
        "start_week": cfg.start_week,
        "end_week": cfg.end_week,
        "storage_target": cfg.storage_target,
        "polars_file_format": cfg.polars_file_format,
        "iceberg_mode": cfg.iceberg_mode,
        "iceberg_dry_run": cfg.iceberg_dry_run,
        "materialized_views_enabled": cfg.materialized_views_enabled,
        "standardization_enabled": cfg.standardization_enabled,
        "include_non_target_sport_frames": cfg.include_non_target_sport_frames,
        "emit_stage_progress": cfg.diagnostics.emit_stage_progress,
    }


def _filter_frames_for_sport(
    frames: dict[str, pl.DataFrame],
    sport: SportCode,
    include_non_target_sport_frames: bool,
) -> dict[str, pl.DataFrame]:
    if include_non_target_sport_frames:
        return frames

    common_frame_keys = {
        "league",
        "team",
        "player",
        "draft_pick",
        "transaction",
        "stat_category",
        "scoring_rule",
    }
    sport_prefix = f"{sport}_"
    return {
        key: value
        for key, value in frames.items()
        if key in common_frame_keys
        or key.startswith(sport_prefix)
        or key.startswith("std_")
        or key.startswith("vw_")
        or key.startswith("v_")
    }


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

    diagnostics_cfg = cfg.diagnostics
    diagnostics_enabled = diagnostics_cfg.enabled
    started_at = _utc_now_iso()
    pipeline_start = time.perf_counter()
    stages: list[StageDiagnostic] = []
    quality_checks: dict[str, Any] = {}
    season: int | None = None
    weeks: list[int] = []

    def add_stage(
        stage_name: str,
        stage_start: float,
        status: Literal["ok", "warning", "error"] = "ok",
        entity_counts: dict[str, int] | None = None,
        frame_counts: dict[str, int] | None = None,
        warnings: list[str] | None = None,
        error: Exception | None = None,
    ) -> None:
        if not diagnostics_enabled:
            return
        duration_ms = round((time.perf_counter() - stage_start) * 1000.0, 2)
        stages.append(
            StageDiagnostic(
                stage_name=stage_name,
                status=status,
                duration_ms=duration_ms,
                entity_counts=entity_counts or {},
                frame_counts=frame_counts or {},
                warnings=tuple(warnings or []),
                error_type=type(error).__name__ if error is not None else None,
                error_message=str(error) if error is not None else None,
            )
        )
        if diagnostics_cfg.emit_stage_progress:
            warning_suffix = f" warnings={len(warnings or [])}" if warnings else ""
            error_suffix = f" error={type(error).__name__}: {error}" if error is not None else ""
            print(
                f"[pipeline] stage={stage_name} status={status} duration_ms={duration_ms}{warning_suffix}{error_suffix}"
            )

    def raise_with_stage_context(stage_name: str, exc: Exception) -> None:
        if hasattr(exc, "add_note"):
            exc.add_note(f"pipeline_stage={stage_name}")
        raise

    stage_start = time.perf_counter()
    try:
        client = api_client if api_client is not None else _build_client(oauth_session, cfg)
        add_stage("build_client", stage_start)
    except Exception as exc:
        add_stage("build_client", stage_start, status="error", error=exc)
        raise_with_stage_context("build_client", exc)

    stage_start = time.perf_counter()
    try:
        common_entities = _collect_common_entities(client, league_key)
        league_record = common_entities.get("league", [{}])[0]
        season = int(league_record.get("season") or 0)
        add_stage(
            "collect_common_entities", stage_start, entity_counts=_entity_counts(common_entities)
        )
    except Exception as exc:
        add_stage("collect_common_entities", stage_start, status="error", error=exc)
        raise_with_stage_context("collect_common_entities", exc)

    league_record = common_entities.get("league", [{}])[0]
    stage_start = time.perf_counter()
    try:
        nfl_entities, nba_entities = _collect_sport_entities(
            client,
            league_key,
            sport,
            league=league_record,
            teams=common_entities.get("team", []),
            config=cfg,
        )
        if sport == "nfl":
            weeks = _resolve_weeks(league_record, cfg)
            add_stage(
                "collect_sport_entities", stage_start, entity_counts=_entity_counts(nfl_entities)
            )
        else:
            add_stage(
                "collect_sport_entities", stage_start, entity_counts=_entity_counts(nba_entities)
            )
    except Exception as exc:
        add_stage("collect_sport_entities", stage_start, status="error", error=exc)
        raise_with_stage_context("collect_sport_entities", exc)

    stage_start = time.perf_counter()
    try:
        stage_warnings: list[str] = []
        if sport == "nfl":
            roster_entries = nfl_entities.get("roster_entries", [])
            player_stats_weekly = nfl_entities.get("player_stats_weekly", [])

            has_non_null_roster_points = any(
                row.get("points") is not None for row in roster_entries
            )
            has_non_zero_fantasy_points = any(
                float(row.get("fantasy_points") or 0.0) != 0.0 for row in player_stats_weekly
            )
            has_any_player_stats = any(bool(row.get("stats")) for row in player_stats_weekly)

            observed_weeks = sorted(
                {
                    int(row.get("week") or 0)
                    for row in roster_entries
                    if int(row.get("week") or 0) > 0
                }
            )
            missing_weeks = sorted(set(weeks) - set(observed_weeks)) if weeks else []

            quality_checks.update(
                {
                    "has_non_null_roster_points": has_non_null_roster_points,
                    "has_non_zero_fantasy_points": has_non_zero_fantasy_points,
                    "has_any_player_stats": has_any_player_stats,
                    "expected_weeks": weeks,
                    "observed_roster_weeks": observed_weeks,
                    "missing_roster_weeks": missing_weeks,
                }
            )

            if diagnostics_cfg.emit_warnings:
                if not has_non_null_roster_points:
                    stage_warnings.append("Roster entries contain no non-null points values.")
                if not has_non_zero_fantasy_points:
                    stage_warnings.append(
                        "Weekly player stats contain no non-zero fantasy_points values."
                    )
                if not has_any_player_stats:
                    stage_warnings.append("Weekly player stats contain no detailed stat lines.")
                if missing_weeks:
                    stage_warnings.append(
                        f"Roster data is missing expected weeks: {missing_weeks}."
                    )

            if (
                cfg.require_nfl_player_points
                and not has_non_null_roster_points
                and not has_non_zero_fantasy_points
                and not has_any_player_stats
            ):
                raise ValueError(
                    "NFL player-level scoring data is unavailable (roster points and player stats are empty). "
                    "Rerun with use_cache=False or refresh cache/API permissions before persisting."
                )

        stage_status: Literal["ok", "warning", "error"] = "warning" if stage_warnings else "ok"
        add_stage("nfl_scoring_guard", stage_start, status=stage_status, warnings=stage_warnings)
    except Exception as exc:
        add_stage("nfl_scoring_guard", stage_start, status="error", error=exc)
        raise_with_stage_context("nfl_scoring_guard", exc)

    stage_start = time.perf_counter()
    try:
        frames = transform(
            common_entities=common_entities, nfl_entities=nfl_entities, nba_entities=nba_entities
        )
        add_stage(
            "transform",
            stage_start,
            frame_counts=_frame_counts(frames) if diagnostics_cfg.capture_frame_summaries else None,
        )
    except Exception as exc:
        add_stage("transform", stage_start, status="error", error=exc)
        raise_with_stage_context("transform", exc)

    stage_start = time.perf_counter()
    try:
        frames = _filter_frames_for_sport(
            frames,
            sport=sport,
            include_non_target_sport_frames=cfg.include_non_target_sport_frames,
        )
        add_stage(
            "filter_sport_frames",
            stage_start,
            frame_counts=_frame_counts(frames) if diagnostics_cfg.capture_frame_summaries else None,
        )
    except Exception as exc:
        add_stage("filter_sport_frames", stage_start, status="error", error=exc)
        raise_with_stage_context("filter_sport_frames", exc)

    standardization_result: StandardizationResult | None = None
    if cfg.standardization_enabled:
        stage_start = time.perf_counter()
        try:
            standardizer = EntityStandardizer(
                config=cfg.standardization_config or StandardizationConfig()
            )
            std_records = [
                {
                    "source_system": "yahoo",
                    "source_entity_id": str(team.get("team_key") or ""),
                    "raw_player_name": "",
                    "raw_team_name": str(team.get("team_name") or ""),
                    "raw_position": "",
                    "season": common_entities["league"][0]["season"]
                    if common_entities.get("league")
                    else 0,
                }
                for team in common_entities.get("team", [])
            ]
            standardization_result = standardizer.standardize_batch(std_records)
            frames.update(
                {
                    key: value
                    for key, value in standardization_result.tables.items()
                    if key
                    in {
                        "std_standardized_outputs",
                        "std_match_queue",
                        "std_rescued_records",
                        "std_source_to_canonical_map",
                    }
                }
            )
            add_stage(
                "standardization",
                stage_start,
                frame_counts=_frame_counts(frames)
                if diagnostics_cfg.capture_frame_summaries
                else None,
            )
        except Exception as exc:
            add_stage("standardization", stage_start, status="error", error=exc)
            raise_with_stage_context("standardization", exc)

    if cfg.materialized_views_enabled:
        stage_start = time.perf_counter()
        try:
            frames.update(build_materialized_views(frames, requested_views=cfg.materialized_views))
            add_stage(
                "materialized_views",
                stage_start,
                frame_counts=_frame_counts(frames)
                if diagnostics_cfg.capture_frame_summaries
                else None,
            )
        except Exception as exc:
            add_stage("materialized_views", stage_start, status="error", error=exc)
            raise_with_stage_context("materialized_views", exc)

    polars_outputs: dict[str, Path] = {}
    iceberg_outputs: list[IcebergWriteResult] = []

    if cfg.storage_target in {"polars", "both"}:
        stage_start = time.perf_counter()
        try:
            polars_outputs = persist_with_polars(
                frames, output_dir=cfg.polars_output_dir, file_format=cfg.polars_file_format
            )
            add_stage("persist_polars", stage_start)
        except Exception as exc:
            add_stage("persist_polars", stage_start, status="error", error=exc)
            raise_with_stage_context("persist_polars", exc)

    if cfg.storage_target in {"iceberg", "both"}:
        stage_start = time.perf_counter()
        try:
            iceberg_outputs = persist_to_iceberg(
                frames=frames,
                catalog_config=cfg.iceberg_catalog,
                namespace_config=cfg.iceberg_namespaces,
                default_mode=cfg.iceberg_mode,
                idempotency_store_path=cfg.iceberg_idempotency_store,
                dry_run=cfg.iceberg_dry_run,
            )
            add_stage("persist_iceberg", stage_start)
        except Exception as exc:
            add_stage("persist_iceberg", stage_start, status="error", error=exc)
            raise_with_stage_context("persist_iceberg", exc)

    finished_at = _utc_now_iso()
    total_duration_ms = round((time.perf_counter() - pipeline_start) * 1000.0, 2)
    request_stats: dict[str, Any] | None = None
    if diagnostics_enabled and diagnostics_cfg.capture_request_stats:
        getter = getattr(client, "get_request_stats", None)
        if callable(getter):
            request_stats = getter()

    diagnostics: PipelineDiagnostics | None = None
    if diagnostics_enabled:
        warning_count = sum(len(stage.warnings) for stage in stages)
        summary = (
            f"Pipeline completed with {len(stages)} stages in {total_duration_ms} ms"
            f" ({warning_count} warning{'s' if warning_count != 1 else ''})."
        )
        diagnostics = PipelineDiagnostics(
            started_at=started_at,
            finished_at=finished_at,
            total_duration_ms=total_duration_ms,
            league_key=league_key,
            sport=sport,
            season=season,
            weeks=weeks,
            config_snapshot=_config_snapshot(cfg),
            request_stats=request_stats,
            stages=stages,
            quality_checks=quality_checks,
            summary=summary,
        )

    return PipelineRunResult(
        league_key=league_key,
        sport=sport,
        frames=frames,
        polars_outputs=polars_outputs,
        iceberg_outputs=iceberg_outputs,
        standardization_result=standardization_result,
        diagnostics=diagnostics,
    )
