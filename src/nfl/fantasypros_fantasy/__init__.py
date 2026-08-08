"""FantasyPros Fantasy library package."""

from nfl.fantasypros_fantasy.api import FantasyProsApiClient
from nfl.fantasypros_fantasy.matching import build_fp_yahoo_crosswalk, fp_adp_records_to_fp_players
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
    "build_fp_yahoo_crosswalk",
    "fp_adp_records_to_fp_players",
    "ContractValidationError",
    "EntityContract",
    "get_contract",
    "validate",
    "validate_polars_frame",
]

__version__ = "0.1.0"
