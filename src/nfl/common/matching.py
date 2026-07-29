"""Shared player name normalization utilities.

Used across all source loaders (ETR, FL, ESPN, FantasyPros) to match
player names to the canonical nflreadpy crosswalk.
"""

from __future__ import annotations

import re
import unicodedata


def normalize_name(name: str) -> str:
    """Normalize a player name to match nflreadpy's merge_name format.

    Preserves hyphens, strips accents, apostrophes, periods, and suffixes
    (Jr., Sr., II, III, etc.).

    Examples:
        >>> normalize_name("Ja'Marr Chase")
        'jamarr chase'
        >>> normalize_name("Amon-Ra St. Brown")
        'amon-ra st brown'
        >>> normalize_name("Travis Kelce Jr.")
        'travis kelce'
    """
    if not name:
        return ""
    s = name.lower().strip()
    # Strip accents
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    # Remove common suffixes
    suffix_pattern = r"\b(jr\.?|sr\.?|ii|iii|iv|v)\s*$"
    s = re.sub(suffix_pattern, "", s).strip()
    # Remove apostrophes and periods but keep hyphens, spaces, letters
    s = re.sub(r"[^a-z\s-]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s
