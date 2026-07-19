"""Canonical common data contracts shared by all sports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SportCode = Literal["nfl", "nba"]


@dataclass(frozen=True, slots=True)
class League:
    league_key: str
    league_id: str
    game_id: int
    game_code: SportCode
    season: int
    league_name: str
    scoring_type: str
    league_type: str
    num_teams: int | None = None


@dataclass(frozen=True, slots=True)
class Team:
    team_key: str
    league_key: str
    team_id: int
    team_name: str
    owner_name: str
    draft_position: int | None = None


@dataclass(frozen=True, slots=True)
class Player:
    player_key: str
    player_id: int
    game_id: int
    full_name: str
    display_position: str
    editorial_team_abbr: str | None = None


@dataclass(frozen=True, slots=True)
class DraftPick:
    league_key: str
    season: int
    team_key: str
    player_key: str
    pick_number: int
    round_number: int
    cost: int | None = None


@dataclass(frozen=True, slots=True)
class Transaction:
    transaction_key: str
    league_key: str
    season: int
    transaction_type: str
    status: str
    player_key: str
    source_team_key: str | None = None
    destination_team_key: str | None = None


@dataclass(frozen=True, slots=True)
class StatCategory:
    game_id: int
    stat_id: str
    display_name: str
    name: str


@dataclass(frozen=True, slots=True)
class ScoringRule:
    league_key: str
    season: int
    stat_id: str
    points_per_unit: float
    bonus_target: float | None = None
    bonus_points: float | None = None


COMMON_ENTITY_NAMES: tuple[str, ...] = (
    "league",
    "team",
    "player",
    "draft_pick",
    "transaction",
    "stat_category",
    "scoring_rule",
)
