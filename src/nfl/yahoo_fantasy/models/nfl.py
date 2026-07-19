"""NFL data contracts for Yahoo Fantasy datasets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NflStanding:
    league_key: str
    season: int
    team_key: str
    rank: int
    wins: int
    losses: int
    ties: int
    points_for: float
    points_against: float


@dataclass(frozen=True, slots=True)
class NflMatchup:
    league_key: str
    season: int
    week: int
    team_key: str
    opponent_team_key: str
    points: float
    opponent_points: float
    is_playoff: bool
    is_consolation: bool


@dataclass(frozen=True, slots=True)
class NflRosterEntry:
    league_key: str
    season: int
    week: int
    team_key: str
    player_key: str
    selected_position: str
    is_starting: bool
    points: float | None = None


@dataclass(frozen=True, slots=True)
class NflPlayerStatWeekly:
    league_key: str
    season: int
    week: int
    player_key: str
    fantasy_points: float
    status: str | None = None
    bye_week: int | None = None
    stats: list[dict[str, float | str]] | None = None


NFL_CONTRACTS: dict[str, dict[str, tuple[str, ...]]] = {
    "standings": {
        "required": (
            "league_key",
            "season",
            "team_key",
            "rank",
            "wins",
            "losses",
            "ties",
            "points_for",
            "points_against",
        ),
        "optional": (),
        "primary_key": ("league_key", "season", "team_key"),
    },
    "matchups": {
        "required": (
            "league_key",
            "season",
            "week",
            "team_key",
            "opponent_team_key",
            "points",
            "opponent_points",
            "is_playoff",
            "is_consolation",
        ),
        "optional": (),
        "primary_key": ("league_key", "season", "week", "team_key"),
    },
    "roster_entries": {
        "required": (
            "league_key",
            "season",
            "week",
            "team_key",
            "player_key",
            "selected_position",
            "is_starting",
        ),
        "optional": ("points",),
        "primary_key": ("league_key", "season", "week", "team_key", "player_key"),
    },
    "player_stats_weekly": {
        "required": (
            "league_key",
            "season",
            "week",
            "player_key",
            "fantasy_points",
        ),
        "optional": ("status", "bye_week", "stats"),
        "primary_key": ("league_key", "season", "week", "player_key"),
    },
}
