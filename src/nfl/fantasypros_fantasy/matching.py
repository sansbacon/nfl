"""FantasyPros to Yahoo crosswalk matching utilities."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from nfl.fantasypros_fantasy.validation import validate


def _norm(text: str | None) -> str:
    raw = (text or "").strip().lower()
    return re.sub(r"[^a-z0-9]", "", raw)


def _name_parts(full_name: str | None) -> tuple[str, str]:
    parts = (full_name or "").strip().split(" ", 1)
    first = parts[0] if parts else ""
    last = parts[1] if len(parts) > 1 else ""
    return first, last


def _adp_rank_map(adp_rows: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in adp_rows:
        player_id = str(row.get("fp_player_id", ""))
        rank = row.get("rank")
        if not player_id:
            continue
        if not isinstance(rank, int):
            continue
        prev = out.get(player_id)
        if prev is None or rank < prev:
            out[player_id] = rank
    return out


def build_fp_yahoo_crosswalk(
    fp_players: list[dict[str, Any]],
    yahoo_players: list[dict[str, Any]],
    adp_rows: list[dict[str, Any]] | None = None,
    matched_at: datetime | None = None,
) -> list[dict[str, Any]]:
    adp_rank = _adp_rank_map(adp_rows or [])
    ts = matched_at or datetime.now(timezone.utc)

    exact_candidates: list[dict[str, Any]] = []
    fuzzy_candidates: list[dict[str, Any]] = []

    for fp in fp_players:
        fp_id = str(fp.get("fp_player_id", ""))
        fp_name = _norm(str(fp.get("full_name", "")))
        fp_pos = _norm(str(fp.get("position", "")))
        fp_first = _norm(str(fp.get("first_name", "")))
        fp_last = _norm(str(fp.get("last_name", "")))
        if not fp_first or not fp_last:
            first, last = _name_parts(str(fp.get("full_name", "")))
            fp_first = fp_first or _norm(first)
            fp_last = fp_last or _norm(last)

        for yh in yahoo_players:
            yahoo_player_id = yh.get("yahoo_player_id", yh.get("player_id"))
            if yahoo_player_id is None:
                continue
            yh_name = _norm(str(yh.get("full_name", "")))
            yh_pos = _norm(str(yh.get("display_position", "")))
            yh_first = _norm(str(yh.get("first_name", "")))
            yh_last = _norm(str(yh.get("last_name", "")))

            candidate = {
                "fp_player_id": fp_id,
                "yahoo_player_id": int(yahoo_player_id),
                "adp_rank": adp_rank.get(fp_id, 9999),
            }
            if fp_name and yh_name and fp_name == yh_name:
                exact_candidates.append({**candidate, "match_method": "exact", "method_priority": 1})
                continue

            if fp_last and yh_last and fp_last == yh_last and fp_pos and yh_pos and fp_pos == yh_pos:
                if fp_first[:3] and yh_first[:3] and fp_first[:3] == yh_first[:3]:
                    fuzzy_candidates.append({**candidate, "match_method": "fuzzy", "method_priority": 2})

    exact_fp_ids = {c["fp_player_id"] for c in exact_candidates}
    candidates = exact_candidates + [c for c in fuzzy_candidates if c["fp_player_id"] not in exact_fp_ids]

    best_by_yahoo: dict[int, dict[str, Any]] = {}
    for c in sorted(candidates, key=lambda x: (x["method_priority"], x["adp_rank"], x["fp_player_id"])):
        yh_id = c["yahoo_player_id"]
        if yh_id not in best_by_yahoo:
            best_by_yahoo[yh_id] = c

    best_by_fp: dict[str, dict[str, Any]] = {}
    for c in sorted(best_by_yahoo.values(), key=lambda x: (x["method_priority"], x["adp_rank"], x["yahoo_player_id"])):
        fp_id = c["fp_player_id"]
        if fp_id not in best_by_fp:
            best_by_fp[fp_id] = c

    output = [
        {
            "fp_player_id": row["fp_player_id"],
            "yahoo_player_id": row["yahoo_player_id"],
            "match_method": row["match_method"],
            "matched_at": ts,
        }
        for row in best_by_fp.values()
    ]

    if output:
        validate(output, entity="fp_yahoo_player_map", sport="nfl")
    return sorted(output, key=lambda r: (r["match_method"], r["fp_player_id"], r["yahoo_player_id"]))
