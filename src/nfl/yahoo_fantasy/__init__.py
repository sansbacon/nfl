"""Unified Yahoo Fantasy library package.

Public API surface — primary entry points for consumers.
Individual query functions are accessible via the `queries` submodule:
    from nfl.yahoo_fantasy.queries import standings_summary
"""

from nfl.yahoo_fantasy.api import YahooApiClient
from nfl.yahoo_fantasy.auth import build_oauth_session
from nfl.yahoo_fantasy.pipeline import PipelineConfig, PipelineRunResult, run_pipeline
from nfl.yahoo_fantasy.warehouse import (
    CatalogPaths,
    RegistrationReport,
    WarehouseQueryError,
    YahooWarehouseClient,
)

__all__ = [
    # Submodules (importable via nfl.yahoo_fantasy.<name>)
    "api",
    "auth",
    "historical_auction",
    "notebook",
    "pipeline",
    "presentation",
    "queries",
    "storage",
    "transforms",
    "validation",
    "views",
    "warehouse",
    # Top-level re-exports
    "YahooApiClient",
    "build_oauth_session",
    "PipelineConfig",
    "PipelineRunResult",
    "run_pipeline",
    "YahooWarehouseClient",
    "WarehouseQueryError",
    "CatalogPaths",
    "RegistrationReport",
]

__version__ = "0.1.0"
