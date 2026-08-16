"""Pipeline orchestration for Fantasy Points data.

Extracts rankings from CSV, matches to the canonical crosswalk,
transforms via Ibis, and persists to the configured backend.

Usage::

    from nfl.fantasypoints_fantasy.pipeline import PipelineConfig, run_pipeline

    result = run_pipeline(PipelineConfig(
        season=2026,
        rankings_csv_path="/Volumes/nfl/fpts/fpts_volume/incoming/ranks/rankings.redraft.barrett.csv",
        backend="duckdb",
    ))
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ibis

from nfl.common.backend import get_backend
from nfl.common.config import PipelineConfigBase
from nfl.common.crosswalk import read_crosswalk
from nfl.common.storage import WriteResult, persist_tables
from nfl.fantasypoints_fantasy.matching import build_player_map, summarize_matching
from nfl.fantasypoints_fantasy.parser import parse_rankings_csv
from nfl.fantasypoints_fantasy.transforms_ibis import FptsTransformResult, transform


@dataclass(frozen=True, slots=True)
class PipelineConfig(PipelineConfigBase):
    """Configuration for the Fantasy Points pipeline.

    Parameters
    ----------
    rankings_csv_path : str | Path
        Path to the FPTS rankings CSV export.
    crosswalk_database : str
        Ibis database containing dim_ff_player_ids (for crosswalk reads).
    rank_threshold : int
        Only attempt crosswalk matching for players ranked at or below this.
    """

    rankings_csv_path: str | Path = ""
    crosswalk_database: str = "main"
    rank_threshold: int = 180


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    """Result of a Fantasy Points pipeline run."""

    season: int
    tables: FptsTransformResult
    write_results: list[WriteResult]
    matching_summary: dict[str, Any]
    rankings_count: int
    player_map_count: int


def run_pipeline(
    config: PipelineConfig | None = None,
    *,
    csv_records: list[dict[str, Any]] | None = None,
    crosswalk_records: list[dict[str, Any]] | None = None,
) -> PipelineRunResult:
    """Run the Fantasy Points data pipeline.

    Parameters
    ----------
    config : PipelineConfig | None
        Pipeline configuration. Required field: rankings_csv_path.
    csv_records : list[dict] | None
        Pre-parsed CSV records (bypasses file read).
    crosswalk_records : list[dict] | None
        Pre-loaded crosswalk records (bypasses backend read).

    Returns
    -------
    PipelineRunResult
    """
    cfg = config or PipelineConfig()
    backend = get_backend(cfg)

    # --- Extract ---
    if csv_records is None:
        if not cfg.rankings_csv_path:
            raise ValueError("rankings_csv_path is required when csv_records is not provided")
        csv_records = parse_rankings_csv(cfg.rankings_csv_path)

    # --- Match to crosswalk ---
    if crosswalk_records is None:
        try:
            xwalk_table = read_crosswalk(backend, database=cfg.crosswalk_database)
            crosswalk_records = xwalk_table.execute().to_pydict()
            # Convert columnar dict to list of row dicts
            if crosswalk_records:
                keys = list(crosswalk_records.keys())
                n_rows = len(crosswalk_records[keys[0]])
                crosswalk_records = [
                    {k: crosswalk_records[k][i] for k in keys}
                    for i in range(n_rows)
                ]
        except Exception:
            # Crosswalk not available — skip mfl_id matching
            crosswalk_records = []

    player_map = build_player_map(
        csv_records, crosswalk_records, rank_threshold=cfg.rank_threshold
    )

    # --- Transform ---
    result = transform(
        csv_records=csv_records,
        player_map_records=player_map,
        season=cfg.season,
        ingestion_date=cfg.effective_date,
    )

    # --- Load ---
    tables_to_write = {
        "fact_fpts_ranks": result.fact_fpts_ranks,
        "fpts_player_map": result.fpts_player_map,
    }
    write_results = persist_tables(tables_to_write, backend, dry_run=cfg.dry_run)

    # --- Summary ---
    matching_summary = summarize_matching(csv_records, player_map)

    rankings_count = int(result.fact_fpts_ranks.count().execute())
    map_count = int(result.fpts_player_map.count().execute())

    return PipelineRunResult(
        season=cfg.season,
        tables=result,
        write_results=write_results,
        matching_summary=matching_summary,
        rankings_count=rankings_count,
        player_map_count=map_count,
    )
