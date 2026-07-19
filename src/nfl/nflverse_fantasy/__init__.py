"""NFLverse ingestion library package."""

from nfl.nflverse_fantasy.api import NflverseApiClient
from nfl.nflverse_fantasy.pipeline import PipelineConfig, PipelineRunResult, run_pipeline

__all__ = [
    "api",
    "models",
    "pipeline",
    "storage",
    "transforms",
    "validation",
    "NflverseApiClient",
    "PipelineConfig",
    "PipelineRunResult",
    "run_pipeline",
]

__version__ = "0.1.0"
