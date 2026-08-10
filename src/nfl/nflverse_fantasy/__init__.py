"""NFLverse ingestion library package."""

from nfl.nflverse_fantasy.api import NflverseApiClient

__all__ = [
    "NflverseApiClient",
    "api",
    "models",
    "pipeline",
    "transforms",
    "validation",
]

__version__ = "0.1.0"
