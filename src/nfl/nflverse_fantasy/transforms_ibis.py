"""Ibis-based transforms for NFLverse wrapper records.

Drop-in replacement for ``transforms.py`` that produces ``ibis.Table``
expressions instead of ``pl.DataFrame`` objects.

Key difference from simpler source modules: NFLverse uses a data-driven
``DATASET_COERCIONS`` dict (16 entity types) with date, datetime, and
string-to-boolean coercion in addition to int/float.

Requires: pip install nfl[ibis]
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import ibis
import pyarrow as pa

from nfl.common.validation import (
    ContractValidationError,
    EntityContract,
    validate_ibis_table,
)
from nfl.nflverse_fantasy.validation import (
    get_contract,
    validate,
)

if TYPE_CHECKING:
    pass


class TransformValidationError(ValueError):
    """Raised when transform output fails validation."""


@dataclass(frozen=True, slots=True)
class IbisTransformResult:
    """Transform result holding Ibis table expressions."""

    tables: dict[str, ibis.Table]


# Data-driven coercion rules per dataset (same as Polars version)
DATASET_COERCIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "pbp": {
        "int": ("season", "week", "qtr", "down", "yardline_100", "yards_gained", "drive"),
        "float": ("epa", "wp", "wpa", "air_yards", "yards_after_catch"),
        "bool": (
            "shotgun",
            "no_huddle",
            "qb_dropback",
            "rush_attempt",
            "pass_attempt",
            "two_point_attempt",
        ),
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
        "float": (
            "avg_time_to_throw",
            "avg_air_yards_to_sticks",
            "completion_percentage_above_expectation",
        ),
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


def _empty_table_for_contract(
    required: tuple[str, ...], optional: tuple[str, ...]
) -> ibis.Table:
    """Create an empty Ibis table matching the contract schema."""
    cols = list(required + optional)
    return ibis.memtable(pa.table({col: pa.array([], type=pa.string()) for col in cols}))


def _coerce_boolean_ibis(table: ibis.Table, column: str) -> ibis.Expr:
    """Coerce a string column to boolean using truthy/falsy string matching.

    Handles: '1'/'true'/'t'/'yes'/'y' -> True,
             '0'/'false'/'f'/'no'/'n' -> False,
             null/other -> null.
    """
    normalized = table[column].cast("string").strip().lower()
    return ibis.cases(
        (table[column].isnull(), ibis.null()),
        (normalized.isin(_TRUE_STRINGS), ibis.literal(True)),
        (normalized.isin(_FALSE_STRINGS), ibis.literal(False)),
        else_=ibis.null(),
    )


def _coerce_table(entity: str, table: ibis.Table) -> ibis.Table:
    """Apply dataset-specific type coercions to an Ibis table.

    Uses the ``DATASET_COERCIONS`` registry to cast columns by entity name.
    Handles int, float, bool (from string), date, and datetime types.
    """
    rules = DATASET_COERCIONS.get(entity, {})
    int_cols = [c for c in rules.get("int", ()) if c in table.columns]
    float_cols = [c for c in rules.get("float", ()) if c in table.columns]
    bool_cols = [c for c in rules.get("bool", ()) if c in table.columns]
    date_cols = [c for c in rules.get("date", ()) if c in table.columns]
    datetime_cols = [c for c in rules.get("datetime", ()) if c in table.columns]

    casts: dict[str, ibis.Expr] = {}

    for col in int_cols:
        casts[col] = table[col].try_cast("int64")
    for col in float_cols:
        casts[col] = table[col].try_cast("float64")
    for col in bool_cols:
        casts[col] = _coerce_boolean_ibis(table, col)
    for col in date_cols:
        casts[col] = table[col].try_cast("date")
    for col in datetime_cols:
        casts[col] = table[col].try_cast("timestamp")

    # Special: _loaded_at column
    if "_loaded_at" in table.columns:
        casts["_loaded_at"] = table["_loaded_at"].try_cast("timestamp")

    return table.mutate(**casts) if casts else table


def transform_entity(
    records: Iterable[Mapping[str, Any]],
    entity: str,
    keep_extra_fields: bool = True,
) -> ibis.Table:
    """Transform raw NFLverse records into a typed, validated Ibis table.

    Parameters
    ----------
    records : Iterable[Mapping[str, Any]]
        Raw records from nflreadpy or other NFLverse source.
    entity : str
        Dataset/entity name (e.g. "pbp", "player_stats", "schedules").
    keep_extra_fields : bool
        If True (default), retains fields not in the contract.
        NFLverse datasets commonly have many extra columns.

    Returns
    -------
    ibis.Table
        Typed and validated Ibis table expression.
    """
    contract = get_contract(entity)
    rows = list(records)

    try:
        validate(rows, entity)
    except ContractValidationError as exc:
        raise TransformValidationError(str(exc)) from exc

    if not rows:
        return _empty_table_for_contract(contract.required, contract.optional)

    if keep_extra_fields:
        data = rows
    else:
        allowed = list(contract.required + contract.optional)
        data = [{field: row.get(field) for field in allowed} for row in rows]

    # Convert to Ibis via memtable
    table = ibis.memtable(data)

    # Apply dataset-specific coercions
    table = _coerce_table(entity, table)

    # Validate schema
    ibis_contract = EntityContract(
        name=contract.name,
        required=contract.required,
        optional=contract.optional,
        primary_key=contract.primary_key,
    )
    try:
        validate_ibis_table(table, ibis_contract, allow_extra_columns=keep_extra_fields)
    except ContractValidationError as exc:
        raise TransformValidationError(str(exc)) from exc

    # Sort by primary key
    sort_keys = [k for k in contract.primary_key if k in table.columns]
    return table.order_by(sort_keys) if sort_keys else table


def transform(
    entities: Mapping[str, Iterable[Mapping[str, Any]]],
) -> dict[str, ibis.Table]:
    """Transform all NFLverse entities into Ibis tables.

    Parameters
    ----------
    entities : Mapping[str, Iterable[Mapping[str, Any]]]
        Entity name to records mapping.

    Returns
    -------
    dict[str, ibis.Table]
        Prefixed entity name to Ibis table mapping.
    """
    return {
        f"nvnfl_{entity}": transform_entity(records, entity=entity)
        for entity, records in entities.items()
    }
