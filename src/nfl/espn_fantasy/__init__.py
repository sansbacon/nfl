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
from nfl.espn_fantasy.transforms import (
    players_to_ranks_rows,
    players_to_season_projection_rows,
    players_to_weekly_projection_rows,
)

__all__ = [
    "api",
    "constants",
    "transforms",
    "EspnApiError",
    "EspnFantasyClient",
    "EspnPlayer",
    "ALL_FANTASY_SLOT_IDS",
    "POSITION_MAP",
    "STAT_MAP",
    "TEAM_MAP",
    "players_to_ranks_rows",
    "players_to_season_projection_rows",
    "players_to_weekly_projection_rows",
]

__version__ = "0.1.0"
