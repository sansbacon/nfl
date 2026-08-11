"""Fantasy Life player matching.

Two-stage join:
1. CSV players → HTML players (by exact name, then normalized fallback)
   to attach ``fl_id``.
2. Matched players → canonical crosswalk (``dim_ff_player_ids``) via
   ``normalize_name`` to obtain ``mfl_id``.

Only players with consensus_rank < 180 are matched to the crosswalk;
deeper sleepers are left with mfl_id = None.
"""

from __future__ import annotations

from typing import Any

from nfl.common.matching import normalize_name
from nfl.fantasylife_fantasy.aliases import is_dst, resolve_alias, resolve_html_display_name


# ---------------------------------------------------------------------------
# Stage 1: CSV → HTML join (attach fl_id to CSV records)
# ---------------------------------------------------------------------------


def _build_html_lookup(
    html_players: list[dict[str, Any]],
) -> tuple[dict[str, dict], dict[str, dict]]:
    """Build exact-name and normalized-name lookup dicts from HTML records.

    Also indexes by resolved CSV alias names (from ``_HTML_TO_CSV_ALIASES``)
    so that HTML entries with legal/alternate names can join to CSV entries
    that use a nickname or common name.

    Returns
    -------
    (exact_lookup, normalized_lookup)
        Both map to the full HTML record.
    """
    exact: dict[str, dict] = {}
    normalized: dict[str, dict] = {}
    for rec in html_players:
        name = rec["display_name"]
        exact[name] = rec
        normalized[normalize_name(name)] = rec
        # Also index by the resolved CSV alias (if different)
        csv_name = resolve_html_display_name(name)
        if csv_name != name:
            exact[csv_name] = rec
            normalized[normalize_name(csv_name)] = rec
    return exact, normalized


def attach_fl_ids(
    csv_records: list[dict[str, Any]],
    html_players: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Join CSV records to HTML players to attach fl_id and fl_uuid.

    Match strategy:
    1. Exact match on display_name == csv player name.
    2. Fallback: normalized name match.
    3. Unmatched: fl_id = None.

    Parameters
    ----------
    csv_records : list[dict]
        Output of ``parse_rankings_csv``.
    html_players : list[dict]
        Output of ``parse_html_players``.

    Returns
    -------
    list[dict[str, Any]]
        CSV records enriched with fl_id, fl_uuid, and match_method.
    """
    exact_lookup, norm_lookup = _build_html_lookup(html_players)

    enriched: list[dict[str, Any]] = []
    for rec in csv_records:
        player_name = rec["player"]
        result = dict(rec)  # shallow copy

        # Try exact match
        html_rec = exact_lookup.get(player_name)
        if html_rec:
            result["fl_id"] = html_rec["fl_id"]
            result["fl_uuid"] = html_rec["fl_uuid"]
            result["id_match_method"] = "exact"
        else:
            # Try normalized match
            norm_name = normalize_name(player_name)
            html_rec = norm_lookup.get(norm_name)
            if html_rec:
                result["fl_id"] = html_rec["fl_id"]
                result["fl_uuid"] = html_rec["fl_uuid"]
                result["id_match_method"] = "normalized"
            else:
                result["fl_id"] = None
                result["fl_uuid"] = None
                result["id_match_method"] = "unmatched"

        enriched.append(result)

    return enriched


# ---------------------------------------------------------------------------
# Stage 2: Match to canonical crosswalk (mfl_id)
# ---------------------------------------------------------------------------


def build_player_map(
    enriched_records: list[dict[str, Any]],
    crosswalk_records: list[dict[str, Any]],
    *,
    rank_threshold: int = 180,
) -> list[dict[str, Any]]:
    """Build the fl_player_map by matching FL players to the crosswalk.

    Only attempts crosswalk matching for players with
    consensus_rank < rank_threshold.

    Parameters
    ----------
    enriched_records : list[dict]
        Output of ``attach_fl_ids`` (CSV records with fl_id attached).
    crosswalk_records : list[dict]
        Records from ``dim_ff_player_ids`` with at least 'merge_name',
        'mfl_id', 'position' columns.
    rank_threshold : int
        Only match players ranked below this threshold (default 180).

    Returns
    -------
    list[dict[str, Any]]
        Player map records with keys: fl_id, fl_uuid, display_name,
        mfl_id, match_method.
    """
    # Build crosswalk lookup: (normalized_name, position) -> mfl_id
    # Also keep a name-only fallback for ambiguous cases
    xwalk_by_name_pos: dict[tuple[str, str], str] = {}
    xwalk_by_name: dict[str, str] = {}
    for xw in crosswalk_records:
        merge_name = (xw.get("merge_name") or "").strip()
        mfl_id = xw.get("mfl_id")
        pos = (xw.get("position") or "").strip().upper()
        if merge_name and mfl_id:
            xwalk_by_name_pos[(merge_name, pos)] = mfl_id
            # Name-only: first seen wins (prefer specific pos match)
            if merge_name not in xwalk_by_name:
                xwalk_by_name[merge_name] = mfl_id

    # Dedupe: one map entry per fl_id (skip records with no fl_id)
    seen_fl_ids: set[int] = set()
    player_map: list[dict[str, Any]] = []

    for rec in enriched_records:
        fl_id = rec.get("fl_id")
        if fl_id is None or fl_id in seen_fl_ids:
            continue
        seen_fl_ids.add(fl_id)

        consensus = rec.get("consensus_rank")
        entry: dict[str, Any] = {
            "fl_id": fl_id,
            "fl_uuid": rec.get("fl_uuid"),
            "display_name": rec["player"],
            "mfl_id": None,
            "match_method": "unmatched",
        }

        # Only attempt crosswalk match for top-ranked players
        if consensus is not None and consensus < rank_threshold:
            norm = normalize_name(rec["player"])
            pos = rec.get("position", "").upper()

            # Skip DST entries (no crosswalk representation)
            if is_dst(norm):
                entry["match_method"] = "dst_skipped"
                player_map.append(entry)
                continue

            # Apply alias resolution before lookup
            resolved = resolve_alias(norm, position=pos)

            # Try (resolved_name, position) first
            mfl_id = xwalk_by_name_pos.get((resolved, pos))
            if mfl_id:
                entry["mfl_id"] = mfl_id
                entry["match_method"] = (
                    "alias_name_position" if resolved != norm else "name_position"
                )
            else:
                # Fallback: resolved name only
                mfl_id = xwalk_by_name.get(resolved)
                if mfl_id:
                    entry["mfl_id"] = mfl_id
                    entry["match_method"] = (
                        "alias_name_only" if resolved != norm else "name_only"
                    )

        player_map.append(entry)

    return player_map


def summarize_matching(
    enriched_records: list[dict[str, Any]],
    player_map: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return summary statistics about matching quality."""
    total_csv = len(enriched_records)
    with_fl_id = sum(1 for r in enriched_records if r.get("fl_id") is not None)
    total_map = len(player_map)
    with_mfl = sum(1 for r in player_map if r.get("mfl_id") is not None)

    id_methods = {}
    for r in enriched_records:
        m = r.get("id_match_method", "unknown")
        id_methods[m] = id_methods.get(m, 0) + 1

    xwalk_methods = {}
    for r in player_map:
        m = r.get("match_method", "unknown")
        xwalk_methods[m] = xwalk_methods.get(m, 0) + 1

    return {
        "csv_players": total_csv,
        "csv_with_fl_id": with_fl_id,
        "csv_without_fl_id": total_csv - with_fl_id,
        "id_match_methods": id_methods,
        "player_map_total": total_map,
        "player_map_with_mfl_id": with_mfl,
        "player_map_without_mfl_id": total_map - with_mfl,
        "crosswalk_match_methods": xwalk_methods,
    }
