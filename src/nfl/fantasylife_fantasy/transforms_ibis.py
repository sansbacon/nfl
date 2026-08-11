"""Ibis-based transforms for Fantasy Life data.

Produces two tables:
- ``fact_fl_ranks`` — SCD2 rankings fact table.
- ``fl_player_map`` — FL player ID to canonical mfl_id mapping.

Requires: pip install nfl[ibis]
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import ibis
import pyarrow as pa


@dataclass(frozen=True, slots=True)
class FlTransformResult:
    """Result of FL transforms containing Ibis table expressions."""

    fact_fl_ranks: ibis.Table
    fl_player_map: ibis.Table


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

_FACT_FL_RANKS_SCHEMA = pa.schema([
    ("season", pa.int32()),
    ("player", pa.string()),
    ("position", pa.string()),
    ("team", pa.string()),
    ("bye", pa.int32()),
    ("position_tier", pa.int32()),
    ("overall_tier", pa.int32()),
    ("consensus_rank", pa.int32()),
    ("rank_stddev", pa.float64()),
    ("adp", pa.float64()),
    ("adp_diff", pa.float64()),
    ("utilization_score", pa.int32()),
    ("last_week_diff", pa.int32()),
    ("scoring_format", pa.string()),
    ("ingestion_date", pa.date32()),
    ("end_date", pa.date32()),
    ("is_current", pa.bool_()),
])

_FL_PLAYER_MAP_SCHEMA = pa.schema([
    ("fl_id", pa.int64()),
    ("fl_uuid", pa.string()),
    ("display_name", pa.string()),
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
    """Transform parsed CSV records into the fact_fl_ranks Ibis table.

    Adds SCD2 metadata columns (ingestion_date, end_date, is_current).

    Parameters
    ----------
    csv_records : list[dict]
        Output of ``parse_rankings_csv`` (optionally enriched with fl_id).
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
            "position_tier": rec.get("position_tier"),
            "overall_tier": rec.get("overall_tier"),
            "consensus_rank": rec.get("consensus_rank"),
            "rank_stddev": rec.get("rank_stddev"),
            "adp": rec.get("adp"),
            "adp_diff": rec.get("adp_diff"),
            "utilization_score": rec.get("utilization_score"),
            "last_week_diff": rec.get("last_week_diff"),
            "scoring_format": rec.get("scoring_format", "PPR"),
            "ingestion_date": eff_date,
            "end_date": None,
            "is_current": True,
        })

    if not rows:
        empty = pa.table(
            {f.name: pa.array([], type=f.type) for f in _FACT_FL_RANKS_SCHEMA},
            schema=_FACT_FL_RANKS_SCHEMA,
        )
        return ibis.memtable(empty)

    # Build a PyArrow table with explicit schema to avoid NULL-typed columns
    # (DuckDB rejects columns where all values are None without a type hint)
    arrays = {
        "season": pa.array([r["season"] for r in rows], type=pa.int32()),
        "player": pa.array([r["player"] for r in rows], type=pa.string()),
        "position": pa.array([r["position"] for r in rows], type=pa.string()),
        "team": pa.array([r["team"] for r in rows], type=pa.string()),
        "bye": pa.array([r["bye"] for r in rows], type=pa.int32()),
        "position_tier": pa.array([r["position_tier"] for r in rows], type=pa.int32()),
        "overall_tier": pa.array([r["overall_tier"] for r in rows], type=pa.int32()),
        "consensus_rank": pa.array([r["consensus_rank"] for r in rows], type=pa.int32()),
        "rank_stddev": pa.array([r["rank_stddev"] for r in rows], type=pa.float64()),
        "adp": pa.array([r["adp"] for r in rows], type=pa.float64()),
        "adp_diff": pa.array([r["adp_diff"] for r in rows], type=pa.float64()),
        "utilization_score": pa.array([r["utilization_score"] for r in rows], type=pa.int32()),
        "last_week_diff": pa.array([r["last_week_diff"] for r in rows], type=pa.int32()),
        "scoring_format": pa.array([r["scoring_format"] for r in rows], type=pa.string()),
        "ingestion_date": pa.array([r["ingestion_date"] for r in rows], type=pa.date32()),
        "end_date": pa.array([r["end_date"] for r in rows], type=pa.date32()),
        "is_current": pa.array([r["is_current"] for r in rows], type=pa.bool_()),
    }
    return ibis.memtable(pa.table(arrays))


def transform_player_map(
    player_map_records: list[dict[str, Any]],
) -> ibis.Table:
    """Transform player map records into the fl_player_map Ibis table.

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
            {f.name: pa.array([], type=f.type) for f in _FL_PLAYER_MAP_SCHEMA},
            schema=_FL_PLAYER_MAP_SCHEMA,
        )
        return ibis.memtable(empty)

    return ibis.memtable(player_map_records)


def transform(
    csv_records: list[dict[str, Any]],
    player_map_records: list[dict[str, Any]],
    *,
    season: int,
    ingestion_date: date | None = None,
) -> FlTransformResult:
    """Run all FL transforms and return the result bundle.

    Parameters
    ----------
    csv_records : list[dict]
        Parsed (and optionally ID-enriched) CSV records.
    player_map_records : list[dict]
        Player map from ``build_player_map``.
    season : int
        NFL season year.
    ingestion_date : date | None
        Override for ingestion date.

    Returns
    -------
    FlTransformResult
    """
    return FlTransformResult(
        fact_fl_ranks=transform_rankings(
            csv_records, season=season, ingestion_date=ingestion_date
        ),
        fl_player_map=transform_player_map(player_map_records),
    )
