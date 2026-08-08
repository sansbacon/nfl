"""ESPN data transformation utilities.

Converts EspnPlayer dataclasses into flat dictionaries suitable for
PySpark DataFrame creation and Unity Catalog persistence.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from nfl.espn_fantasy.api import EspnPlayer
from nfl.espn_fantasy.constants import STAT_MAP


def players_to_ranks_rows(
    players: list[EspnPlayer],
    season: int,
    ingestion_date: date | None = None,
) -> list[dict[str, Any]]:
    """Convert ESPN players into fact_espn_ranks rows.

    Produces one row per player with PPR and Standard rankings,
    auction values, and ownership percentages.
    """
    effective = ingestion_date or date.today()
    rows: list[dict[str, Any]] = []

    for p in players:
        if p.rank_ppr is None and p.rank_standard is None:
            continue
        rows.append(
            {
                "espn_id": p.espn_id,
                "player": p.full_name,
                "position": p.position,
                "team": p.team,
                "rank_ppr": p.rank_ppr,
                "rank_standard": p.rank_standard,
                "auction_value_ppr": p.auction_value_ppr,
                "auction_value_standard": p.auction_value_standard,
                "percent_owned": p.percent_owned,
                "percent_started": p.percent_started,
                "season": season,
                "ingestion_date": effective,
                "end_date": None,
                "is_current": True,
            }
        )

    return rows


def players_to_season_projection_rows(
    players: list[EspnPlayer],
    season: int,
    ingestion_date: date | None = None,
) -> list[dict[str, Any]]:
    """Convert ESPN players into fact_espn_projections rows.

    Produces one row per player with full-season stat projections.
    """
    effective = ingestion_date or date.today()
    rows: list[dict[str, Any]] = []

    for p in players:
        if not p.season_projection:
            continue
        row: dict[str, Any] = {
            "espn_id": p.espn_id,
            "player": p.full_name,
            "position": p.position,
            "team": p.team,
            "season": season,
            "projected_total": p.season_projected_total,
            "ingestion_date": effective,
            "end_date": None,
            "is_current": True,
        }
        # Add all stat columns (fill missing with None)
        for col_name in STAT_MAP.values():
            row[col_name] = p.season_projection.get(col_name)
        rows.append(row)

    return rows


def players_to_weekly_projection_rows(
    players: list[EspnPlayer],
    season: int,
    ingestion_date: date | None = None,
) -> list[dict[str, Any]]:
    """Convert ESPN players into fact_espn_weekly_projections rows.

    Produces one row per player per week with stat projections.
    """
    effective = ingestion_date or date.today()
    rows: list[dict[str, Any]] = []

    for p in players:
        for week, stats in p.weekly_projections.items():
            row: dict[str, Any] = {
                "espn_id": p.espn_id,
                "player": p.full_name,
                "position": p.position,
                "team": p.team,
                "season": season,
                "week": week,
                "projected_total": p.weekly_projected_totals.get(week),
                "ingestion_date": effective,
                "end_date": None,
                "is_current": True,
            }
            for col_name in STAT_MAP.values():
                row[col_name] = stats.get(col_name)
            rows.append(row)

    return rows
