"""NFLverse ingestion library package."""

from nfl.nflverse_fantasy.api import NflverseApiClient
from nfl.nflverse_fantasy.pipeline import PipelineConfig, PipelineRunResult, run_pipeline

__all__ = [
    "NflverseApiClient",
    "PipelineConfig",
    "PipelineRunResult",
    "api",
    "models",
    "pipeline",
    "run_pipeline",
    "storage",
    "transforms",
    "validation",
]

__version__ = "0.1.0"
