"""FantasyPros extraction and normalization client."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from nfl.fantasypros_fantasy.validation import validate

FP_BASE_URL = "https://www.fantasypros.com/nfl"
FP_PARTNERS_API = "https://partners.fantasypros.com/api/v1"
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


def _safe_float(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
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

    def _build_adp_csv_url(self, season: int) -> str:
        return (
            f"{FP_PARTNERS_API}/consensus-rankings.php"
            f"?sport=NFL&year={season}&week=0&id=0&position=ALL&type=ADP&scoring=PPR&export=xls"
        )

    def fetch_adp_page(self, season: int) -> str:
        url = self._build_adp_url(season)
        response = self.session.get(url, headers=FP_HEADERS, timeout=self.timeout_seconds)
        response.raise_for_status()
        return str(response.text)

    def fetch_adp_csv(self, season: int) -> str:
        """Fetch full ADP data from the FantasyPros partners CSV export API."""
        url = self._build_adp_csv_url(season)
        response = self.session.get(url, headers=FP_HEADERS, timeout=self.timeout_seconds)
        response.raise_for_status()
        return str(response.text)

    def parse_adp_csv(
        self,
        csv_text: str,
        season: int,
        effective_date: date | None = None,
    ) -> AdpPageData:
        """Parse CSV export into AdpPageData (same schema as HTML parser)."""
        import csv as _csv

        lines = csv_text.splitlines()
        # Skip metadata header lines (first 4 lines are title/blank)
        data_start = 0
        for i, line in enumerate(lines):
            if line.strip().lower().startswith("rank,"):
                data_start = i
                break

        reader = _csv.DictReader(lines[data_start:])
        effective = effective_date or date.today()
        player_rows: list[dict[str, Any]] = []
        adp_rows: list[dict[str, Any]] = []

        for idx, row in enumerate(reader):
            full_name = (row.get("Player Name") or "").strip()
            if not full_name:
                continue
            team = (row.get("Team") or "").strip().upper()
            position = (row.get("Position") or "").strip().upper()
            first_name, last_name = _normalize_name(full_name)

            # Derive a stable player ID from name + team
            slug = re.sub(r"[^a-z0-9]+", "-", full_name.lower()).strip("-")
            fp_player_id = slug

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

            rank = _safe_int(row.get("Rank")) or (idx + 1)
            high = _safe_int(row.get("Min"))
            low = _safe_int(row.get("Max"))
            stdev = _safe_float(row.get("STD Dev"))
            # Use average of min/max as ADP estimate
            adp = (
                round((high + low) / 2.0, 1)
                if high is not None and low is not None
                else float(rank)
            )

            round_num = int((adp - 1) // 12) + 1
            pick_num = int((adp - 1) % 12) + 1
            adp_formatted = f"{round_num}.{pick_num:02d}"

            adp_rows.append(
                {
                    "fp_player_id": fp_player_id,
                    "season": season,
                    "rank": rank,
                    "adp": adp,
                    "adp_espn": None,
                    "adp_sleeper": None,
                    "adp_cbs": None,
                    "adp_nfl": None,
                    "adp_rtsports": None,
                    "adp_fantrax": None,
                    "adp_realtime": None,
                    "adp_formatted": adp_formatted,
                    "high": high,
                    "low": low,
                    "stdev": stdev,
                    "bye_week": None,
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

    def parse_adp_page(
        self, html: str, season: int, effective_date: date | None = None
    ) -> AdpPageData:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table", {"id": "data"})
        if table:
            return self._parse_legacy_adp_table(
                table=table,
                season=season,
                effective_date=effective_date,
            )

        report_config = self._extract_report_config(soup)
        if report_config is not None:
            return self._parse_report_config_adp(
                report_config=report_config,
                season=season,
                effective_date=effective_date,
            )

        raise ExtractionError(
            "Could not find FantasyPros ADP payload (legacy table or reportConfig JSON)."
        )

    def _extract_report_config(self, soup: BeautifulSoup) -> dict[str, Any] | None:
        for script in soup.find_all("script"):
            script_text = (
                script.string
                if isinstance(script.string, str)
                else script.get_text("", strip=False)
            )
            if not script_text or "window.FP.reportConfig" not in script_text:
                continue

            marker = "window.FP.reportConfig"
            marker_idx = script_text.find(marker)
            if marker_idx < 0:
                continue

            assign_idx = script_text.find("=", marker_idx)
            if assign_idx < 0:
                continue

            start_idx = script_text.find("{", assign_idx)
            if start_idx < 0:
                continue

            depth = 0
            end_idx = -1
            for idx in range(start_idx, len(script_text)):
                char = script_text[idx]
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end_idx = idx
                        break

            if end_idx < 0:
                continue

            json_blob = script_text[start_idx : end_idx + 1]

            try:
                payload = json.loads(json_blob)
            except json.JSONDecodeError:
                continue

            if isinstance(payload, dict) and isinstance(payload.get("table"), dict):
                return payload

        return None

    def _parse_report_config_adp(
        self,
        report_config: dict[str, Any],
        season: int,
        effective_date: date | None,
    ) -> AdpPageData:
        table_data = report_config.get("table")
        if not isinstance(table_data, dict):
            raise ExtractionError("FantasyPros reportConfig payload is missing table data.")

        rows = table_data.get("rows")
        if not isinstance(rows, list) or not rows:
            return AdpPageData(players=[], adp_rows=[])

        raw_fields = table_data.get("fields")
        fields: list[Any] = raw_fields if isinstance(raw_fields, list) else []
        source_key_by_label: dict[str, str] = {}
        for field in fields:
            if not isinstance(field, dict):
                continue
            label = field.get("label")
            key = field.get("key")
            if isinstance(label, str) and isinstance(key, str):
                source_key_by_label[label.strip().upper()] = key

        adp_key = source_key_by_label.get("AVG", "avg")
        realtime_key = source_key_by_label.get("REAL-TIME", "realtime")
        platform_keys = {
            "adp_espn": source_key_by_label.get("ESPN"),
            "adp_sleeper": source_key_by_label.get("SLEEPER"),
            "adp_cbs": source_key_by_label.get("CBS"),
            "adp_nfl": source_key_by_label.get("NFL"),
            "adp_rtsports": source_key_by_label.get("RTSPORTS"),
            "adp_fantrax": source_key_by_label.get("FANTRAX"),
        }

        effective = effective_date or date.today()
        player_rows: list[dict[str, Any]] = []
        adp_rows: list[dict[str, Any]] = []

        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                continue

            player_data = row.get("player")
            if not isinstance(player_data, dict):
                continue

            full_name = str(player_data.get("name") or "").strip()
            first_name, last_name = _normalize_name(full_name)

            player_url = str(player_data.get("url") or "")
            url_match = re.search(r"/nfl/players/([^/.]+)", player_url)
            fp_player_id = url_match.group(1) if url_match else f"unknown_{idx}"

            team_text = str(player_data.get("team") or "").strip()
            team_match = re.match(r"^([A-Za-z]+)\s*\((\d+)\)$", team_text)
            if team_match:
                team = team_match.group(1).upper()
                bye_week = _safe_int(team_match.group(2))
            else:
                team = team_text.upper()
                bye_week = None

            pos_text = str(row.get("pos") or "").strip()
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

            rank = _safe_int(str(row.get("rank"))) or idx + 1
            adp = _safe_float(row.get(adp_key))
            if adp is None:
                continue

            values: dict[str, float | None] = {}
            for target_name, source_key in platform_keys.items():
                values[target_name] = _safe_float(row.get(source_key)) if source_key else None

            adp_realtime = _safe_float(row.get(realtime_key))

            platforms = [
                values["adp_espn"],
                values["adp_sleeper"],
                values["adp_cbs"],
                values["adp_nfl"],
                values["adp_rtsports"],
                values["adp_fantrax"],
            ]
            valid_platforms = [v for v in platforms if v is not None]
            high = int(min(valid_platforms)) if valid_platforms else None
            low = int(max(valid_platforms)) if valid_platforms else None

            stdev = None
            if len(valid_platforms) >= 2:
                mean = sum(valid_platforms) / len(valid_platforms)
                variance = sum((x - mean) ** 2 for x in valid_platforms) / len(valid_platforms)
                stdev = round(variance**0.5, 2)

            round_num = int((adp - 1) // 12) + 1
            pick_num = int((adp - 1) % 12) + 1
            adp_formatted = f"{round_num}.{pick_num:02d}"

            adp_rows.append(
                {
                    "fp_player_id": fp_player_id,
                    "season": season,
                    "rank": rank,
                    "adp": adp,
                    "adp_espn": values["adp_espn"],
                    "adp_sleeper": values["adp_sleeper"],
                    "adp_cbs": values["adp_cbs"],
                    "adp_nfl": values["adp_nfl"],
                    "adp_rtsports": values["adp_rtsports"],
                    "adp_fantrax": values["adp_fantrax"],
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

    def _parse_legacy_adp_table(
        self, table: Any, season: int, effective_date: date | None
    ) -> AdpPageData:

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
                stdev = round(variance**0.5, 2)

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

    def _fetch_and_parse(self, season: int, effective_date: date | None = None) -> AdpPageData:
        """Fetch ADP data, preferring CSV export (full data) over HTML (registration-gated)."""
        try:
            csv_text = self.fetch_adp_csv(season)
            result = self.parse_adp_csv(csv_text, season=season, effective_date=effective_date)
            if result.players:
                return result
        except Exception:
            pass
        # Fallback to HTML scraping (may return limited rows due to registrationFence)
        html = self.fetch_adp_page(season)
        return self.parse_adp_page(html, season=season, effective_date=effective_date)

    def get_players(self, season: int) -> list[dict[str, Any]]:
        return self._fetch_and_parse(season).players

    def get_adp_snapshots(
        self, season: int, effective_date: date | None = None
    ) -> list[dict[str, Any]]:
        return self._fetch_and_parse(season, effective_date=effective_date).adp_rows

    def parse_adp_volume_csv(
        self,
        file_path: str | Path,
        season: int,
        effective_date: date | None = None,
    ) -> AdpPageData:
        """Parse a FantasyPros ADP CSV file downloaded to a local path or UC Volume.

        This handles the CSV format produced by FantasyPros' rankings export
        (e.g. ``FantasyPros_2024_Overall_ADP_Rankings.csv``) that users
        download and store in Unity Catalog Volumes.  The format differs from
        the web API export: it uses a ``"Player (Bye)"`` column that bundles
        name, team abbreviation, and bye week together.

        Parameters
        ----------
        file_path:
            Path to the CSV file (local path or UC Volume path such as
            ``/Volumes/nfl/default/nfl_volume/FantasyPros_2024_...csv``).
        season:
            NFL season year to tag on returned records.
        effective_date:
            Override for the snapshot effective date.  Defaults to today.

        Returns
        -------
        AdpPageData
            Parsed player and ADP records in the standard library schema.

        Examples
        --------
        .. code-block:: python

            from nfl.fantasypros_fantasy.api import FantasyProsApiClient

            client = FantasyProsApiClient()
            data = client.parse_adp_volume_csv(
                "/Volumes/nfl/default/nfl_volume/FantasyPros_2024_Overall_ADP_Rankings.csv",
                season=2024,
            )
            print(len(data.players), "players parsed")
        """
        import polars as _pl

        path = Path(file_path)
        df = _pl.read_csv(str(path), truncate_ragged_lines=True, null_values=["—"])

        player_col = "Player (Bye)" if "Player (Bye)" in df.columns else "Player"

        # Strip bye week annotation, e.g. "Christian McCaffrey   SF (9)" → "Christian McCaffrey   SF"
        df = df.with_columns(
            _pl.col(player_col)
            .str.replace(r"\s*\(\d+\)\s*$", "")
            .str.strip_chars()
            .alias("_cleaned")
        )
        # Extract trailing 2-3-letter team abbreviation, then strip it from the name
        df = df.with_columns(
            _pl.col("_cleaned").str.extract(r"\s+([A-Z]{2,3})$").alias("team"),
            _pl.col("_cleaned")
            .str.replace(r"\s+[A-Z]{2,3}$", "")
            .str.strip_chars()
            .alias("player_name"),
        )
        # Strip positional rank number, e.g. "RB1" → "RB"
        pos_col = "POS" if "POS" in df.columns else ("Pos" if "Pos" in df.columns else None)
        if pos_col:
            df = df.with_columns(
                _pl.col(pos_col).str.extract(r"^([A-Z]+)").alias("position")
            )
        else:
            df = df.with_columns(_pl.lit(None).cast(_pl.String).alias("position"))

        effective = effective_date or date.today()
        player_rows: list[dict[str, Any]] = []
        adp_rows: list[dict[str, Any]] = []

        rank_col = "Rank" if "Rank" in df.columns else None
        adp_col = "AVG" if "AVG" in df.columns else None

        platform_map = {
            "ESPN": "adp_espn",
            "Sleeper": "adp_sleeper",
            "CBS": "adp_cbs",
            "NFL": "adp_nfl",
            "RTSports": "adp_rtsports",
            "Fantrax": "adp_fantrax",
        }

        for row in df.iter_rows(named=True):
            name = str(row.get("player_name") or "").strip()
            if not name:
                continue
            first_name, last_name = _normalize_name(name)
            team = str(row.get("team") or "").strip().upper()
            position = str(row.get("position") or "").strip().upper()

            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            fp_player_id = f"{slug}_{team.lower()}" if team else slug

            player_rows.append(
                {
                    "fp_player_id": fp_player_id,
                    "full_name": name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "position": position,
                    "team": team,
                }
            )

            rank = _safe_int(str(row.get(rank_col) or "")) if rank_col else None
            if rank is None:
                rank = len(player_rows)
            adp = _safe_float(row.get(adp_col)) if adp_col else float(rank)
            if adp is None:
                adp = float(rank)

            platform_values: dict[str, float | None] = {}
            for csv_col, adp_field in platform_map.items():
                platform_values[adp_field] = _safe_float(row.get(csv_col))

            valid_platforms = [v for v in platform_values.values() if v is not None]
            high = int(min(valid_platforms)) if valid_platforms else None
            low = int(max(valid_platforms)) if valid_platforms else None

            stdev: float | None = None
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
                    "adp_espn": platform_values.get("adp_espn"),
                    "adp_sleeper": platform_values.get("adp_sleeper"),
                    "adp_cbs": platform_values.get("adp_cbs"),
                    "adp_nfl": platform_values.get("adp_nfl"),
                    "adp_rtsports": platform_values.get("adp_rtsports"),
                    "adp_fantrax": platform_values.get("adp_fantrax"),
                    "adp_realtime": None,
                    "adp_formatted": adp_formatted,
                    "high": high,
                    "low": low,
                    "stdev": stdev,
                    "bye_week": None,
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
