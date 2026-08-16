"""Fantasy Points player matching to canonical crosswalk.

Single-stage join (simpler than FL since FPTS has no HTML player IDs):
- Parsed players → canonical crosswalk (``dim_ff_player_ids``) via
  ``normalize_name`` to obtain ``mfl_id``.

Match strategy:
1. Exact (normalized_name, position) match.
2. Fallback: normalized_name only.
3. Unmatched: mfl_id = None (logged for manual review).
"""

from __future__ import annotations

from typing import Any

from nfl.common.matching import normalize_name


def build_player_map(
    parsed_records: list[dict[str, Any]],
    crosswalk_records: list[dict[str, Any]],
    *,
    rank_threshold: int = 180,
) -> list[dict[str, Any]]:
    """Build the fpts_player_map by matching FPTS players to the crosswalk.

    Only attempts crosswalk matching for players with
    overall_rank <= rank_threshold.

    Parameters
    ----------
    parsed_records : list[dict]
        Output of ``parse_rankings_csv``.
    crosswalk_records : list[dict]
        Records from ``dim_ff_player_ids`` with at least 'merge_name',
        'mfl_id', 'position' columns.
    rank_threshold : int
        Only match players ranked at or below this threshold (default 180).

    Returns
    -------
    list[dict[str, Any]]
        Player map records with keys: player, position, team,
        mfl_id, match_method.
    """
    # Build crosswalk lookups
    xwalk_by_name_pos: dict[tuple[str, str], str] = {}
    xwalk_by_name: dict[str, str] = {}
    for xw in crosswalk_records:
        merge_name = (xw.get("merge_name") or "").strip()
        mfl_id = xw.get("mfl_id")
        pos = (xw.get("position") or "").strip().upper()
        if merge_name and mfl_id:
            xwalk_by_name_pos[(merge_name, pos)] = mfl_id
            if merge_name not in xwalk_by_name:
                xwalk_by_name[merge_name] = mfl_id

    # Dedupe: one map entry per (player, position)
    seen_keys: set[tuple[str, str]] = set()
    player_map: list[dict[str, Any]] = []

    for rec in parsed_records:
        player = rec["player"]
        position = rec["position"]
        key = (normalize_name(player), position)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        entry: dict[str, Any] = {
            "player": player,
            "position": position,
            "team": rec.get("team", ""),
            "merge_name": key[0],
            "mfl_id": None,
            "match_method": "unmatched",
        }

        rank = rec.get("overall_rank")
        if rank is not None and rank <= rank_threshold:
            norm = key[0]

            # Try (name, position) first
            mfl_id = xwalk_by_name_pos.get((norm, position))
            if mfl_id:
                entry["mfl_id"] = str(int(mfl_id))
                entry["match_method"] = "name_position"
            else:
                # Fallback: name only
                mfl_id = xwalk_by_name.get(norm)
                if mfl_id:
                    entry["mfl_id"] = str(int(mfl_id))
                    entry["match_method"] = "name_only"

        player_map.append(entry)

    return player_map


def summarize_matching(
    parsed_records: list[dict[str, Any]],
    player_map: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return summary statistics about matching quality."""
    total_csv = len(parsed_records)
    total_map = len(player_map)
    with_mfl = sum(1 for r in player_map if r.get("mfl_id") is not None)

    methods: dict[str, int] = {}
    for r in player_map:
        m = r.get("match_method", "unknown")
        methods[m] = methods.get(m, 0) + 1

    return {
        "csv_players": total_csv,
        "player_map_total": total_map,
        "player_map_with_mfl_id": with_mfl,
        "player_map_without_mfl_id": total_map - with_mfl,
        "match_methods": methods,
    }
