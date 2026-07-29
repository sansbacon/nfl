"""ESPN Fantasy Football public API client.

No authentication required. Fetches player projections, rankings, and
ownership data from ESPN's public fantasy football endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import json
from typing import Any

import requests

from nfl.espn_fantasy.constants import (
    ALL_FANTASY_SLOT_IDS,
    DEFAULT_BATCH_SIZE,
    ESPN_API_BASE,
    MAX_PLAYERS,
    POSITION_MAP,
    STAT_MAP,
    STAT_SOURCE_PROJECTED,
    STAT_SPLIT_SEASON,
    STAT_SPLIT_WEEKLY,
    TEAM_MAP,
)


class EspnApiError(RuntimeError):
    """Raised when an ESPN API request fails."""


@dataclass(frozen=True, slots=True)
class EspnPlayer:
    """A single ESPN player with projections and rankings."""

    espn_id: int
    full_name: str
    first_name: str
    last_name: str
    position: str
    team: str
    pro_team_id: int
    rank_standard: int | None = None
    rank_ppr: int | None = None
    auction_value_standard: int | None = None
    auction_value_ppr: int | None = None
    percent_owned: float | None = None
    percent_started: float | None = None
    season_projection: dict[str, float] = field(default_factory=dict)
    season_projected_total: float | None = None
    weekly_projections: dict[int, dict[str, float]] = field(default_factory=dict)
    weekly_projected_totals: dict[int, float] = field(default_factory=dict)


class EspnFantasyClient:
    """Client for ESPN's public fantasy football API.

    No authentication or league membership required. All data comes from
    the public ``leaguedefaults`` endpoint.

    Parameters
    ----------
    timeout_seconds : int
        HTTP request timeout (default 30).
    session : requests.Session | None
        Optional pre-configured session for connection pooling.
    """

    def __init__(
        self,
        timeout_seconds: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def _build_url(self, season: int) -> str:
        return f"{ESPN_API_BASE}/seasons/{season}/segments/0/leaguedefaults"

    def _fetch_batch(
        self,
        season: int,
        *,
        offset: int = 0,
        limit: int = DEFAULT_BATCH_SIZE,
        sort_by: str = "PPR",
    ) -> list[dict[str, Any]]:
        """Fetch a single batch of players from the ESPN API."""
        url = self._build_url(season)
        fantasy_filter = {
            "players": {
                "filterStatsForStatTypeId": {"value": 0},
                "filterStatsForSourceIds": {"value": [STAT_SOURCE_PROJECTED]},
                "sortDraftRanks": {
                    "sortPriority": 100,
                    "sortAsc": True,
                    "value": sort_by,
                },
                "offset": offset,
                "limit": limit,
                "filterSlotIds": {"value": ALL_FANTASY_SLOT_IDS},
            }
        }
        headers = {
            "x-fantasy-filter": json.dumps(fantasy_filter),
            "Accept": "application/json",
        }
        resp = self.session.get(
            url, params={"view": "kona_player_info"}, headers=headers,
            timeout=self.timeout_seconds,
        )
        if resp.status_code != 200:
            raise EspnApiError(
                f"ESPN API returned {resp.status_code}: {resp.text[:200]}"
            )
        data = resp.json()
        # Response is a list of dicts, each with a "players" key
        players_raw: list[dict[str, Any]] = []
        for item in data:
            players_raw.extend(item.get("players", []))
        return players_raw

    def fetch_all_players(
        self,
        season: int,
        *,
        max_players: int = MAX_PLAYERS,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[EspnPlayer]:
        """Fetch all fantasy-relevant players with projections.

        Paginates through the ESPN API in batches and parses each player
        into an EspnPlayer dataclass.

        Parameters
        ----------
        season : int
            NFL season year.
        max_players : int
            Maximum number of players to fetch (default 5000).
        batch_size : int
            Number of players per API call (default 1000).

        Returns
        -------
        list[EspnPlayer]
            Parsed player objects with projections and rankings.
        """
        all_players: list[EspnPlayer] = []
        offset = 0

        while offset < max_players:
            batch = self._fetch_batch(season, offset=offset, limit=batch_size)
            if not batch:
                break
            for raw in batch:
                player = self._parse_player(raw)
                if player is not None:
                    all_players.append(player)
            offset += batch_size

        return all_players

    def _parse_player(self, raw: dict[str, Any]) -> EspnPlayer | None:
        """Parse a raw ESPN API player dict into an EspnPlayer."""
        player_data = raw.get("player")
        if player_data is None:
            return None

        espn_id = player_data.get("id")
        if espn_id is None:
            return None

        position_id = player_data.get("defaultPositionId", 0)
        position = POSITION_MAP.get(position_id, "UNK")

        pro_team_id = player_data.get("proTeamId", 0)
        team = TEAM_MAP.get(pro_team_id, "FA")

        # Rankings
        ranks = player_data.get("draftRanksByRankType", {})
        rank_standard = ranks.get("STANDARD", {}).get("rank")
        rank_ppr = ranks.get("PPR", {}).get("rank")
        auction_standard = ranks.get("STANDARD", {}).get("auctionValue")
        auction_ppr = ranks.get("PPR", {}).get("auctionValue")

        # Ownership
        ownership = player_data.get("ownership", {})
        pct_owned = ownership.get("percentOwned")
        pct_started = ownership.get("percentStarted")

        # Projections
        season_proj: dict[str, float] = {}
        season_total: float | None = None
        weekly_projs: dict[int, dict[str, float]] = {}
        weekly_totals: dict[int, float] = {}

        for stat_entry in player_data.get("stats", []):
            if stat_entry.get("statSourceId") != STAT_SOURCE_PROJECTED:
                continue

            split_type = stat_entry.get("statSplitTypeId")
            scoring_period = stat_entry.get("scoringPeriodId", 0)
            applied_total = stat_entry.get("appliedTotal", 0.0)
            raw_stats = stat_entry.get("stats", {})

            # Map numeric stat IDs to named columns
            mapped_stats = {}
            for stat_id, value in raw_stats.items():
                col_name = STAT_MAP.get(stat_id)
                if col_name:
                    mapped_stats[col_name] = round(value, 2)

            if split_type == STAT_SPLIT_SEASON and scoring_period == 0:
                season_proj = mapped_stats
                season_total = round(applied_total, 2)
            elif split_type == STAT_SPLIT_WEEKLY and scoring_period > 0:
                weekly_projs[scoring_period] = mapped_stats
                weekly_totals[scoring_period] = round(applied_total, 2)

        return EspnPlayer(
            espn_id=espn_id,
            full_name=player_data.get("fullName", ""),
            first_name=player_data.get("firstName", ""),
            last_name=player_data.get("lastName", ""),
            position=position,
            team=team,
            pro_team_id=pro_team_id,
            rank_standard=rank_standard,
            rank_ppr=rank_ppr,
            auction_value_standard=auction_standard,
            auction_value_ppr=auction_ppr,
            percent_owned=pct_owned,
            percent_started=pct_started,
            season_projection=season_proj,
            season_projected_total=season_total,
            weekly_projections=weekly_projs,
            weekly_projected_totals=weekly_totals,
        )
