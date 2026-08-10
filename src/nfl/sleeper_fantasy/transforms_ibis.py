"""Ibis-based Sleeper data transformation utilities.

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

from nfl.sleeper_fantasy.api import SleeperPlayer
from nfl.sleeper_fantasy.transforms import (
    players_to_adp_rows,
    players_to_dim_rows,
)

if TYPE_CHECKING:
    pass

# Type coercion sets for Sleeper entities
_DIM_INT_COLUMNS = {"age", "years_exp"}
_ADP_INT_COLUMNS = {"season"}
_ADP_FLOAT_COLUMNS = {
    "adp_half_ppr",
    "adp_ppr",
    "adp_std",
    "adp_2qb",
    "adp_dynasty",
}
_ADP_BOOL_COLUMNS = {"is_current"}


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


def players_to_dim_table(players: list[SleeperPlayer]) -> ibis.Table:
    """Convert SleeperPlayer objects into an Ibis dim_sl_players table.

    Parameters
    ----------
    players : list[SleeperPlayer]
        Players from the Sleeper API.

    Returns
    -------
    ibis.Table
        Typed Ibis table expression with player metadata.
    """
    rows = players_to_dim_rows(players)
    if not rows:
        return ibis.memtable(
            {"sleeper_player_id": [], "full_name": [], "position": [], "team": []}
        )
    table = ibis.memtable(rows)
    return _coerce_types(table, _DIM_INT_COLUMNS, set(), set())


def players_to_adp_table(
    players: list[SleeperPlayer],
    season: int,
    ingestion_date: date | None = None,
) -> ibis.Table:
    """Convert SleeperPlayer objects into an Ibis fact_sl_adp table.

    Parameters
    ----------
    players : list[SleeperPlayer]
        Players with ADP data.
    season : int
        NFL season year.
    ingestion_date : date | None
        Effective date for SCD2 tracking.

    Returns
    -------
    ibis.Table
        Typed Ibis table with ADP data per scoring format.
    """
    rows = players_to_adp_rows(players, season=season, ingestion_date=ingestion_date)
    if not rows:
        return ibis.memtable(
            {"season": [], "sleeper_player_id": [], "adp_half_ppr": []}
        )
    table = ibis.memtable(rows)
    return _coerce_types(table, _ADP_INT_COLUMNS, _ADP_FLOAT_COLUMNS, _ADP_BOOL_COLUMNS)
