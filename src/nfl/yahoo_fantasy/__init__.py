"""Unified Yahoo Fantasy library package."""

from nfl.yahoo_fantasy.api import YahooApiClient
from nfl.yahoo_fantasy.auth import build_oauth_session
from nfl.yahoo_fantasy.notebook import configure_polars_display, make_table_loaders
from nfl.yahoo_fantasy.pipeline import PipelineConfig, PipelineRunResult, run_pipeline
from nfl.yahoo_fantasy.presentation import format_table_for_display
from nfl.yahoo_fantasy.queries import (
    average_scoring_by_position_by_team,
    build_player_weekly_points,
    enrich_weekly_team_points,
    league_average_by_position,
    league_team_info,
    latest_roster_snapshot,
    player_points_health,
    position_usage_counts,
    position_weekly_points,
    scoring_quality_by_week,
    standings_summary,
    team_weekly_fallback_from_matchups,
    team_position_weekly_points,
    weekly_team_points,
    weekly_team_points_resolved,
)
from nfl.yahoo_fantasy.warehouse import (
    DEFAULT_NAMESPACES,
    CatalogPaths,
    RegistrationReport,
    WarehouseQueryError,
    YahooWarehouseClient,
)

__all__ = [
    "api",
    "auth",
    "pipeline",
    "transforms",
    "validation",
    "YahooApiClient",
    "build_oauth_session",
    "PipelineConfig",
    "PipelineRunResult",
    "run_pipeline",
    "configure_polars_display",
    "make_table_loaders",
    "format_table_for_display",
    "YahooWarehouseClient",
    "WarehouseQueryError",
    "CatalogPaths",
    "RegistrationReport",
    "DEFAULT_NAMESPACES",
    "league_team_info",
    "standings_summary",
    "build_player_weekly_points",
    "weekly_team_points",
    "weekly_team_points_resolved",
    "team_weekly_fallback_from_matchups",
    "enrich_weekly_team_points",
    "position_weekly_points",
    "team_position_weekly_points",
    "position_usage_counts",
    "latest_roster_snapshot",
    "average_scoring_by_position_by_team",
    "league_average_by_position",
    "player_points_health",
    "scoring_quality_by_week",
]

__version__ = "0.1.0"
