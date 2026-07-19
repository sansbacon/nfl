"""nflreadpy wrapper adapters for NFLverse ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from nfl.nflverse_fantasy.validation import validate


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
    raise TypeError("Unsupported nflreadpy payload type")


def _add_metadata(dataset: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    loaded_at = datetime.now(timezone.utc).isoformat()
    out: list[dict[str, Any]] = []
    for row in rows:
        row_copy = dict(row)
        payload_hash = hashlib.sha256(
            json.dumps(row_copy, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        row_copy["_record_hash"] = payload_hash
        row_copy["_dataset"] = dataset
        row_copy["_loaded_at"] = loaded_at
        out.append(row_copy)
    return out


@dataclass(frozen=True, slots=True)
class NflverseApiClient:
    validate_contracts: bool = True

    def _load_dataset(self, loader_name: str, dataset: str, **kwargs: Any) -> list[dict[str, Any]]:
        try:
            import nflreadpy
        except ModuleNotFoundError as exc:
            raise RuntimeError("nflreadpy is required for nflverse ingestion.") from exc

        loader = getattr(nflreadpy, loader_name)
        try:
            raw = loader(**{k: v for k, v in kwargs.items() if v is not None})
        except TypeError:
            raw = loader()

        rows = _to_dicts(raw)
        rows = _add_metadata(dataset, rows)
        if self.validate_contracts and rows:
            validate(rows, entity=dataset)
        return rows

    def get_pbp(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_pbp", "pbp", seasons=seasons)

    def get_player_stats(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_player_stats", "player_stats", seasons=seasons)

    def get_team_stats(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_team_stats", "team_stats", seasons=seasons)

    def get_schedules(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_schedules", "schedules", seasons=seasons)

    def get_players(self) -> list[dict[str, Any]]:
        return self._load_dataset("load_players", "players")

    def get_rosters(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_rosters", "rosters", seasons=seasons)

    def get_rosters_weekly(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_rosters_weekly", "rosters_weekly", seasons=seasons)

    def get_snap_counts(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_snap_counts", "snap_counts", seasons=seasons)

    def get_nextgen_stats(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_nextgen_stats", "nextgen_stats", seasons=seasons)

    def get_ftn_charting(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_ftn_charting", "ftn_charting", seasons=seasons)

    def get_participation(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_participation", "participation", seasons=seasons)

    def get_draft_picks(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_draft_picks", "draft_picks", seasons=seasons)

    def get_injuries(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_injuries", "injuries", seasons=seasons)

    def get_contracts(self) -> list[dict[str, Any]]:
        return self._load_dataset("load_contracts", "contracts")

    def get_officials(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_officials", "officials", seasons=seasons)

    def get_combine(self) -> list[dict[str, Any]]:
        return self._load_dataset("load_combine", "combine")

    def get_depth_charts(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_depth_charts", "depth_charts", seasons=seasons)

    def get_trades(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_trades", "trades", seasons=seasons)

    def get_ff_playerids(self) -> list[dict[str, Any]]:
        return self._load_dataset("load_ff_playerids", "ff_playerids")

    def get_ff_rankings(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_ff_rankings", "ff_rankings", seasons=seasons)

    def get_ff_opportunity(self, seasons: list[int] | None = None) -> list[dict[str, Any]]:
        return self._load_dataset("load_ff_opportunity", "ff_opportunity", seasons=seasons)
