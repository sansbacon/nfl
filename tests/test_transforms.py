from __future__ import annotations

import polars as pl
import pytest

from nfl.yahoo_fantasy.transforms import TransformValidationError, transform, transform_entity, transform_nfl


def test_transform_entity_coerces_and_sorts_nfl_standings() -> None:
    rows = [
        {
            "league_key": "461.l.717896",
            "season": "2025",
            "team_key": "461.l.717896.t.2",
            "rank": "2",
            "wins": "9",
            "losses": "4",
            "ties": "0",
            "points_for": "1399.1",
            "points_against": "1300.0",
        },
        {
            "league_key": "461.l.717896",
            "season": "2025",
            "team_key": "461.l.717896.t.1",
            "rank": "1",
            "wins": "10",
            "losses": "3",
            "ties": "0",
            "points_for": "1450.2",
            "points_against": "1320.1",
        },
    ]

    frame = transform_entity(rows, entity="standings", sport="nfl")

    assert frame.schema["season"] == pl.Int64
    assert frame.schema["points_for"] == pl.Float64
    assert frame["team_key"].to_list() == ["461.l.717896.t.1", "461.l.717896.t.2"]


def test_transform_entity_reports_validation_error() -> None:
    bad_rows = [
        {
            "league_key": "461.l.717896",
            "season": 2025,
            "team_key": "461.l.717896.t.1",
            "wins": 10,
            "losses": 3,
            "ties": 0,
            "points_for": 1450.2,
            "points_against": 1320.1,
        }
    ]

    with pytest.raises(TransformValidationError):
        transform_entity(bad_rows, entity="standings", sport="nfl")


def test_transform_nfl_is_deterministic() -> None:
    standings_a = [
        {
            "league_key": "461.l.717896",
            "season": 2025,
            "team_key": "461.l.717896.t.2",
            "rank": 2,
            "wins": 9,
            "losses": 4,
            "ties": 0,
            "points_for": 1399.1,
            "points_against": 1300.0,
        },
        {
            "league_key": "461.l.717896",
            "season": 2025,
            "team_key": "461.l.717896.t.1",
            "rank": 1,
            "wins": 10,
            "losses": 3,
            "ties": 0,
            "points_for": 1450.2,
            "points_against": 1320.1,
        },
    ]
    standings_b = list(reversed(standings_a))

    result_a = transform_nfl(standings=standings_a)
    result_b = transform_nfl(standings=standings_b)

    assert result_a.frames["standings"].to_dicts() == result_b.frames["standings"].to_dicts()


def test_transform_full_pipeline_common_and_sport_frames() -> None:
    frames = transform(
        common_entities={
            "league": [
                {
                    "league_key": "461.l.717896",
                    "league_id": "717896",
                    "game_id": 461,
                    "game_code": "nfl",
                    "season": 2025,
                    "league_name": "Test League",
                    "scoring_type": "head",
                    "league_type": "private",
                    "num_teams": 12,
                }
            ],
            "team": [
                {
                    "team_key": "461.l.717896.t.1",
                    "league_key": "461.l.717896",
                    "team_id": 1,
                    "team_name": "Team One",
                    "owner_name": "Owner One",
                    "draft_position": 2,
                }
            ],
            "stat_category": [
                {
                    "game_id": 461,
                    "stat_id": "5",
                    "display_name": "Pass Yds",
                    "name": "Passing Yards",
                }
            ],
            "scoring_rule": [
                {
                    "league_key": "461.l.717896",
                    "season": 2025,
                    "stat_id": "5",
                    "points_per_unit": 0.04,
                    "bonus_target": None,
                    "bonus_points": None,
                }
            ],
        },
        nfl_entities={
            "standings": [
                {
                    "league_key": "461.l.717896",
                    "season": 2025,
                    "team_key": "461.l.717896.t.1",
                    "rank": 1,
                    "wins": 10,
                    "losses": 3,
                    "ties": 0,
                    "points_for": 1450.2,
                    "points_against": 1320.1,
                }
            ]
        },
        nba_entities={
            "standings": [
                {
                    "league_key": "418.l.123456",
                    "season": 2025,
                    "team_key": "418.l.123456.t.1",
                    "rank": 1,
                    "scoring_type": "roto",
                    "points_for": 95.0,
                }
            ]
        },
    )

    assert "league" in frames
    assert "stat_category" in frames
    assert "scoring_rule" in frames
    assert "nfl_standings" in frames
    assert "nba_standings" in frames
