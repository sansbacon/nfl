"""Known nickname → canonical crosswalk name mappings.

Resolves cases where a Fantasy Life display name (or any other source)
uses a nickname, abbreviation, or legal-name variant that differs from
the nflreadpy crosswalk's ``merge_name``.

All keys and values are **already normalized** (lowercase, no accents,
no apostrophes/periods, hyphens preserved, no suffixes).

Usage::

    from nfl.fantasylife_fantasy.aliases import resolve_alias

    canonical = resolve_alias("chig okonkwo", position="TE")
    # -> "chigoziem okonkwo"
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Alias registry
# ---------------------------------------------------------------------------
# Key: (normalized_name, position) or just normalized_name
# Value: canonical crosswalk merge_name
#
# Use the (name, position) tuple for ambiguous names (e.g. multiple
# "mike williams" across positions). Use name-only for unambiguous.
# ---------------------------------------------------------------------------

# Nicknames → legal/crosswalk names
_NICKNAME_ALIASES: dict[str, str] = {
    "chig okonkwo": "chigoziem okonkwo",
    "hollywood brown": "marquise brown",
    "zonovan knight": "bam knight",
    "joshua palmer": "josh palmer",
    "gabe davis": "gabriel davis",
    "scotty miller": "scott miller",
    "pat freiermuth": "patrick freiermuth",
    "robbie chosen anderson": "robbie anderson",
    "chosen anderson": "robbie anderson",
    "ken walker": "kenneth walker",
}

# Position-qualified aliases for names that are ambiguous across positions
_POSITIONAL_ALIASES: dict[tuple[str, str], str] = {
    # Add entries here when the same normalized name maps to different
    # crosswalk players depending on position:
    # ("mike williams", "WR"): "michael williams",  # example
}

# DST team names → crosswalk-compatible identifiers.
# nflreadpy has no DST entries so these map to None (no mfl_id),
# but we store the abbreviation for downstream use.
_DST_ALIASES: dict[str, str] = {
    "los angeles rams": "LAR",
    "los angeles chargers": "LAC",
    "san francisco 49ers": "SF",
    "las vegas raiders": "LV",
    "washington commanders": "WAS",
    "new york giants": "NYG",
    "new york jets": "NYJ",
    "new england patriots": "NE",
    "tampa bay buccaneers": "TB",
    "green bay packers": "GB",
    "kansas city chiefs": "KC",
    "new orleans saints": "NO",
    "jacksonville jaguars": "JAX",
    "minnesota vikings": "MIN",
    "buffalo bills": "BUF",
    "pittsburgh steelers": "PIT",
    "denver broncos": "DEN",
    "miami dolphins": "MIA",
    "philadelphia eagles": "PHI",
    "baltimore ravens": "BAL",
    "detroit lions": "DET",
    "dallas cowboys": "DAL",
    "cleveland browns": "CLE",
    "atlanta falcons": "ATL",
    "houston texans": "HOU",
    "indianapolis colts": "IND",
    "tennessee titans": "TEN",
    "carolina panthers": "CAR",
    "seattle seahawks": "SEA",
    "arizona cardinals": "ARI",
    "chicago bears": "CHI",
    "cincinnati bengals": "CIN",
}



# HTML display name → CSV player name mappings.
# Used in Stage 1 (CSV→HTML join) when Fantasy Life uses a different
# display name in HTML vs. their CSV export.
_HTML_TO_CSV_ALIASES: dict[str, str] = {
    "Jo\u2019quavioius Marks": "Woody Marks",
    "Jo'quavioius Marks": "Woody Marks",
}


def resolve_html_display_name(html_name: str) -> str:
    """Resolve an HTML display name to the CSV player name.

    Used in Stage 1 matching when the HTML page uses a different name
    variant (legal name, misspelling) than the CSV export.

    Parameters
    ----------
    html_name : str
        Display name as parsed from the HTML ``<img alt="...">`` tag.

    Returns
    -------
    str
        The corresponding CSV player name, or the input unchanged.
    """
    return _HTML_TO_CSV_ALIASES.get(html_name, html_name)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_alias(
    normalized_name: str,
    position: str | None = None,
) -> str:
    """Resolve a normalized name to its canonical crosswalk merge_name.

    Lookup order:
    1. Positional alias (name + position) — most specific.
    2. Nickname alias (name only).
    3. Return the input unchanged if no alias found.

    Parameters
    ----------
    normalized_name : str
        Already-normalized player name (output of ``normalize_name``).
    position : str | None
        Player position code (e.g. "TE", "WR"). Used for
        position-qualified disambiguation.

    Returns
    -------
    str
        Canonical crosswalk merge_name, or the original name if no
        alias exists.

    Examples
    --------
    >>> resolve_alias("chig okonkwo", position="TE")
    'chigoziem okonkwo'
    >>> resolve_alias("patrick mahomes", position="QB")
    'patrick mahomes'
    """
    # Check positional alias first
    if position:
        pos_key = (normalized_name, position.upper())
        if pos_key in _POSITIONAL_ALIASES:
            return _POSITIONAL_ALIASES[pos_key]

    # Check nickname alias
    if normalized_name in _NICKNAME_ALIASES:
        return _NICKNAME_ALIASES[normalized_name]

    return normalized_name


def is_dst(normalized_name: str) -> bool:
    """Check if a normalized name is a DST team entry."""
    return normalized_name in _DST_ALIASES


def get_dst_abbrev(normalized_name: str) -> str | None:
    """Get the team abbreviation for a DST entry, or None."""
    return _DST_ALIASES.get(normalized_name)


def list_aliases() -> dict[str, str]:
    """Return all registered nickname aliases (for debugging/display)."""
    return dict(_NICKNAME_ALIASES)
