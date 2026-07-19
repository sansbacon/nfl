"""NBA data contracts for Yahoo Fantasy datasets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NbaStanding:
    league_key: str
    season: int
    team_key: str
    rank: int
    scoring_type: str
    points_for: float


@dataclass(frozen=True, slots=True)
class NbaStandingCategoryScore:
    league_key: str
    season: int
    team_key: str
    stat_id: str
    stat_name: str
    category_value: float
    category_rank: int | None = None


@dataclass(frozen=True, slots=True)
class NbaRosterEntry:
    league_key: str
    season: int
    team_key: str
    player_key: str
    selected_position: str
    is_starting: bool


@dataclass(frozen=True, slots=True)
class NbaPlayerProjection:
    league_key: str
    season: int
    week: int | None
    player_key: str
    projected_points: float


NBA_CONTRACTS: dict[str, dict[str, tuple[str, ...]]] = {
    "standings": {
        "required": (
            "league_key",
            "season",
            "team_key",
            "rank",
            "scoring_type",
            "points_for",
        ),
        "optional": (),
        "primary_key": ("league_key", "season", "team_key"),
    },
    "standing_category_scores": {
        "required": (
            "league_key",
            "season",
            "team_key",
            "stat_id",
            "stat_name",
            "category_value",
        ),
        "optional": ("category_rank",),
        "primary_key": ("league_key", "season", "team_key", "stat_id"),
    },
    "roster_entries": {
        "required": (
            "league_key",
            "season",
            "team_key",
            "player_key",
            "selected_position",
            "is_starting",
        ),
        "optional": (),
        "primary_key": ("league_key", "season", "team_key", "player_key"),
    },
    "player_projections": {
        "required": (
            "league_key",
            "season",
            "player_key",
            "projected_points",
        ),
        "optional": ("week",),
        "primary_key": ("league_key", "season", "player_key", "week"),
    },
}
