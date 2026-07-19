from __future__ import annotations

import polars as pl

from nfl.nflverse_fantasy.transforms import transform


def test_transform_builds_prefixed_frames() -> None:
    frames = transform(
        {
            "players": [
                {
                    "_record_hash": "r1",
                    "_dataset": "players",
                    "_loaded_at": "2026-07-18T00:00:00Z",
                    "gsis_id": "GSIS_1",
                    "display_name": "Austin Ekeler",
                }
            ],
            "schedules": [
                {
                    "_record_hash": "r2",
                    "_dataset": "schedules",
                    "_loaded_at": "2026-07-18T00:00:00Z",
                    "game_id": "2024_01_LAC_KC",
                }
            ],
        }
    )

    assert "nvnfl_players" in frames
    assert "nvnfl_schedules" in frames
    assert isinstance(frames["nvnfl_players"], pl.DataFrame)


def test_transform_coerces_players_types() -> None:
    frames = transform(
        {
            "players": [
                {
                    "_record_hash": "r1",
                    "_dataset": "players",
                    "_loaded_at": "2026-07-18T00:00:00Z",
                    "gsis_id": "GSIS_1",
                    "display_name": "Austin Ekeler",
                    "weight": "215",
                    "active": "true",
                    "birth_date": "1995-05-17",
                }
            ]
        }
    )

    players = frames["nvnfl_players"]
    assert players.schema["weight"] == pl.Int64
    assert players.schema["active"] == pl.Boolean
    assert players.schema["birth_date"] == pl.Date
    assert players.schema["_loaded_at"] == pl.Datetime(time_zone="UTC")


def test_transform_coerces_schedule_types() -> None:
    frames = transform(
        {
            "schedules": [
                {
                    "_record_hash": "r2",
                    "_dataset": "schedules",
                    "_loaded_at": "2026-07-18T00:00:00Z",
                    "game_id": "2024_01_LAC_KC",
                    "season": "2024",
                    "week": "1",
                    "div_game": "0",
                    "gameday": "2024-09-08",
                }
            ]
        }
    )

    schedules = frames["nvnfl_schedules"]
    assert schedules.schema["season"] == pl.Int64
    assert schedules.schema["week"] == pl.Int64
    assert schedules.schema["div_game"] == pl.Boolean
    assert schedules.schema["gameday"] == pl.Date
