from __future__ import annotations

from datetime import date, datetime, timezone

import polars as pl
import pytest

from nfl.fantasypros_fantasy.validation import (
    ContractValidationError,
    get_contract,
    validate,
    validate_polars_frame,
)


def test_fp_player_contract_validates_records() -> None:
    records = [
        {
            "fp_player_id": "justin-jefferson",
            "full_name": "Justin Jefferson",
            "first_name": "Justin",
            "last_name": "Jefferson",
            "position": "WR",
            "team": "MIN",
        }
    ]

    validated = validate(records, entity="fp_player")
    assert validated == 1


def test_fp_adp_snapshot_requires_adp() -> None:
    records = [
        {
            "fp_player_id": "justin-jefferson",
            "season": 2025,
            "rank": 1,
            "effective_date": date(2026, 7, 18),
            "is_current": True,
        }
    ]

    with pytest.raises(ContractValidationError):
        validate(records, entity="fp_adp_snapshot")


def test_fp_yahoo_map_duplicate_primary_key_is_rejected() -> None:
    now = datetime.now(timezone.utc)
    records = [
        {
            "fp_player_id": "justin-jefferson",
            "yahoo_player_id": 1001,
            "match_method": "exact",
            "matched_at": now,
        },
        {
            "fp_player_id": "justin-jefferson",
            "yahoo_player_id": 1001,
            "match_method": "fuzzy",
            "matched_at": now,
        },
    ]

    with pytest.raises(ContractValidationError):
        validate(records, entity="fp_yahoo_player_map")


def test_fp_polars_frame_validation() -> None:
    contract = get_contract(entity="fp_adp_snapshot")
    frame = pl.DataFrame(
        {
            "fp_player_id": ["justin-jefferson"],
            "season": [2025],
            "rank": [1],
            "adp": [1.2],
            "effective_date": [date(2026, 7, 18)],
            "is_current": [True],
        }
    )

    validate_polars_frame(frame, contract)
