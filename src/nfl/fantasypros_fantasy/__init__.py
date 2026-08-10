"""FantasyPros Fantasy library package."""

from nfl.fantasypros_fantasy.api import FantasyProsApiClient
from nfl.fantasypros_fantasy.matching import build_fp_yahoo_crosswalk, fp_adp_records_to_fp_players
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
    "api",
    "build_fp_yahoo_crosswalk",
    "fp_adp_records_to_fp_players",
    "get_contract",
    "matching",
    "pipeline",
    "transforms",
    "validate",
    "validate_polars_frame",
    "validation",
]

__version__ = "0.1.0"
