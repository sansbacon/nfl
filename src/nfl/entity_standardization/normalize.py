"""Deterministic normalization for names, teams, and positions."""

from __future__ import annotations

import re
import unicodedata

ALLOWED_POSITIONS: tuple[str, ...] = ("QB", "RB", "WR", "TE", "DST", "K")

_POSITION_ALIASES = {
    "QB": "QB",
    "RB": "RB",
    "WR": "WR",
    "TE": "TE",
    "K": "K",
    "PK": "K",
    "DST": "DST",
    "D/ST": "DST",
    "DEF": "DST",
    "DEFENSE": "DST",
    "FB": "RB",
    "HB": "RB",
}

_TEAM_ALIASES = {
    "SD": "LAC",
    "SAN DIEGO": "LAC",
    "SAN DIEGO CHARGERS": "LAC",
    "STL": "LAR",
    "ST LOUIS": "LAR",
    "ST LOUIS RAMS": "LAR",
    "OAK": "LV",
    "OAKLAND": "LV",
    "OAKLAND RAIDERS": "LV",
    "WSH": "WAS",
    "WSN": "WAS",
    "WFT": "WAS",
    "WASHINGTON FOOTBALL TEAM": "WAS",
    "WASHINGTON REDSKINS": "WAS",
    "JAC": "JAX",
}

_SUFFIX_TOKENS = {"JR", "SR", "II", "III", "IV", "V"}


def normalize_text(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    ascii_value = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.upper()
    cleaned = re.sub(r"[^A-Z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_player_name(name: str | None) -> str:
    text = normalize_text(name)
    if not text:
        return ""
    tokens = [tok for tok in text.split(" ") if tok and tok not in _SUFFIX_TOKENS]
    return " ".join(tokens)


def normalize_team_code(team: str | None) -> str:
    normalized = normalize_text(team)
    if not normalized:
        return ""
    return _TEAM_ALIASES.get(normalized, normalized)


def normalize_position(position: str | None) -> str:
    normalized = normalize_text(position)
    if not normalized:
        return ""
    return _POSITION_ALIASES.get(normalized, normalized)
