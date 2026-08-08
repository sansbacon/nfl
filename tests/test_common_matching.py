"""Tests for nfl.common.matching."""

from __future__ import annotations

import pytest

from nfl.common.matching import normalize_name


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Ja'Marr Chase", "jamarr chase"),
        ("Amon-Ra St. Brown", "amon-ra st brown"),
        ("Travis Kelce Jr.", "travis kelce"),
        ("Patrick Mahomes II", "patrick mahomes"),
        ("Patrick Mahomes III", "patrick mahomes"),
        ("Patrick Mahomes IV", "patrick mahomes"),
        ("Odell Beckham Sr.", "odell beckham"),
        ("Justin Jefferson", "justin jefferson"),
        ("A.J. Brown", "aj brown"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalize_name_parametrized(name: str, expected: str) -> None:
    assert normalize_name(name) == expected


def test_normalize_name_strips_accents() -> None:
    assert normalize_name("Davante Adams") == "davante adams"
    # Name with an accent character (ê → e after NFD stripping)
    result = normalize_name("Davantê Adams")
    assert result == "davante adams"


def test_normalize_name_preserves_hyphens() -> None:
    result = normalize_name("Amon-Ra St. Brown")
    assert "-" in result


def test_normalize_name_collapses_whitespace() -> None:
    result = normalize_name("Travis  Kelce")
    assert result == "travis kelce"


def test_normalize_name_lowercases() -> None:
    result = normalize_name("JUSTIN JEFFERSON")
    assert result == "justin jefferson"


def test_normalize_name_removes_apostrophes() -> None:
    result = normalize_name("Ja'Marr Chase")
    assert "'" not in result
