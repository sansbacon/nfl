from __future__ import annotations

import polars as pl
import pytest

from nfl.fantasypros_fantasy.transforms import TransformValidationError, transform, transform_entity


def test_transform_entity_coerces_and_sorts_adp_snapshots() -> None:
    rows = [
        {
            "fp_player_id": "p2",
            "season": "2025",
            "rank": "2",
            "adp": "14.4",
            "effective_date": "2026-07-18",
            "is_current": True,
        },
        {
            "fp_player_id": "p1",
            "season": "2025",
            "rank": "1",
            "adp": "1.4",
            "effective_date": "2026-07-18",
            "is_current": True,
        },
    ]

    frame = transform_entity(rows, entity="fp_adp_snapshot", sport="nfl")

    assert frame.schema["season"] == pl.Int64
    assert frame.schema["adp"] == pl.Float64
    assert frame["fp_player_id"].to_list() == ["p1", "p2"]


def test_transform_entity_reports_validation_error() -> None:
    bad_rows = [
        {
            "fp_player_id": "p1",
            "season": 2025,
            "rank": 1,
            "effective_date": "2026-07-18",
            "is_current": True,
        }
    ]

    with pytest.raises(TransformValidationError):
        transform_entity(bad_rows, entity="fp_adp_snapshot", sport="nfl")


def test_transform_returns_common_and_nfl_frames() -> None:
    frames = transform(
        common_entities={
            "fp_player": [
                {
                    "fp_player_id": "p1",
                    "full_name": "Justin Jefferson",
                    "first_name": "Justin",
                    "last_name": "Jefferson",
                    "position": "WR",
                    "team": "MIN",
                }
            ]
        },
        nfl_entities={
            "fp_adp_snapshot": [
                {
                    "fp_player_id": "p1",
                    "season": 2025,
                    "rank": 1,
                    "adp": 1.4,
                    "effective_date": "2026-07-18",
                    "is_current": True,
                }
            ]
        },
    )

    assert "fp_player" in frames
    assert "nfl_fp_adp_snapshot" in frames
    assert "nfl_fp_yahoo_player_map" in frames
