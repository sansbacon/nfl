"""Polars-first transformation pipeline interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import polars as pl

from nfl.yahoo_fantasy.validation import (
    ContractValidationError,
    get_contract,
    validate,
    validate_polars_frame,
)


class TransformValidationError(ValueError):
    """Raised when transformation outputs fail quality checks."""


@dataclass(frozen=True, slots=True)
class TransformResult:
    frames: dict[str, pl.DataFrame]


_INT_COLUMNS = {
    "game_id", "season", "num_teams", "team_id", "draft_position", "pick_number", "round_number",
    "cost", "rank", "wins", "losses", "ties", "week", "bye_week", "category_rank",
}
_FLOAT_COLUMNS = {
    "points_for", "points_against", "fantasy_points", "points", "opponent_points", "projected_points", "category_value",
    "points_per_unit", "bonus_target", "bonus_points",
}
_BOOL_COLUMNS = {"is_playoff", "is_consolation", "is_starting"}


def _empty_frame_for_contract(required: tuple[str, ...], optional: tuple[str, ...]) -> pl.DataFrame:
    return pl.DataFrame({col: [] for col in list(required + optional)})


def _coerce_frame_types(frame: pl.DataFrame) -> pl.DataFrame:
    casts: list[pl.Expr] = []
    for col in frame.columns:
        if col in _INT_COLUMNS:
            casts.append(pl.col(col).cast(pl.Int64, strict=False))
        elif col in _FLOAT_COLUMNS:
            casts.append(pl.col(col).cast(pl.Float64, strict=False))
        elif col in _BOOL_COLUMNS:
            casts.append(pl.col(col).cast(pl.Boolean, strict=False))
    return frame.with_columns(casts) if casts else frame


def _sorted_by_primary_key(frame: pl.DataFrame, primary_key: tuple[str, ...]) -> pl.DataFrame:
    keys = [k for k in primary_key if k in frame.columns]
    return frame.sort(keys) if keys else frame


def transform_entity(
    records: Iterable[Mapping[str, Any]],
    entity: str,
    sport: str | None = None,
    keep_extra_fields: bool = False,
) -> pl.DataFrame:
    contract = get_contract(entity=entity, sport=sport)  # type: ignore[arg-type]
    records_list = list(records)
    try:
        validate(records_list, entity=entity, sport=sport)  # type: ignore[arg-type]
    except ContractValidationError as exc:
        raise TransformValidationError(str(exc)) from exc

    if not records_list:
        return _coerce_frame_types(_empty_frame_for_contract(contract.required, contract.optional))

    if keep_extra_fields:
        frame = pl.DataFrame(records_list)
    else:
        allowed = list(contract.required + contract.optional)
        normalized = [{field: row.get(field) for field in allowed} for row in records_list]
        frame = pl.DataFrame(normalized)

    frame = _coerce_frame_types(frame)
    try:
        validate_polars_frame(frame, contract, allow_extra_fields=keep_extra_fields)
    except ContractValidationError as exc:
        raise TransformValidationError(str(exc)) from exc

    return _sorted_by_primary_key(frame, contract.primary_key)


def transform_nfl(
    standings: Iterable[Mapping[str, Any]] | None = None,
    matchups: Iterable[Mapping[str, Any]] | None = None,
    roster_entries: Iterable[Mapping[str, Any]] | None = None,
    player_stats_weekly: Iterable[Mapping[str, Any]] | None = None,
) -> TransformResult:
    return TransformResult(
        frames={
            "standings": transform_entity(standings or [], entity="standings", sport="nfl"),
            "matchups": transform_entity(matchups or [], entity="matchups", sport="nfl"),
            "roster_entries": transform_entity(roster_entries or [], entity="roster_entries", sport="nfl"),
            "player_stats_weekly": transform_entity(player_stats_weekly or [], entity="player_stats_weekly", sport="nfl"),
        }
    )


def transform_nba(
    standings: Iterable[Mapping[str, Any]] | None = None,
    standing_category_scores: Iterable[Mapping[str, Any]] | None = None,
    roster_entries: Iterable[Mapping[str, Any]] | None = None,
    player_projections: Iterable[Mapping[str, Any]] | None = None,
) -> TransformResult:
    return TransformResult(
        frames={
            "standings": transform_entity(standings or [], entity="standings", sport="nba"),
            "standing_category_scores": transform_entity(standing_category_scores or [], entity="standing_category_scores", sport="nba"),
            "roster_entries": transform_entity(roster_entries or [], entity="roster_entries", sport="nba"),
            "player_projections": transform_entity(player_projections or [], entity="player_projections", sport="nba"),
        }
    )


def transform(
    common_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    nfl_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    nba_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, pl.DataFrame]:
    common_entities = common_entities or {}
    nfl_entities = nfl_entities or {}
    nba_entities = nba_entities or {}

    common_frames = {
        "league": transform_entity(common_entities.get("league", []), entity="league"),
        "team": transform_entity(common_entities.get("team", []), entity="team"),
        "player": transform_entity(common_entities.get("player", []), entity="player"),
        "draft_pick": transform_entity(common_entities.get("draft_pick", []), entity="draft_pick"),
        "transaction": transform_entity(common_entities.get("transaction", []), entity="transaction"),
        "stat_category": transform_entity(common_entities.get("stat_category", []), entity="stat_category"),
        "scoring_rule": transform_entity(common_entities.get("scoring_rule", []), entity="scoring_rule"),
    }

    nfl = transform_nfl(
        standings=nfl_entities.get("standings", []),
        matchups=nfl_entities.get("matchups", []),
        roster_entries=nfl_entities.get("roster_entries", []),
        player_stats_weekly=nfl_entities.get("player_stats_weekly", []),
    )
    nba = transform_nba(
        standings=nba_entities.get("standings", []),
        standing_category_scores=nba_entities.get("standing_category_scores", []),
        roster_entries=nba_entities.get("roster_entries", []),
        player_projections=nba_entities.get("player_projections", []),
    )

    return {
        **common_frames,
        **{f"nfl_{name}": frame for name, frame in nfl.frames.items()},
        **{f"nba_{name}": frame for name, frame in nba.frames.items()},
    }
