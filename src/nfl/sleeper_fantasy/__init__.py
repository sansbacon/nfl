"""Sleeper Fantasy Football data source.

Public API (no authentication required) for ADP data from Sleeper
mock drafts across multiple scoring formats.
"""

from nfl.sleeper_fantasy.api import SleeperApiError, SleeperClient, SleeperPlayer
from nfl.sleeper_fantasy.transforms import players_to_adp_rows, players_to_dim_rows

__all__ = [
    "SleeperApiError",
    "SleeperClient",
    "SleeperPlayer",
    "api",
    "matching",
    "pipeline",
    "players_to_adp_rows",
    "players_to_dim_rows",
    "transforms",
]

__version__ = "0.1.0"
