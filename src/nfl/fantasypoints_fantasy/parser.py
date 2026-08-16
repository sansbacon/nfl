"""Fantasy Points CSV parser.

Reads the Fantasy Points redraft PPR rankings export and produces
standardized records for downstream transforms.

Expected CSV columns:
- OVERALL: overall rank (int)
- NAME: player name (str)
- Position: position (QB/RB/WR/TE)
- Team: NFL team abbreviation
- BYE: bye week (int)
- $$: auction value as dollar string (e.g. "$60")
- EXODIA: flag ("1" or null)
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


# Column name for auction value (three dollar signs)
_DOLLAR_COL = "$" * 3


def parse_rankings_csv(path: str | Path) -> list[dict[str, Any]]:
    """Parse a Fantasy Points rankings CSV export.

    Returns a list of dicts with standardized keys:
    - player, position, team, bye
    - overall_rank, auction_value, exodia
    - scoring_format (always "Redraft PPR")

    Parameters
    ----------
    path : str | Path
        Path to the CSV file.

    Returns
    -------
    list[dict[str, Any]]
    """
    path = Path(path)
    records: list[dict[str, Any]] = []

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)

        for row in reader:
            record = {
                "player": (row.get("NAME") or "").strip(),
                "position": (row.get("Position") or "").strip().upper(),
                "team": (row.get("Team") or "").strip().upper(),
                "bye": _safe_int(row.get("BYE")),
                "overall_rank": _safe_int(row.get("OVERALL")),
                "auction_value": _parse_dollar(row.get(_DOLLAR_COL)),
                "exodia": _parse_bool_flag(row.get("EXODIA")),
                "scoring_format": "Redraft PPR",
            }
            if record["player"]:
                records.append(record)

    return records


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_dollar(value: str | None) -> int | None:
    """Parse a dollar string like '$60' to an integer.

    Examples
    --------
    >>> _parse_dollar("$60")
    60
    >>> _parse_dollar(None)
    """
    if not value:
        return None
    cleaned = value.strip().lstrip("$")
    try:
        return int(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_bool_flag(value: str | None) -> bool:
    """Parse a '1'/null flag to boolean."""
    if not value:
        return False
    return value.strip() == "1"


def _safe_int(value: str | None) -> int | None:
    """Parse a string to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
