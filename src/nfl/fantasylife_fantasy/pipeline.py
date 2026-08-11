"""Pipeline orchestration for Fantasy Life data.

Extracts rankings from CSV + player IDs from HTML, matches to the
canonical crosswalk, transforms via Ibis, and persists to the
configured backend.

Usage::

    from nfl.fantasylife_fantasy.pipeline import PipelineConfig, run_pipeline

    result = run_pipeline(PipelineConfig(
        season=2026,
        rankings_csv_path="/Volumes/nfl/fl/fl_volume/incoming/rankings/fantasy_life_rankings_20260811.csv",
        html_paths=[
            "/Volumes/nfl/fl/fl_volume/incoming/html/flife1.html",
            "/Volumes/nfl/fl/fl_volume/incoming/html/flife2.html",
            "/Volumes/nfl/fl/fl_volume/incoming/html/flife3.html",
            "/Volumes/nfl/fl/fl_volume/incoming/html/flife4.html",
            "/Volumes/nfl/fl/fl_volume/incoming/html/flife5.html",
        ],
        backend="duckdb",
    ))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ibis

from nfl.common.backend import get_backend
from nfl.common.config import PipelineConfigBase
from nfl.common.crosswalk import read_crosswalk
from nfl.common.storage import WriteResult, merge_scd2, persist_tables
from nfl.fantasylife_fantasy.matching import (
    attach_fl_ids,
    build_player_map,
    summarize_matching,
)
from nfl.fantasylife_fantasy.parser import parse_html_players, parse_rankings_csv
from nfl.fantasylife_fantasy.transforms_ibis import FlTransformResult, transform


@dataclass(frozen=True, slots=True)
class PipelineConfig(PipelineConfigBase):
    """Configuration for the Fantasy Life pipeline.

    Parameters
    ----------
    rankings_csv_path : str | Path
        Path to the FL rankings CSV export.
    html_paths : list[str | Path]
        Paths to the HTML player-ID pages (flife1.html–flife5.html).
    crosswalk_database : str
        Ibis database containing dim_ff_player_ids (for crosswalk reads).
    rank_threshold : int
        Only attempt crosswalk matching for players ranked below this.
    """

    rankings_csv_path: str | Path = ""
    html_paths: list[str | Path] = field(default_factory=list)
    crosswalk_database: str = "main"
    rank_threshold: int = 180


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    """Result of a Fantasy Life pipeline run."""

    season: int
    tables: FlTransformResult
    write_results: list[WriteResult]
    matching_summary: dict[str, Any]
    rankings_count: int
    player_map_count: int


def run_pipeline(
    config: PipelineConfig | None = None,
    *,
    csv_records: list[dict[str, Any]] | None = None,
    html_players: list[dict[str, Any]] | None = None,
    crosswalk_records: list[dict[str, Any]] | None = None,
) -> PipelineRunResult:
    """Run the Fantasy Life data pipeline.

    Parameters
    ----------
    config : PipelineConfig | None
        Pipeline configuration. Required fields: rankings_csv_path,
        html_paths.
    csv_records : list[dict] | None
        Pre-parsed CSV records (bypasses file read).
    html_players : list[dict] | None
        Pre-parsed HTML players (bypasses file read).
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

    if html_players is None:
        if not cfg.html_paths:
            raise ValueError("html_paths is required when html_players is not provided")
        html_players = parse_html_players(cfg.html_paths)

    # --- Match: Stage 1 (CSV → HTML) ---
    enriched = attach_fl_ids(csv_records, html_players)

    # --- Match: Stage 2 (FL → crosswalk) ---
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
        enriched, crosswalk_records, rank_threshold=cfg.rank_threshold
    )

    # --- Transform ---
    result = transform(
        csv_records=enriched,
        player_map_records=player_map,
        season=cfg.season,
        ingestion_date=cfg.effective_date,
    )

    # --- Load ---
    tables_to_write = {
        "fact_fl_ranks": result.fact_fl_ranks,
        "fl_player_map": result.fl_player_map,
    }
    write_results = persist_tables(tables_to_write, backend, dry_run=cfg.dry_run)

    # --- Summary ---
    matching_summary = summarize_matching(enriched, player_map)

    rankings_count = int(result.fact_fl_ranks.count().execute())
    map_count = int(result.fl_player_map.count().execute())

    return PipelineRunResult(
        season=cfg.season,
        tables=result,
        write_results=write_results,
        matching_summary=matching_summary,
        rankings_count=rankings_count,
        player_map_count=map_count,
    )
