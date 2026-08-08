"""Tests for nfl.nflverse_fantasy.models.common."""

from __future__ import annotations

import pytest

from nfl.nflverse_fantasy.models.common import (
    COMMON_ENTITY_NAMES,
    NflverseRecordMeta,
)


def test_nflverse_record_meta_creation() -> None:
    meta = NflverseRecordMeta(
        record_hash="abc123",
        dataset="players",
        loaded_at="2026-07-18T00:00:00Z",
    )
    assert meta.record_hash == "abc123"
    assert meta.dataset == "players"
    assert meta.loaded_at == "2026-07-18T00:00:00Z"


def test_nflverse_record_meta_is_frozen() -> None:
    meta = NflverseRecordMeta(
        record_hash="xyz",
        dataset="schedules",
        loaded_at="2026-07-18T00:00:00Z",
    )
    with pytest.raises((AttributeError, TypeError)):
        meta.dataset = "other"  # type: ignore[misc]


def test_common_entity_names_contains_expected_entities() -> None:
    assert "players" in COMMON_ENTITY_NAMES
    assert "schedules" in COMMON_ENTITY_NAMES
    assert "ff_playerids" in COMMON_ENTITY_NAMES
