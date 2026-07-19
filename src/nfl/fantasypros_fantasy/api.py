"""FantasyPros extraction and normalization client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from nfl.fantasypros_fantasy.validation import validate

FP_BASE_URL = "https://www.fantasypros.com/nfl"
FP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
}


class ExtractionError(RuntimeError):
    """Raised when FantasyPros page extraction or parsing fails."""


@dataclass(frozen=True, slots=True)
class AdpPageData:
    players: list[dict[str, Any]]
    adp_rows: list[dict[str, Any]]


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.replace(",", "").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(" ", 1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name, last_name


def _extract_player_id_from_cell(player_cell: Any, row_idx: int) -> str:
    player_link = player_cell.find("a", class_="player-name") if player_cell else None
    if player_link:
        href = player_link.get("href", "")
        match = re.search(r"/nfl/players/([^/.]+)", href)
        if match:
            return match.group(1)
        for cls in player_link.get("class", []):
            if isinstance(cls, str) and cls.startswith("fp-id-"):
                return cls.replace("fp-id-", "")
    return f"unknown_{row_idx}"


def _extract_team_and_bye(player_cell: Any) -> tuple[str, int | None]:
    smalls = player_cell.find_all("small") if player_cell else []
    team = smalls[0].get_text(strip=True).upper() if smalls else ""
    bye_week = None
    if len(smalls) >= 2:
        bye_week = _safe_int(smalls[1].get_text(strip=True).strip("()"))
    return team, bye_week


class FantasyProsApiClient:
    def __init__(
        self,
        timeout_seconds: int = 30,
        validate_contracts: bool = True,
        session: Any | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.validate_contracts = validate_contracts
        self.session = session or requests.Session()

    def _build_adp_url(self, season: int) -> str:
        current_year = date.today().year
        if season < current_year:
            return f"{FP_BASE_URL}/adp/ppr-overall.php?year={season}"
        return f"{FP_BASE_URL}/adp/ppr-overall.php"

    def fetch_adp_page(self, season: int) -> str:
        url = self._build_adp_url(season)
        response = self.session.get(url, headers=FP_HEADERS, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.text

    def parse_adp_page(self, html: str, season: int, effective_date: date | None = None) -> AdpPageData:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table", {"id": "data"})
        if not table:
            raise ExtractionError("Could not find FantasyPros ADP table with id='data'.")

        tbody = table.find("tbody")
        if not tbody:
            raise ExtractionError("Could not find table body for FantasyPros ADP table.")

        rows = tbody.find_all("tr")
        if not rows:
            return AdpPageData(players=[], adp_rows=[])

        effective = effective_date or date.today()
        player_rows: list[dict[str, Any]] = []
        adp_rows: list[dict[str, Any]] = []

        for idx, row in enumerate(rows):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            player_cell = cells[1]
            fp_player_id = _extract_player_id_from_cell(player_cell, idx)
            player_link = player_cell.find("a", class_="player-name")
            full_name = player_link.get_text(strip=True) if player_link else ""
            first_name, last_name = _normalize_name(full_name)
            team, bye_week = _extract_team_and_bye(player_cell)

            pos_text = cells[2].get_text(strip=True)
            position = re.sub(r"\d+$", "", pos_text).upper()

            player_rows.append(
                {
                    "fp_player_id": fp_player_id,
                    "full_name": full_name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "position": position,
                    "team": team,
                }
            )

            cell_texts = [c.get_text(strip=True) for c in cells]
            num_cols = len(cell_texts)

            rank = _safe_int(cell_texts[0]) or idx + 1
            if num_cols >= 10:
                adp_espn = _safe_float(cell_texts[3])
                adp_sleeper = _safe_float(cell_texts[4])
                adp_cbs = _safe_float(cell_texts[5])
                adp_nfl = _safe_float(cell_texts[6])
                adp_rtsports = _safe_float(cell_texts[7])
                adp_fantrax = _safe_float(cell_texts[8])
                adp = _safe_float(cell_texts[9])
                adp_realtime = _safe_float(cell_texts[10]) if num_cols > 10 else None
            else:
                adp_espn = None
                adp_sleeper = None
                adp_cbs = None
                adp_nfl = None
                adp_rtsports = None
                adp_fantrax = None
                adp = _safe_float(cell_texts[3])
                adp_realtime = None

            if adp is None:
                continue

            platforms = [adp_espn, adp_sleeper, adp_cbs, adp_nfl, adp_rtsports, adp_fantrax]
            valid_platforms = [v for v in platforms if v is not None]
            high = int(min(valid_platforms)) if valid_platforms else None
            low = int(max(valid_platforms)) if valid_platforms else None

            stdev = None
            if len(valid_platforms) >= 2:
                mean = sum(valid_platforms) / len(valid_platforms)
                variance = sum((x - mean) ** 2 for x in valid_platforms) / len(valid_platforms)
                stdev = round(variance ** 0.5, 2)

            round_num = int((adp - 1) // 12) + 1
            pick_num = int((adp - 1) % 12) + 1
            adp_formatted = f"{round_num}.{pick_num:02d}"

            adp_rows.append(
                {
                    "fp_player_id": fp_player_id,
                    "season": season,
                    "rank": rank,
                    "adp": adp,
                    "adp_espn": adp_espn,
                    "adp_sleeper": adp_sleeper,
                    "adp_cbs": adp_cbs,
                    "adp_nfl": adp_nfl,
                    "adp_rtsports": adp_rtsports,
                    "adp_fantrax": adp_fantrax,
                    "adp_realtime": adp_realtime,
                    "adp_formatted": adp_formatted,
                    "high": high,
                    "low": low,
                    "stdev": stdev,
                    "bye_week": bye_week,
                    "effective_date": effective,
                    "end_date": None,
                    "is_current": True,
                }
            )

        if self.validate_contracts and player_rows:
            validate(player_rows, entity="fp_player")
        if self.validate_contracts and adp_rows:
            validate(adp_rows, entity="fp_adp_snapshot", sport="nfl")

        return AdpPageData(players=player_rows, adp_rows=adp_rows)

    def get_players(self, season: int) -> list[dict[str, Any]]:
        html = self.fetch_adp_page(season)
        return self.parse_adp_page(html, season=season).players

    def get_adp_snapshots(self, season: int, effective_date: date | None = None) -> list[dict[str, Any]]:
        html = self.fetch_adp_page(season)
        return self.parse_adp_page(html, season=season, effective_date=effective_date).adp_rows
