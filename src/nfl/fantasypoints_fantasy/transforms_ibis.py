"""Ibis-based transforms for Fantasy Points data.

Produces two tables:
- ``fact_fpts_ranks`` — SCD2 rankings fact table.
- ``fpts_player_map`` — FPTS player name to canonical mfl_id mapping.

Requires: pip install nfl[ibis]
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import ibis
import pyarrow as pa


@dataclass(frozen=True, slots=True)
class FptsTransformResult:
    """Result of FPTS transforms containing Ibis table expressions."""

    fact_fpts_ranks: ibis.Table
    fpts_player_map: ibis.Table


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

_FACT_FPTS_RANKS_SCHEMA = pa.schema([
    ("season", pa.int32()),
    ("player", pa.string()),
    ("position", pa.string()),
    ("team", pa.string()),
    ("bye", pa.int32()),
    ("overall_rank", pa.int32()),
    ("auction_value", pa.int32()),
    ("exodia", pa.bool_()),
    ("scoring_format", pa.string()),
    ("ingestion_date", pa.date32()),
    ("end_date", pa.date32()),
    ("is_current", pa.bool_()),
])

_FPTS_PLAYER_MAP_SCHEMA = pa.schema([
    ("player", pa.string()),
    ("position", pa.string()),
    ("team", pa.string()),
    ("merge_name", pa.string()),
    ("mfl_id", pa.string()),
    ("match_method", pa.string()),
])


# ---------------------------------------------------------------------------
# Transform functions
# ---------------------------------------------------------------------------


def transform_rankings(
    csv_records: list[dict[str, Any]],
    *,
    season: int,
    ingestion_date: date | None = None,
) -> ibis.Table:
    """Transform parsed CSV records into the fact_fpts_ranks Ibis table.

    Adds SCD2 metadata columns (ingestion_date, end_date, is_current).

    Parameters
    ----------
    csv_records : list[dict]
        Output of ``parse_rankings_csv``.
    season : int
        NFL season year.
    ingestion_date : date | None
        Override for ingestion timestamp (defaults to today).

    Returns
    -------
    ibis.Table
    """
    eff_date = ingestion_date or date.today()

    rows: list[dict[str, Any]] = []
    for rec in csv_records:
        rows.append({
            "season": season,
            "player": rec["player"],
            "position": rec["position"],
            "team": rec["team"],
            "bye": rec.get("bye"),
            "overall_rank": rec.get("overall_rank"),
            "auction_value": rec.get("auction_value"),
            "exodia": rec.get("exodia", False),
            "scoring_format": rec.get("scoring_format", "Redraft PPR"),
            "ingestion_date": eff_date,
            "end_date": None,
            "is_current": True,
        })

    if not rows:
        empty = pa.table(
            {f.name: pa.array([], type=f.type) for f in _FACT_FPTS_RANKS_SCHEMA},
            schema=_FACT_FPTS_RANKS_SCHEMA,
        )
        return ibis.memtable(empty)

    arrays = {
        "season": pa.array([r["season"] for r in rows], type=pa.int32()),
        "player": pa.array([r["player"] for r in rows], type=pa.string()),
        "position": pa.array([r["position"] for r in rows], type=pa.string()),
        "team": pa.array([r["team"] for r in rows], type=pa.string()),
        "bye": pa.array([r["bye"] for r in rows], type=pa.int32()),
        "overall_rank": pa.array([r["overall_rank"] for r in rows], type=pa.int32()),
        "auction_value": pa.array([r["auction_value"] for r in rows], type=pa.int32()),
        "exodia": pa.array([r["exodia"] for r in rows], type=pa.bool_()),
        "scoring_format": pa.array([r["scoring_format"] for r in rows], type=pa.string()),
        "ingestion_date": pa.array([r["ingestion_date"] for r in rows], type=pa.date32()),
        "end_date": pa.array([r["end_date"] for r in rows], type=pa.date32()),
        "is_current": pa.array([r["is_current"] for r in rows], type=pa.bool_()),
    }
    return ibis.memtable(pa.table(arrays))


def transform_player_map(
    player_map_records: list[dict[str, Any]],
) -> ibis.Table:
    """Transform player map records into the fpts_player_map Ibis table.

    Parameters
    ----------
    player_map_records : list[dict]
        Output of ``build_player_map``.

    Returns
    -------
    ibis.Table
    """
    if not player_map_records:
        empty = pa.table(
            {f.name: pa.array([], type=f.type) for f in _FPTS_PLAYER_MAP_SCHEMA},
            schema=_FPTS_PLAYER_MAP_SCHEMA,
        )
        return ibis.memtable(empty)

    return ibis.memtable(player_map_records)


def transform(
    csv_records: list[dict[str, Any]],
    player_map_records: list[dict[str, Any]],
    *,
    season: int,
    ingestion_date: date | None = None,
) -> FptsTransformResult:
    """Run all FPTS transforms and return the result bundle.

    Parameters
    ----------
    csv_records : list[dict]
        Parsed CSV records.
    player_map_records : list[dict]
        Player map from ``build_player_map``.
    season : int
        NFL season year.
    ingestion_date : date | None
        Override for ingestion date.

    Returns
    -------
    FptsTransformResult
    """
    return FptsTransformResult(
        fact_fpts_ranks=transform_rankings(
            csv_records, season=season, ingestion_date=ingestion_date
        ),
        fpts_player_map=transform_player_map(player_map_records),
    )
