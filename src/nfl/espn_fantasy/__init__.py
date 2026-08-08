"""ESPN Fantasy Football library package.

Public API client for ESPN projections and rankings.
No authentication or league membership required.
"""

from nfl.espn_fantasy.api import EspnApiError, EspnFantasyClient, EspnPlayer
from nfl.espn_fantasy.constants import (
    ALL_FANTASY_SLOT_IDS,
    POSITION_MAP,
    STAT_MAP,
    TEAM_MAP,
)
from nfl.espn_fantasy.pipeline import PipelineConfig, PipelineRunResult, run_pipeline
from nfl.espn_fantasy.transforms import (
    players_to_ranks_rows,
    players_to_season_projection_rows,
    players_to_weekly_projection_rows,
)

__all__ = [
    "ALL_FANTASY_SLOT_IDS",
    "POSITION_MAP",
    "STAT_MAP",
    "TEAM_MAP",
    "EspnApiError",
    "EspnFantasyClient",
    "EspnPlayer",
    "PipelineConfig",
    "PipelineRunResult",
    "api",
    "constants",
    "pipeline",
    "players_to_ranks_rows",
    "players_to_season_projection_rows",
    "players_to_weekly_projection_rows",
    "run_pipeline",
    "transforms",
]

__version__ = "0.1.0"
