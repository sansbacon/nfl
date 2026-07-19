"""Canonical registry loading from nflreadpy-backed sources."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from nfl.entity_standardization.normalize import ALLOWED_POSITIONS, normalize_player_name, normalize_position, normalize_team_code


@dataclass(frozen=True, slots=True)
class CanonicalRegistry:
    players: list[dict[str, Any]]
    teams: list[dict[str, Any]]
    positions: list[dict[str, Any]]
    source_to_canonical_map: list[dict[str, Any]]


def _to_dicts(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [dict(row) for row in payload if isinstance(row, dict)]
    if hasattr(payload, "to_dict"):
        try:
            rows = payload.to_dict("records")
            if isinstance(rows, list):
                return [dict(row) for row in rows if isinstance(row, dict)]
        except TypeError:
            pass
    raise TypeError("Unsupported tabular payload type from nflreadpy loader")


def _pick_canonical_player_id(row: dict[str, Any]) -> str:
    for key in ("gsis_id", "player_id", "nfl_id", "pfr_id"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _player_display_name(row: dict[str, Any]) -> str:
    display_name = row.get("display_name") or row.get("player_name")
    if isinstance(display_name, str) and display_name.strip():
        return display_name.strip()
    first_name = str(row.get("first_name") or "").strip()
    last_name = str(row.get("last_name") or "").strip()
    return f"{first_name} {last_name}".strip()


def _infer_source_system(column_name: str) -> str | None:
    lowered = column_name.lower()
    mapping = {
        "yahoo": "yahoo",
        "fantasypros": "fantasypros",
        "espn": "espn",
        "sleeper": "sleeper",
        "fleaflicker": "fleaflicker",
        "mfl": "mfl",
        "cbs": "cbs",
    }
    for key, source in mapping.items():
        if key in lowered:
            return source
    return None


class CanonicalRegistryLoader:
    def load_registry(self) -> CanonicalRegistry:
        try:
            import nflreadpy
        except ModuleNotFoundError as exc:
            raise RuntimeError("nflreadpy is required to load canonical registries.") from exc

        players_raw = _to_dicts(nflreadpy.load_players())
        ff_ids_raw = _to_dicts(nflreadpy.load_ff_playerids())
        schedules_raw = _to_dicts(nflreadpy.load_schedules())
        source_version = datetime.now(timezone.utc).isoformat()

        players: list[dict[str, Any]] = []
        player_by_id: dict[str, dict[str, Any]] = {}

        for row in players_raw:
            canonical_player_id = _pick_canonical_player_id(row)
            if not canonical_player_id:
                continue

            display_name = _player_display_name(row)
            first_name = str(row.get("first_name") or "").strip()
            last_name = str(row.get("last_name") or "").strip()
            current_team = normalize_team_code(str(row.get("recent_team") or row.get("team") or ""))
            primary_position = normalize_position(str(row.get("position") or ""))
            if primary_position not in ALLOWED_POSITIONS:
                primary_position = ""

            aliases = sorted(
                {
                    normalize_player_name(display_name),
                    normalize_player_name(f"{first_name} {last_name}"),
                    normalize_player_name(f"{last_name} {first_name}"),
                }
                - {""}
            )

            record = {
                "canonical_player_id": canonical_player_id,
                "display_name": display_name,
                "first_name": first_name,
                "last_name": last_name,
                "current_team": current_team,
                "primary_position": primary_position,
                "aliases": aliases,
                "source_version": source_version,
            }
            players.append(record)
            player_by_id[canonical_player_id] = record

        source_to_canonical_map: list[dict[str, Any]] = []
        for row in ff_ids_raw:
            canonical_player_id = _pick_canonical_player_id(row)
            if not canonical_player_id or canonical_player_id not in player_by_id:
                continue

            cross_source_ids: dict[str, str] = {}
            for key, value in row.items():
                if key in {"gsis_id", "player_id", "nfl_id", "pfr_id"}:
                    continue
                source_system = _infer_source_system(key)
                if source_system is None or value in (None, ""):
                    continue
                source_entity_id = str(value)
                cross_source_ids[source_system] = source_entity_id
                source_to_canonical_map.append(
                    {
                        "source_system": source_system,
                        "source_entity_id": source_entity_id,
                        "canonical_player_id": canonical_player_id,
                        "provenance": "nflreadpy.load_ff_playerids",
                        "valid_from": None,
                        "valid_to": None,
                    }
                )
            player_by_id[canonical_player_id]["cross_source_ids"] = cross_source_ids

        for record in players:
            record.setdefault("cross_source_ids", {})

        team_codes = {
            normalize_team_code(str(row.get("home_team") or ""))
            for row in schedules_raw
        } | {
            normalize_team_code(str(row.get("away_team") or ""))
            for row in schedules_raw
        }
        team_codes = {code for code in team_codes if code}

        teams = [
            {
                "canonical_team_id": code,
                "canonical_team_name": code,
                "canonical_team_abbr": code,
                "aliases": [code],
                "source_version": source_version,
                "team_code_authority": "load_schedules",
            }
            for code in sorted(team_codes)
        ]

        positions = [
            {
                "canonical_position_id": code,
                "canonical_position_code": code,
                "aliases": [code],
            }
            for code in ALLOWED_POSITIONS
        ]

        return CanonicalRegistry(
            players=players,
            teams=teams,
            positions=positions,
            source_to_canonical_map=source_to_canonical_map,
        )
