from __future__ import annotations

import polars as pl
import pytest

from nfl.yahoo_fantasy.validation import (
    ContractValidationError,
    get_contract,
    validate,
    validate_polars_frame,
)


def test_common_league_contract_validates_records() -> None:
    records = [
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
    ]

    validated = validate(records, entity="league")
    assert validated == 1


def test_nfl_standings_contract_requires_team_key() -> None:
    records = [
        {
            "league_key": "461.l.717896",
            "season": 2025,
            "rank": 1,
            "wins": 10,
            "losses": 3,
            "ties": 0,
            "points_for": 1450.2,
            "points_against": 1320.1,
        }
    ]

    with pytest.raises(ContractValidationError):
        validate(records, entity="standings", sport="nfl")


def test_duplicate_primary_key_is_rejected() -> None:
    records = [
        {
            "league_key": "461.l.717896",
            "season": 2025,
            "team_key": "461.l.717896.t.1",
            "rank": 1,
            "scoring_type": "roto",
            "points_for": 92.5,
        },
        {
            "league_key": "461.l.717896",
            "season": 2025,
            "team_key": "461.l.717896.t.1",
            "rank": 2,
            "scoring_type": "roto",
            "points_for": 88.2,
        },
    ]

    with pytest.raises(ContractValidationError):
        validate(records, entity="standings", sport="nba")


def test_polars_frame_validation() -> None:
    contract = get_contract(entity="roster_entries", sport="nfl")
    frame = pl.DataFrame(
        {
            "league_key": ["461.l.717896"],
            "season": [2025],
            "week": [1],
            "team_key": ["461.l.717896.t.1"],
            "player_key": ["461.p.30123"],
            "selected_position": ["QB"],
            "is_starting": [True],
        }
    )

    validate_polars_frame(frame, contract)
