"""Ibis-based transformation pipeline interfaces for Yahoo Fantasy.

Drop-in replacement for ``transforms.py`` that produces ``ibis.Table``
expressions instead of ``pl.DataFrame`` objects. Supports NFL and NBA
sport scopes.

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
from nfl.yahoo_fantasy.validation import (
    get_contract,
    validate,
)

if TYPE_CHECKING:
    pass


class TransformValidationError(ValueError):
    """Raised when transformation outputs fail quality checks."""


@dataclass(frozen=True, slots=True)
class IbisTransformResult:
    """Transform result holding Ibis table expressions."""

    tables: dict[str, ibis.Table]


# Column type sets (same as the Polars version)
_INT_COLUMNS = {
    "game_id",
    "season",
    "num_teams",
    "team_id",
    "draft_position",
    "pick_number",
    "round_number",
    "cost",
    "rank",
    "wins",
    "losses",
    "ties",
    "week",
    "bye_week",
    "category_rank",
}
_FLOAT_COLUMNS = {
    "points_for",
    "points_against",
    "fantasy_points",
    "points",
    "opponent_points",
    "projected_points",
    "category_value",
    "points_per_unit",
    "bonus_target",
    "bonus_points",
}
_BOOL_COLUMNS = {"is_playoff", "is_consolation", "is_starting"}


def _empty_table_for_contract(
    required: tuple[str, ...], optional: tuple[str, ...]
) -> ibis.Table:
    """Create an empty Ibis table matching the contract schema."""
    cols = list(required + optional)
    return ibis.memtable(pa.table({col: pa.array([], type=pa.string()) for col in cols}))


def _coerce_types(table: ibis.Table) -> ibis.Table:
    """Cast columns to their expected types based on column name sets."""
    casts: dict[str, ibis.Expr] = {}
    for col in table.columns:
        if col in _INT_COLUMNS:
            casts[col] = table[col].try_cast("int64")
        elif col in _FLOAT_COLUMNS:
            casts[col] = table[col].try_cast("float64")
        elif col in _BOOL_COLUMNS:
            casts[col] = table[col].try_cast("boolean")
    return table.mutate(**casts) if casts else table


def _sorted_by_primary_key(
    table: ibis.Table, primary_key: tuple[str, ...]
) -> ibis.Table:
    """Order the table by primary key columns present in the schema."""
    keys = [k for k in primary_key if k in table.columns]
    return table.order_by(keys) if keys else table


def transform_entity(
    records: Iterable[Mapping[str, Any]],
    entity: str,
    sport: str | None = None,
    keep_extra_fields: bool = False,
) -> ibis.Table:
    """Transform raw records into a typed, validated Ibis table.

    Parameters
    ----------
    records : Iterable[Mapping[str, Any]]
        Raw records from extraction.
    entity : str
        Entity name (e.g. "league", "team", "player").
    sport : str | None
        Sport code for sport-scoped contracts ("nfl" or "nba").
    keep_extra_fields : bool
        If True, retains fields not in the contract.

    Returns
    -------
    ibis.Table
        Typed and validated Ibis table expression.
    """
    contract = get_contract(entity=entity, sport=sport)  # type: ignore[arg-type]
    records_list = list(records)

    # Validate raw records (reuse existing validation logic)
    try:
        validate(records_list, entity=entity, sport=sport)  # type: ignore[arg-type]
    except Exception as exc:
        raise TransformValidationError(str(exc)) from exc

    if not records_list:
        return _coerce_types(
            _empty_table_for_contract(contract.required, contract.optional)
        )

    # Build the record set
    if keep_extra_fields:
        data = records_list
    else:
        allowed = list(contract.required + contract.optional)
        data = [{field: row.get(field) for field in allowed} for row in records_list]

    # Convert to Ibis via memtable
    table = ibis.memtable(data)

    # Coerce types
    table = _coerce_types(table)

    # Validate schema using the common validator
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

    return _sorted_by_primary_key(table, contract.primary_key)


def transform_nfl(
    standings: Iterable[Mapping[str, Any]] | None = None,
    matchups: Iterable[Mapping[str, Any]] | None = None,
    roster_entries: Iterable[Mapping[str, Any]] | None = None,
    player_stats_weekly: Iterable[Mapping[str, Any]] | None = None,
) -> IbisTransformResult:
    """Transform NFL-scoped Yahoo Fantasy entities."""
    return IbisTransformResult(
        tables={
            "standings": transform_entity(standings or [], entity="standings", sport="nfl"),
            "matchups": transform_entity(matchups or [], entity="matchups", sport="nfl"),
            "roster_entries": transform_entity(
                roster_entries or [], entity="roster_entries", sport="nfl"
            ),
            "player_stats_weekly": transform_entity(
                player_stats_weekly or [], entity="player_stats_weekly", sport="nfl"
            ),
        }
    )


def transform_nba(
    standings: Iterable[Mapping[str, Any]] | None = None,
    standing_category_scores: Iterable[Mapping[str, Any]] | None = None,
    roster_entries: Iterable[Mapping[str, Any]] | None = None,
    player_projections: Iterable[Mapping[str, Any]] | None = None,
) -> IbisTransformResult:
    """Transform NBA-scoped Yahoo Fantasy entities."""
    return IbisTransformResult(
        tables={
            "standings": transform_entity(standings or [], entity="standings", sport="nba"),
            "standing_category_scores": transform_entity(
                standing_category_scores or [], entity="standing_category_scores", sport="nba"
            ),
            "roster_entries": transform_entity(
                roster_entries or [], entity="roster_entries", sport="nba"
            ),
            "player_projections": transform_entity(
                player_projections or [], entity="player_projections", sport="nba"
            ),
        }
    )


def transform(
    common_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    nfl_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    nba_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, ibis.Table]:
    """Transform all Yahoo Fantasy entities into Ibis tables.

    Parameters
    ----------
    common_entities : Mapping | None
        Sport-agnostic entities (league, team, player, etc.).
    nfl_entities : Mapping | None
        NFL-scoped entities (standings, matchups, etc.).
    nba_entities : Mapping | None
        NBA-scoped entities (standings, category_scores, etc.).

    Returns
    -------
    dict[str, ibis.Table]
        Entity name to Ibis table mapping.
    """
    common_entities = common_entities or {}
    nfl_entities = nfl_entities or {}
    nba_entities = nba_entities or {}

    common_tables = {
        "league": transform_entity(common_entities.get("league", []), entity="league"),
        "team": transform_entity(common_entities.get("team", []), entity="team"),
        "player": transform_entity(common_entities.get("player", []), entity="player"),
        "draft_pick": transform_entity(
            common_entities.get("draft_pick", []), entity="draft_pick"
        ),
        "transaction": transform_entity(
            common_entities.get("transaction", []), entity="transaction"
        ),
        "stat_category": transform_entity(
            common_entities.get("stat_category", []), entity="stat_category"
        ),
        "scoring_rule": transform_entity(
            common_entities.get("scoring_rule", []), entity="scoring_rule"
        ),
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
        **common_tables,
        **{f"nfl_{name}": table for name, table in nfl.tables.items()},
        **{f"nba_{name}": table for name, table in nba.tables.items()},
    }
