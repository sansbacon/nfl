"""Pipeline orchestration for ESPN Fantasy data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from nfl.common.config import PipelineConfigBase
from nfl.common.storage import persist_with_polars
from nfl.espn_fantasy.api import EspnFantasyClient
from nfl.espn_fantasy.constants import DEFAULT_BATCH_SIZE, MAX_PLAYERS
from nfl.espn_fantasy.transforms import (
    players_to_ranks_rows,
    players_to_season_projection_rows,
    players_to_weekly_projection_rows,
)


@dataclass(frozen=True, slots=True)
class PipelineConfig(PipelineConfigBase):
    """Configuration for the ESPN Fantasy data pipeline.

    Inherits common fields from :class:`~nfl.common.config.PipelineConfigBase`
    and adds ESPN-specific options.

    Parameters
    ----------
    timeout_seconds : int
        HTTP request timeout for ESPN API calls (default 30).
    max_players : int
        Maximum number of players to fetch per pipeline run.
    batch_size : int
        Number of players to request per API call.
    """

    polars_output_dir: str | Path = "./output/espn_polars"
    timeout_seconds: int = 30
    max_players: int = MAX_PLAYERS
    batch_size: int = DEFAULT_BATCH_SIZE


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    """Result of an ESPN pipeline run."""

    season: int
    frames: dict[str, pl.DataFrame]
    polars_outputs: dict[str, Path]
    player_count: int


def _build_client(config: PipelineConfig) -> EspnFantasyClient:
    return EspnFantasyClient(timeout_seconds=config.timeout_seconds)


def run_pipeline(
    config: PipelineConfig | None = None,
    api_client: Any | None = None,
) -> PipelineRunResult:
    """Run the ESPN Fantasy data pipeline.

    Fetches player projections and rankings from ESPN's public API,
    transforms them into flat Polars DataFrames, and optionally persists
    to local files.

    Parameters
    ----------
    config : PipelineConfig | None
        Pipeline configuration. Defaults to sensible values.
    api_client : EspnFantasyClient | None
        Optional pre-configured API client. If not provided, one is built
        from ``config``.

    Returns
    -------
    PipelineRunResult
        Frames, file outputs, and player count.
    """
    cfg = config or PipelineConfig()
    client = api_client if api_client is not None else _build_client(cfg)

    # --- Extract ---
    players = client.fetch_all_players(
        cfg.season,
        max_players=cfg.max_players,
        batch_size=cfg.batch_size,
    )

    # --- Transform ---
    effective = cfg.effective_date
    ranks_rows = players_to_ranks_rows(players, cfg.season, ingestion_date=effective)
    season_proj_rows = players_to_season_projection_rows(
        players, cfg.season, ingestion_date=effective
    )
    weekly_proj_rows = players_to_weekly_projection_rows(
        players, cfg.season, ingestion_date=effective
    )

    frames: dict[str, pl.DataFrame] = {
        "fact_espn_ranks": pl.DataFrame(ranks_rows) if ranks_rows else pl.DataFrame(),
        "fact_espn_projections": (
            pl.DataFrame(season_proj_rows) if season_proj_rows else pl.DataFrame()
        ),
        "fact_espn_weekly_projections": (
            pl.DataFrame(weekly_proj_rows) if weekly_proj_rows else pl.DataFrame()
        ),
    }

    # --- Load ---
    polars_outputs: dict[str, Path] = {}

    if cfg.storage_target == "polars":
        polars_outputs = persist_with_polars(
            frames,
            output_dir=cfg.polars_output_dir,
            file_format=cfg.polars_file_format,
        )

    return PipelineRunResult(
        season=cfg.season,
        frames=frames,
        polars_outputs=polars_outputs,
        player_count=len(players),
    )
