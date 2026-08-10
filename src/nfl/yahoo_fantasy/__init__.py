"""Unified Yahoo Fantasy library package.

Public API surface — primary entry points for consumers.
Individual query functions are accessible via the `queries` submodule:
    from nfl.yahoo_fantasy.queries import standings_summary
"""

from nfl.yahoo_fantasy.api import YahooApiClient
from nfl.yahoo_fantasy.auth import build_oauth_session
from nfl.yahoo_fantasy.warehouse import (
    CatalogPaths,
    RegistrationReport,
    WarehouseQueryError,
    YahooWarehouseClient,
)

__all__ = [
    "CatalogPaths",
    "RegistrationReport",
    "WarehouseQueryError",
    # Top-level re-exports
    "YahooApiClient",
    "YahooWarehouseClient",
    # Submodules (importable via nfl.yahoo_fantasy.<name>)
    "api",
    "auth",
    "build_oauth_session",
    "historical_auction",
    "notebook",
    "pipeline",
    "presentation",
    "queries",
    "transforms",
    "validation",
    "views",
    "warehouse",
]

__version__ = "0.1.0"
