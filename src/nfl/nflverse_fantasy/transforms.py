"""Polars transforms for NFLverse wrapper records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import polars as pl

from nfl.nflverse_fantasy.validation import ContractValidationError, get_contract, validate, validate_polars_frame


class TransformValidationError(ValueError):
    """Raised when transform output fails validation."""


@dataclass(frozen=True, slots=True)
class TransformResult:
    frames: dict[str, pl.DataFrame]


DATASET_COERCIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "pbp": {
        "int": ("season", "week", "qtr", "down", "yardline_100", "yards_gained", "drive"),
        "float": ("epa", "wp", "wpa", "air_yards", "yards_after_catch"),
        "bool": ("shotgun", "no_huddle", "qb_dropback", "rush_attempt", "pass_attempt", "two_point_attempt"),
        "date": ("game_date",),
        "datetime": (),
    },
    "player_stats": {
        "int": ("season", "week", "completions", "attempts", "carries", "receptions", "targets"),
        "float": ("passing_yards", "rushing_yards", "receiving_yards", "fantasy_points_ppr"),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "team_stats": {
        "int": ("season", "week", "games", "wins", "losses", "ties"),
        "float": ("points_for", "points_against", "epa_offense", "epa_defense"),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "schedules": {
        "int": ("season", "week", "home_score", "away_score"),
        "float": (),
        "bool": ("div_game", "overtime"),
        "date": ("gameday", "game_date"),
        "datetime": ("gametime",),
    },
    "players": {
        "int": ("entry_year", "rookie_year", "height", "weight"),
        "float": (),
        "bool": ("active",),
        "date": ("birth_date",),
        "datetime": (),
    },
    "rosters": {
        "int": ("season",),
        "float": (),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "rosters_weekly": {
        "int": ("season", "week"),
        "float": (),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "snap_counts": {
        "int": ("season", "week", "offense_snaps", "defense_snaps", "special_teams_snaps"),
        "float": ("offense_pct", "defense_pct", "special_teams_pct"),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "nextgen_stats": {
        "int": ("season", "week"),
        "float": ("avg_time_to_throw", "avg_air_yards_to_sticks", "completion_percentage_above_expectation"),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "ftn_charting": {
        "int": ("season", "week"),
        "float": ("yac_over_expected", "air_yards_share", "target_share"),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "participation": {
        "int": ("season", "week", "offense_snaps", "defense_snaps", "special_teams_snaps"),
        "float": ("offense_pct", "defense_pct", "special_teams_pct"),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "draft_picks": {
        "int": ("season", "round", "pick", "overall"),
        "float": (),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "injuries": {
        "int": ("season", "week"),
        "float": (),
        "bool": ("did_not_practice", "questionable", "doubtful", "out"),
        "date": ("report_date",),
        "datetime": (),
    },
    "contracts": {
        "int": ("year_signed", "year_expire", "years", "total_value", "guaranteed"),
        "float": (),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "officials": {
        "int": ("season", "week"),
        "float": (),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "combine": {
        "int": ("year", "height", "weight", "bench"),
        "float": ("forty", "vertical", "broad_jump", "cone"),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "depth_charts": {
        "int": ("season", "week", "depth_team"),
        "float": (),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "trades": {
        "int": ("season",),
        "float": (),
        "bool": (),
        "date": ("trade_date",),
        "datetime": (),
    },
    "ff_playerids": {
        "int": (),
        "float": (),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "ff_rankings": {
        "int": ("season", "week", "rank", "pos_rank", "tier"),
        "float": ("points",),
        "bool": (),
        "date": (),
        "datetime": (),
    },
    "ff_opportunity": {
        "int": ("season", "week", "carries", "targets"),
        "float": ("xfp", "ra_xfp", "re_xfp"),
        "bool": (),
        "date": (),
        "datetime": (),
    },
}

_TRUE_STRINGS = {"1", "true", "t", "yes", "y"}
_FALSE_STRINGS = {"0", "false", "f", "no", "n"}


def _empty_frame_for_contract(required: tuple[str, ...], optional: tuple[str, ...]) -> pl.DataFrame:
    return pl.DataFrame({col: [] for col in required + optional})


def _coerce_boolean_expr(column: str) -> pl.Expr:
    normalized = pl.col(column).cast(pl.Utf8, strict=False).str.strip_chars().str.to_lowercase()
    return (
        pl.when(pl.col(column).is_null())
        .then(None)
        .when(normalized.is_in(_TRUE_STRINGS))
        .then(True)
        .when(normalized.is_in(_FALSE_STRINGS))
        .then(False)
        .otherwise(None)
        .alias(column)
    )


def _coerce_frame(entity: str, frame: pl.DataFrame) -> pl.DataFrame:
    rules = DATASET_COERCIONS.get(entity, {})
    int_cols = [c for c in rules.get("int", ()) if c in frame.columns]
    float_cols = [c for c in rules.get("float", ()) if c in frame.columns]
    bool_cols = [c for c in rules.get("bool", ()) if c in frame.columns]
    date_cols = [c for c in rules.get("date", ()) if c in frame.columns]
    datetime_cols = [c for c in rules.get("datetime", ()) if c in frame.columns]

    exprs: list[pl.Expr] = []
    exprs.extend(pl.col(c).cast(pl.Int64, strict=False).alias(c) for c in int_cols)
    exprs.extend(pl.col(c).cast(pl.Float64, strict=False).alias(c) for c in float_cols)
    exprs.extend(_coerce_boolean_expr(c) for c in bool_cols)
    exprs.extend(pl.col(c).str.strptime(pl.Date, strict=False).alias(c) for c in date_cols)
    exprs.extend(pl.col(c).str.to_datetime(time_zone="UTC", strict=False).alias(c) for c in datetime_cols)

    if "_loaded_at" in frame.columns:
        exprs.append(pl.col("_loaded_at").str.to_datetime(time_zone="UTC", strict=False).alias("_loaded_at"))

    if exprs:
        frame = frame.with_columns(exprs)
    return frame


def transform_entity(
    records: Iterable[Mapping[str, Any]],
    entity: str,
    keep_extra_fields: bool = True,
) -> pl.DataFrame:
    contract = get_contract(entity)
    rows = list(records)
    try:
        validate(rows, entity)
    except ContractValidationError as exc:
        raise TransformValidationError(str(exc)) from exc

    if not rows:
        return _empty_frame_for_contract(contract.required, contract.optional)

    if keep_extra_fields:
        frame = pl.DataFrame(rows)
    else:
        allowed = list(contract.required + contract.optional)
        frame = pl.DataFrame([{field: row.get(field) for field in allowed} for row in rows])

    frame = _coerce_frame(entity, frame)

    try:
        validate_polars_frame(frame, contract)
    except ContractValidationError as exc:
        raise TransformValidationError(str(exc)) from exc

    return frame.sort([k for k in contract.primary_key if k in frame.columns])


def transform(
    entities: Mapping[str, Iterable[Mapping[str, Any]]],
) -> dict[str, pl.DataFrame]:
    return {
        f"nvnfl_{entity}": transform_entity(records, entity=entity)
        for entity, records in entities.items()
    }
