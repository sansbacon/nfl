"""Tests for nfl.fantasypros_fantasy.models.common."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from nfl.fantasypros_fantasy.models.common import (
    COMMON_ENTITY_NAMES,
    FpAdpSnapshot,
    FpPlayer,
    FpYahooPlayerMap,
)


def test_fp_player_creation() -> None:
    player = FpPlayer(
        fp_player_id="justin-jefferson",
        full_name="Justin Jefferson",
        first_name="Justin",
        last_name="Jefferson",
        position="WR",
        team="MIN",
    )
    assert player.fp_player_id == "justin-jefferson"
    assert player.full_name == "Justin Jefferson"
    assert player.position == "WR"
    assert player.team == "MIN"


def test_fp_player_is_frozen() -> None:
    player = FpPlayer(
        fp_player_id="p1",
        full_name="Test Player",
        first_name="Test",
        last_name="Player",
        position="RB",
        team="KC",
    )
    with pytest.raises((AttributeError, TypeError)):
        player.team = "SF"  # type: ignore[misc]


def test_fp_adp_snapshot_required_fields() -> None:
    snap = FpAdpSnapshot(
        fp_player_id="justin-jefferson",
        season=2025,
        rank=5,
        adp=5.2,
        effective_date=date(2026, 7, 18),
        is_current=True,
    )
    assert snap.rank == 5
    assert snap.adp == 5.2
    assert snap.is_current is True
    # Optional fields default to None
    assert snap.adp_espn is None
    assert snap.bye_week is None
    assert snap.end_date is None


def test_fp_adp_snapshot_optional_fields() -> None:
    snap = FpAdpSnapshot(
        fp_player_id="p1",
        season=2025,
        rank=1,
        adp=1.0,
        effective_date=date(2026, 7, 18),
        is_current=True,
        adp_espn=1.5,
        bye_week=7,
        high=1,
        low=3,
        stdev=0.5,
        end_date=date(2026, 8, 1),
    )
    assert snap.adp_espn == 1.5
    assert snap.bye_week == 7
    assert snap.high == 1
    assert snap.end_date == date(2026, 8, 1)


def test_fp_yahoo_player_map_creation() -> None:
    now = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
    mapping = FpYahooPlayerMap(
        fp_player_id="justin-jefferson",
        yahoo_player_id=12345,
        match_method="exact",
        matched_at=now,
    )
    assert mapping.fp_player_id == "justin-jefferson"
    assert mapping.yahoo_player_id == 12345
    assert mapping.match_method == "exact"
    assert mapping.matched_at == now


def test_common_entity_names_contains_expected_entities() -> None:
    assert "fp_player" in COMMON_ENTITY_NAMES
    assert "fp_adp_snapshot" in COMMON_ENTITY_NAMES
    assert "fp_yahoo_player_map" in COMMON_ENTITY_NAMES
