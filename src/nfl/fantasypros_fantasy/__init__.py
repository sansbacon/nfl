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
    "ContractValidationError",
    "EntityContract",
    "FantasyProsApiClient",
    "PipelineConfig",
    "PipelineRunResult",
    "api",
    "get_contract",
    "matching",
    "pipeline",
    "run_pipeline",
    "storage",
    "transforms",
    "validate",
    "validate_polars_frame",
    "validation",
]

__version__ = "0.1.0"
