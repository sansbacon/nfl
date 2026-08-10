"""Ibis-based ESPN data transformation utilities.

Thin wrapper around the existing row-level transforms that converts
the output to ``ibis.Table`` expressions. The dataclass-to-dict
conversion stays in Python (extraction boundary); Ibis takes over
at the DataFrame layer.

Requires: pip install nfl[ibis]
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import ibis

from nfl.espn_fantasy.api import EspnPlayer
from nfl.espn_fantasy.transforms import (
    players_to_ranks_rows,
    players_to_season_projection_rows,
    players_to_weekly_projection_rows,
)

if TYPE_CHECKING:
    pass

# Type coercion sets for ESPN entities
_RANKS_INT_COLUMNS = {"espn_id", "rank_ppr", "rank_standard", "season"}
_RANKS_FLOAT_COLUMNS = {
    "auction_value_ppr",
    "auction_value_standard",
    "percent_owned",
    "percent_started",
}
_RANKS_BOOL_COLUMNS = {"is_current"}

_PROJ_INT_COLUMNS = {"espn_id", "season", "week"}
_PROJ_FLOAT_COLUMNS = {"projected_total"}
_PROJ_BOOL_COLUMNS = {"is_current"}


def _coerce_types(
    table: ibis.Table,
    int_cols: set[str],
    float_cols: set[str],
    bool_cols: set[str],
) -> ibis.Table:
    """Cast columns to expected types."""
    casts: dict[str, ibis.Expr] = {}
    for col in table.columns:
        if col in int_cols:
            casts[col] = table[col].try_cast("int64")
        elif col in float_cols:
            casts[col] = table[col].try_cast("float64")
        elif col in bool_cols:
            casts[col] = table[col].try_cast("boolean")
    return table.mutate(**casts) if casts else table


def players_to_ranks_table(
    players: list[EspnPlayer],
    season: int,
    ingestion_date: date | None = None,
) -> ibis.Table:
    """Convert ESPN players into an Ibis fact_espn_ranks table.

    Parameters
    ----------
    players : list[EspnPlayer]
        ESPN players with ranking data.
    season : int
        NFL season year.
    ingestion_date : date | None
        Effective date for SCD2 tracking.

    Returns
    -------
    ibis.Table
        Typed Ibis table with PPR/Standard ranks and ownership.
    """
    rows = players_to_ranks_rows(players, season=season, ingestion_date=ingestion_date)
    if not rows:
        return ibis.memtable(
            {"espn_id": [], "player": [], "position": [], "season": []}
        )
    table = ibis.memtable(rows)
    return _coerce_types(table, _RANKS_INT_COLUMNS, _RANKS_FLOAT_COLUMNS, _RANKS_BOOL_COLUMNS)


def players_to_season_projection_table(
    players: list[EspnPlayer],
    season: int,
    ingestion_date: date | None = None,
) -> ibis.Table:
    """Convert ESPN players into an Ibis fact_espn_projections table.

    Parameters
    ----------
    players : list[EspnPlayer]
        ESPN players with season projections.
    season : int
        NFL season year.
    ingestion_date : date | None
        Effective date for SCD2 tracking.

    Returns
    -------
    ibis.Table
        Typed Ibis table with full-season stat projections.
    """
    rows = players_to_season_projection_rows(
        players, season=season, ingestion_date=ingestion_date
    )
    if not rows:
        return ibis.memtable(
            {"espn_id": [], "player": [], "position": [], "season": []}
        )
    table = ibis.memtable(rows)
    return _coerce_types(table, _PROJ_INT_COLUMNS, _PROJ_FLOAT_COLUMNS, _PROJ_BOOL_COLUMNS)


def players_to_weekly_projection_table(
    players: list[EspnPlayer],
    season: int,
    ingestion_date: date | None = None,
) -> ibis.Table:
    """Convert ESPN players into an Ibis fact_espn_weekly_projections table.

    Parameters
    ----------
    players : list[EspnPlayer]
        ESPN players with weekly projections.
    season : int
        NFL season year.
    ingestion_date : date | None
        Effective date for SCD2 tracking.

    Returns
    -------
    ibis.Table
        Typed Ibis table with per-week stat projections.
    """
    rows = players_to_weekly_projection_rows(
        players, season=season, ingestion_date=ingestion_date
    )
    if not rows:
        return ibis.memtable(
            {"espn_id": [], "player": [], "position": [], "season": [], "week": []}
        )
    table = ibis.memtable(rows)
    return _coerce_types(table, _PROJ_INT_COLUMNS, _PROJ_FLOAT_COLUMNS, _PROJ_BOOL_COLUMNS)
