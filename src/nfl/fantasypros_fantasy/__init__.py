"""FantasyPros Fantasy library package."""

from nfl.fantasypros_fantasy.api import FantasyProsApiClient
from nfl.fantasypros_fantasy.pipeline import PipelineConfig, PipelineRunResult, run_pipeline
from nfl.fantasypros_fantasy.validation import (
    ContractValidationError,
    EntityContract,
    get_contract,
    validate,
    validate_polars_frame,
)

__all__ = [
    "api",
    "matching",
    "pipeline",
    "storage",
    "transforms",
    "validation",
    "FantasyProsApiClient",
    "PipelineConfig",
    "PipelineRunResult",
    "run_pipeline",
    "ContractValidationError",
    "EntityContract",
    "get_contract",
    "validate",
    "validate_polars_frame",
]

__version__ = "0.1.0"
