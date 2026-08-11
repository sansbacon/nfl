"""Pipeline orchestration for FantasyPros data.

Extracts player and ADP data from FantasyPros, transforms via Ibis,
and persists to the configured backend.

Usage::

    from nfl.fantasypros_fantasy.pipeline import PipelineConfig, run_pipeline

    result = run_pipeline(PipelineConfig(season=2025, backend="duckdb"))
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import ibis

from nfl.common.backend import get_backend
from nfl.common.config import PipelineConfigBase
from nfl.common.storage import WriteResult, persist_tables
from nfl.fantasypros_fantasy.api import FantasyProsApiClient
from nfl.fantasypros_fantasy.transforms_ibis import transform


@dataclass(frozen=True, slots=True)
class PipelineConfig(PipelineConfigBase):
    """Configuration for the FantasyPros pipeline.

    Parameters
    ----------
    timeout_seconds : int
        HTTP request timeout for FantasyPros API calls.
    include_adp : bool
        If True (default), also fetch and persist ADP snapshot data.
    """

    timeout_seconds: int = 30
    include_adp: bool = True


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    """Result of a FantasyPros pipeline run."""

    season: int
    tables: dict[str, ibis.Table]
    write_results: list[WriteResult]
    player_count: int
    adp_snapshot_count: int


def run_pipeline(
    config: PipelineConfig | None = None,
    *,
    players: list[dict[str, Any]] | None = None,
    adp_snapshots: list[dict[str, Any]] | None = None,
) -> PipelineRunResult:
    """Run the FantasyPros data pipeline.

    Fetches player rosters and ADP data from FantasyPros,
    transforms into Ibis tables, and persists to the configured backend.

    Parameters
    ----------
    config : PipelineConfig | None
        Pipeline configuration. Defaults to sensible values.
    players : list[dict] | None
        Pre-extracted player records (bypasses API call).
    adp_snapshots : list[dict] | None
        Pre-extracted ADP records (bypasses API call).

    Returns
    -------
    PipelineRunResult
    """
    cfg = config or PipelineConfig()
    backend = get_backend(cfg)

    # --- Extract ---
    client: FantasyProsApiClient | None = None
    if players is None:
        client = FantasyProsApiClient(timeout_seconds=cfg.timeout_seconds)
        players = client.get_players(cfg.season)

    if adp_snapshots is None and cfg.include_adp:
        if client is None:
            client = FantasyProsApiClient(timeout_seconds=cfg.timeout_seconds)
        adp_snapshots = client.get_adp_snapshots(
            cfg.season, effective_date=cfg.effective_date
        )

    # --- Transform ---
    tables = transform(
        common_entities={"fp_player": players},
        nfl_entities={
            "fp_adp_snapshot": adp_snapshots or [],
            "fp_yahoo_player_map": [],
        },
    )

    # --- Load ---
    write_results = persist_tables(tables, backend, dry_run=cfg.dry_run)

    return PipelineRunResult(
        season=cfg.season,
        tables=tables,
        write_results=write_results,
        player_count=int(tables.get("fp_player", ibis.memtable({"x": []})).count().execute()),
        adp_snapshot_count=int(
            tables.get("nfl_fp_adp_snapshot", ibis.memtable({"x": []})).count().execute()
        ),
    )
