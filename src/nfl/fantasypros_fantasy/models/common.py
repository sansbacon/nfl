"""Canonical FantasyPros contracts shared by all sports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class FpPlayer:
    fp_player_id: str
    full_name: str
    first_name: str
    last_name: str
    position: str
    team: str


@dataclass(frozen=True, slots=True)
class FpAdpSnapshot:
    fp_player_id: str
    season: int
    rank: int
    adp: float
    effective_date: date
    is_current: bool
    adp_espn: float | None = None
    adp_sleeper: float | None = None
    adp_cbs: float | None = None
    adp_nfl: float | None = None
    adp_rtsports: float | None = None
    adp_fantrax: float | None = None
    adp_realtime: float | None = None
    adp_formatted: str | None = None
    high: int | None = None
    low: int | None = None
    stdev: float | None = None
    bye_week: int | None = None
    end_date: date | None = None


@dataclass(frozen=True, slots=True)
class FpYahooPlayerMap:
    fp_player_id: str
    yahoo_player_id: int
    match_method: str
    matched_at: datetime


COMMON_ENTITY_NAMES: tuple[str, ...] = (
    "fp_player",
    "fp_adp_snapshot",
    "fp_yahoo_player_map",
)
