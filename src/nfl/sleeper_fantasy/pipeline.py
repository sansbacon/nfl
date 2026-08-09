"""Pipeline orchestration for Sleeper Fantasy data."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from nfl.common.config import PipelineConfigBase
from nfl.common.storage import persist_with_polars
from nfl.sleeper_fantasy.api import SleeperClient
from nfl.sleeper_fantasy.transforms import players_to_adp_rows, players_to_dim_rows


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

    polars_output_dir: str | Path = "./output/sleeper_polars"
    timeout_seconds: int = 60


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    """Result of a Sleeper pipeline run."""

    season: int
    frames: dict[str, pl.DataFrame]
    polars_outputs: dict[str, Path]
    uc_outputs: list
    player_count: int
    adp_count: int


def run_pipeline(
    config: PipelineConfig | None = None,
) -> PipelineRunResult:
    """Run the Sleeper data pipeline.

    Fetches ADP and player data from Sleeper's public API,
    transforms into dim/fact tables, and optionally persists
    to local Polars files or Unity Catalog.

    Parameters
    ----------
    config : PipelineConfig | None
        Pipeline configuration. Defaults to sensible values.

    Returns
    -------
    PipelineRunResult
        Frames, file outputs, and UC write results.
    """
    cfg = config or PipelineConfig()

    # --- Extract ---
    client = SleeperClient(timeout_seconds=cfg.timeout_seconds)
    players = client.fetch_players_with_adp(cfg.season)

    # --- Transform ---
    effective_date = cfg.effective_date
    dim_rows = players_to_dim_rows(players)
    adp_rows = players_to_adp_rows(players, season=cfg.season, ingestion_date=effective_date)

    frames: dict[str, pl.DataFrame] = {
        "dim_sl_players": pl.DataFrame(dim_rows) if dim_rows else pl.DataFrame(),
        "fact_sl_adp": pl.DataFrame(adp_rows) if adp_rows else pl.DataFrame(),
    }

    # --- Load ---
    polars_outputs: dict[str, Path] = {}
    uc_outputs: list = []

    if cfg.storage_target in ("polars",):
        polars_outputs = persist_with_polars(
            frames, output_dir=cfg.polars_output_dir, file_format=cfg.polars_file_format
        )

    if cfg.storage_target in ("unity_catalog", "uc_volume"):
        try:
            from nfl_databricks.storage import persist_to_uc_tables, persist_to_uc_volume
        except ImportError as exc:
            raise ImportError(
                "Unity Catalog storage requires the nfl-databricks package. "
                "Install it with: pip install nfl-databricks"
            ) from exc

        if cfg.storage_target == "unity_catalog":
            uc_outputs = persist_to_uc_tables(frames, dry_run=cfg.dry_run)
        else:
            uc_outputs = persist_to_uc_volume(frames, dry_run=cfg.dry_run)

    return PipelineRunResult(
        season=cfg.season,
        frames=frames,
        polars_outputs=polars_outputs,
        uc_outputs=uc_outputs,
        player_count=len(dim_rows),
        adp_count=len(adp_rows),
    )
