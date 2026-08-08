"""Sleeper Fantasy Football public API client.

No authentication required. Fetches player metadata and ADP data from
Sleeper's public endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

SLEEPER_PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"
SLEEPER_PROJECTIONS_URL = "https://api.sleeper.com/projections/nfl"
FANTASY_POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]


class SleeperApiError(RuntimeError):
    """Raised when a Sleeper API request fails."""


@dataclass(frozen=True, slots=True)
class SleeperPlayer:
    """A single Sleeper player with optional ADP data."""

    sleeper_id: str
    full_name: str
    first_name: str
    last_name: str
    position: str
    team: str | None
    age: int | None = None
    years_exp: int | None = None
    college: str | None = None
    status: str | None = None
    adp_half_ppr: float | None = None
    adp_ppr: float | None = None
    adp_std: float | None = None
    adp_2qb: float | None = None
    adp_dynasty: float | None = None


class SleeperClient:
    """Client for Sleeper's public fantasy football API.

    No authentication or account required. All data comes from public
    endpoints.

    Parameters
    ----------
    timeout_seconds : int
        HTTP request timeout (default 60, the players endpoint is large).
    session : requests.Session | None
        Optional pre-configured session for connection pooling.
    """

    def __init__(
        self,
        timeout_seconds: int = 60,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def fetch_players(self) -> dict[str, dict[str, Any]]:
        """Fetch all NFL players from the /players/nfl endpoint.

        Returns a dict keyed by sleeper_player_id with raw player metadata.
        This is a large response (~10MB) containing ~12K players.
        """
        resp = self.session.get(SLEEPER_PLAYERS_URL, timeout=self.timeout_seconds)
        if resp.status_code != 200:
            raise SleeperApiError(
                f"Sleeper players API returned {resp.status_code}: {resp.text[:200]}"
            )
        payload = resp.json()
        if not isinstance(payload, dict) or not all(
            isinstance(player_id, str) and isinstance(player_data, dict)
            for player_id, player_data in payload.items()
        ):
            raise SleeperApiError("Sleeper players API returned an unexpected payload shape.")
        return payload

    def fetch_adp(self, season: int) -> list[dict[str, Any]]:
        """Fetch ADP projections for a given season.

        Requests all fantasy-relevant positions ordered by half-PPR ADP.
        Returns a list of dicts with player_id and stats containing ADP
        values for all scoring formats.

        Parameters
        ----------
        season : int
            NFL season year.
        """
        position_params = "&".join(f"position[]={p}" for p in FANTASY_POSITIONS)
        url = (
            f"{SLEEPER_PROJECTIONS_URL}/{season}"
            f"?season_type=regular&{position_params}&order_by=adp_half_ppr"
        )
        resp = self.session.get(url, timeout=self.timeout_seconds)
        if resp.status_code != 200:
            raise SleeperApiError(
                f"Sleeper projections API returned {resp.status_code}: {resp.text[:200]}"
            )
        payload = resp.json()
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            raise SleeperApiError("Sleeper projections API returned an unexpected payload shape.")
        return payload

    def fetch_players_with_adp(self, season: int) -> list[SleeperPlayer]:
        """Fetch players and ADP, returning merged SleeperPlayer objects.

        Convenience method that calls both endpoints and merges the results
        into a list of SleeperPlayer dataclasses. Only includes players at
        fantasy-relevant positions who have ADP data.

        Parameters
        ----------
        season : int
            NFL season year.

        Returns
        -------
        list[SleeperPlayer]
            Players with ADP data, sorted by adp_half_ppr.
        """
        players_json = self.fetch_players()
        adp_json = self.fetch_adp(season)

        results: list[SleeperPlayer] = []
        for item in adp_json:
            pid = item.get("player_id")
            stats = item.get("stats") or {}
            adp_half = stats.get("adp_half_ppr")
            if adp_half is None:
                continue

            info = players_json.get(str(pid), {})
            position = info.get("position")
            if position not in FANTASY_POSITIONS:
                continue

            results.append(
                SleeperPlayer(
                    sleeper_id=str(pid),
                    full_name=(
                        info.get("full_name")
                        or f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
                    ),
                    first_name=info.get("first_name", ""),
                    last_name=info.get("last_name", ""),
                    position=position,
                    team=info.get("team"),
                    age=info.get("age"),
                    years_exp=info.get("years_exp"),
                    college=info.get("college"),
                    status=info.get("status"),
                    adp_half_ppr=adp_half,
                    adp_ppr=stats.get("adp_ppr"),
                    adp_std=stats.get("adp_std"),
                    adp_2qb=stats.get("adp_2qb"),
                    adp_dynasty=stats.get("adp_dynasty"),
                )
            )

        return sorted(results, key=lambda p: p.adp_half_ppr or 9999)
