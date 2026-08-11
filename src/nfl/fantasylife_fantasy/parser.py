"""Fantasy Life data parsers.

Two parsers:
- ``parse_rankings_csv`` — reads the CSV export, keeps tiers/consensus,
  computes rank standard deviation from individual ranker columns.
- ``parse_html_players`` — one-time extraction of (fl_id, fl_uuid,
  display_name) from saved HTML ranking pages.
"""

from __future__ import annotations

import csv
import re
import statistics
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# CSV Parser
# ---------------------------------------------------------------------------

# Columns that are always present and meaningful
_KEEP_COLUMNS = {
    "position_tier",
    "overall_tier",
    "Player",
    "Position",
    "Team",
    "Bye",
    "Consensus",
    "Last Week Difference",
    "ADP",
    "Difference vs. ADP",
    "Utilization Score",
}

# Columns that are NOT individual ranker ranks
_NON_RANKER_COLUMNS = _KEEP_COLUMNS | {
    "position_tier",
    "overall_tier",
    "Player",
    "Position",
    "Team",
    "Bye",
    "Consensus",
    "Last Week Difference",
    "ADP",
    "Difference vs. ADP",
    "Utilization Score",
}


def _extract_scoring_format(path: str | Path) -> str:
    """Extract scoring format from filename, defaulting to PPR.

    Examples
    --------
    >>> _extract_scoring_format("fantasy_life_rankings_half_ppr_20260811.csv")
    'Half PPR'
    >>> _extract_scoring_format("fantasy_life_rankings_20260811.csv")
    'PPR'
    """
    name = Path(path).stem.lower()
    if "half_ppr" in name or "half-ppr" in name:
        return "Half PPR"
    if "standard" in name:
        return "Standard"
    return "PPR"


def _compute_stddev(ranker_values: list[str | None]) -> float | None:
    """Compute population stddev from ranker rank strings.

    Returns None if fewer than 2 valid numeric values.
    """
    nums: list[float] = []
    for v in ranker_values:
        if v is not None:
            try:
                nums.append(float(v))
            except (ValueError, TypeError):
                pass
    if len(nums) < 2:
        return None
    return round(statistics.pstdev(nums), 2)


def parse_rankings_csv(path: str | Path) -> list[dict[str, Any]]:
    """Parse a Fantasy Life rankings CSV export.

    Returns a list of dicts with standardized keys:
    - player, position, team, bye
    - position_tier, overall_tier
    - consensus_rank, rank_stddev
    - adp, adp_diff, utilization_score
    - last_week_diff, scoring_format

    Parameters
    ----------
    path : str | Path
        Path to the CSV file.

    Returns
    -------
    list[dict[str, Any]]
    """
    path = Path(path)
    scoring_format = _extract_scoring_format(path)

    records: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []

        # Identify ranker columns (any column not in _NON_RANKER_COLUMNS)
        ranker_cols = [h for h in headers if h not in _NON_RANKER_COLUMNS]

        for row in reader:
            # Compute stddev from individual ranker ranks
            ranker_vals = [row.get(col) for col in ranker_cols]
            stddev = _compute_stddev(ranker_vals)

            record = {
                "player": (row.get("Player") or "").strip(),
                "position": (row.get("Position") or "").strip().upper(),
                "team": (row.get("Team") or "").strip().upper(),
                "bye": _safe_int(row.get("Bye")),
                "position_tier": _safe_int(row.get("position_tier")),
                "overall_tier": _safe_int(row.get("overall_tier")),
                "consensus_rank": _safe_int(row.get("Consensus")),
                "rank_stddev": stddev,
                "adp": _safe_float(row.get("ADP")),
                "adp_diff": _safe_float(row.get("Difference vs. ADP")),
                "utilization_score": _safe_int(row.get("Utilization Score")),
                "last_week_diff": _safe_int(row.get("Last Week Difference")),
                "scoring_format": scoring_format,
            }
            if record["player"]:
                records.append(record)

    return records


# ---------------------------------------------------------------------------
# HTML Parser
# ---------------------------------------------------------------------------

# Regex: <a href="/nfl/players/{id}/{slug}" class="..." data-player="{uuid}">
#   ...  <img alt="{display_name}" ...
_PLAYER_LINK_RE = re.compile(
    r'href="/nfl/players/(\d+)/([^"]+)"[^>]*data-player="([^"]*)"'
)
_IMG_ALT_RE = re.compile(r'<img\s+alt="([^"]+)"')


def parse_html_players(paths: list[str | Path]) -> list[dict[str, Any]]:
    """Extract player IDs from Fantasy Life HTML ranking pages.

    Parses the ``<a href="/nfl/players/{fl_id}/{slug}" data-player="{uuid}">``
    elements and extracts the display name from the nested ``<img alt="...">``.

    Parameters
    ----------
    paths : list[str | Path]
        Paths to the HTML files (e.g. flife1.html through flife5.html).

    Returns
    -------
    list[dict[str, Any]]
        Records with keys: fl_id (int), fl_uuid (str), display_name (str),
        slug (str).
    """
    seen_ids: set[int] = set()
    records: list[dict[str, Any]] = []

    for path in sorted(Path(p) for p in paths):
        content = path.read_text(encoding="utf-8")

        # Split on player link anchors and capture the img alt from
        # the subsequent block (within ~1500 chars of the link)
        for match in _PLAYER_LINK_RE.finditer(content):
            fl_id = int(match.group(1))
            if fl_id in seen_ids:
                continue
            seen_ids.add(fl_id)

            slug = match.group(2)
            fl_uuid = match.group(3)

            # Find the <img alt="..."> within the next ~2000 chars
            block = content[match.end(): match.end() + 2000]
            alt_match = _IMG_ALT_RE.search(block)
            display_name = alt_match.group(1) if alt_match else _slug_to_name(slug)

            records.append({
                "fl_id": fl_id,
                "fl_uuid": fl_uuid,
                "display_name": display_name,
                "slug": slug,
            })

    return records


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slug_to_name(slug: str) -> str:
    """Convert a URL slug back to a display name as a fallback.

    Example: 'Jaxon-Smith-Njigba' -> 'Jaxon Smith-Njigba' (best effort).
    """
    # Replace hyphens with spaces, then title-case
    return slug.replace("-", " ").title()


def _safe_int(value: str | None) -> int | None:
    """Parse a string to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        # Handle float strings like "1.0"
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None


def _safe_float(value: str | None) -> float | None:
    """Parse a string to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
