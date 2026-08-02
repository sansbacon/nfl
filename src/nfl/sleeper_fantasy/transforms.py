"""Sleeper data transformation utilities.

Converts SleeperPlayer dataclasses into flat dictionaries suitable for
PySpark DataFrame creation and Unity Catalog persistence.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from nfl.sleeper_fantasy.api import SleeperPlayer


def players_to_dim_rows(players: list[SleeperPlayer]) -> list[dict[str, Any]]:
    """Convert SleeperPlayer objects into dim_sl_players rows.

    Produces one row per player with current metadata.
    """
    return [
        {
            "sleeper_player_id": p.sleeper_id,
            "full_name": p.full_name,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "position": p.position,
            "team": p.team,
            "age": p.age,
            "years_exp": p.years_exp,
            "college": p.college,
            "status": p.status,
        }
        for p in players
    ]


def players_to_adp_rows(
    players: list[SleeperPlayer],
    season: int,
    ingestion_date: date | None = None,
) -> list[dict[str, Any]]:
    """Convert SleeperPlayer objects into fact_sl_adp rows.

    Produces one row per player with all five ADP scoring formats.
    Natural key: (season, sleeper_player_id).

    Parameters
    ----------
    players : list[SleeperPlayer]
        Players with ADP data.
    season : int
        NFL season year.
    ingestion_date : date | None
        Effective date for SCD2 tracking. Defaults to today.
    """
    effective = ingestion_date or date.today()
    return [
        {
            "season": season,
            "sleeper_player_id": p.sleeper_id,
            "adp_half_ppr": p.adp_half_ppr,
            "adp_ppr": p.adp_ppr,
            "adp_std": p.adp_std,
            "adp_2qb": p.adp_2qb,
            "adp_dynasty": p.adp_dynasty,
            "ingestion_date": effective,
            "end_date": None,
            "is_current": True,
        }
        for p in players
        if p.adp_half_ppr is not None
    ]
