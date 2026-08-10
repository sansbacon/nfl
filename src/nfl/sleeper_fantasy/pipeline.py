"""Pipeline orchestration for Sleeper Fantasy data."""

from __future__ import annotations

from dataclasses import dataclass

import ibis

from nfl.common.backend import get_backend
from nfl.common.config import PipelineConfigBase
from nfl.common.storage import persist_tables
from nfl.sleeper_fantasy.transforms_ibis import players_to_adp_table, players_to_dim_table
from nfl.sleeper_fantasy.api import SleeperClient


@dataclass(frozen=True, slots=True)
class PipelineConfig(PipelineConfigBase):
    """Configuration for the Sleeper data pipeline.

    Inherits common fields from :class:`~nfl.common.config.PipelineConfigBase`
    and adds Sleeper-specific options.

    Parameters
    ----------
    timeout_seconds : int
        HTTP request timeout for Sleeper API calls (default 60).
    """

    timeout_seconds: int = 60


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    """Result of a Sleeper pipeline run."""

    season: int
    tables: dict[str, ibis.Table]
    write_results: list
    player_count: int
    adp_count: int


def run_pipeline(
    config: PipelineConfig | None = None,
) -> PipelineRunResult:
    """Run the Sleeper data pipeline.

    Fetches ADP and player data from Sleeper's public API,
    transforms into Ibis tables, and persists to the configured backend.

    Parameters
    ----------
    config : PipelineConfig | None
        Pipeline configuration. Defaults to sensible values.

    Returns
    -------
    PipelineRunResult
        Tables, write results, and row counts.
    """
    cfg = config or PipelineConfig()
    backend = get_backend(cfg)

    # --- Extract ---
    client = SleeperClient(timeout_seconds=cfg.timeout_seconds)
    players = client.fetch_players_with_adp(cfg.season)

    # --- Transform ---
    effective_date = cfg.effective_date
    dim_table = players_to_dim_table(players)
    adp_table = players_to_adp_table(players, season=cfg.season, ingestion_date=effective_date)

    tables: dict[str, ibis.Table] = {
        "dim_sl_players": dim_table,
        "fact_sl_adp": adp_table,
    }

    # --- Load ---
    write_results = persist_tables(tables, backend, dry_run=cfg.dry_run)

    return PipelineRunResult(
        season=cfg.season,
        tables=tables,
        write_results=write_results,
        player_count=int(dim_table.count().execute()),
        adp_count=int(adp_table.count().execute()),
    )
