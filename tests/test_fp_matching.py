from __future__ import annotations

from datetime import datetime, timezone

from nfl.fantasypros_fantasy.matching import build_fp_yahoo_crosswalk


def test_crosswalk_prefers_exact_and_enforces_one_to_one() -> None:
    fp_players = [
        {
            "fp_player_id": "aj-brown",
            "full_name": "A.J. Brown",
            "first_name": "A.J.",
            "last_name": "Brown",
            "position": "WR",
            "team": "PHI",
        },
        {
            "fp_player_id": "ahmarean-brown",
            "full_name": "Ahmarean Brown",
            "first_name": "Ahmarean",
            "last_name": "Brown",
            "position": "WR",
            "team": "BUF",
        },
    ]

    yahoo_players = [
        {
            "yahoo_player_id": 101,
            "full_name": "A.J. Brown",
            "first_name": "A.J.",
            "last_name": "Brown",
            "display_position": "WR",
        }
    ]

    adp_rows = [
        {"fp_player_id": "aj-brown", "rank": 9},
        {"fp_player_id": "ahmarean-brown", "rank": 250},
    ]

    rows = build_fp_yahoo_crosswalk(
        fp_players=fp_players,
        yahoo_players=yahoo_players,
        adp_rows=adp_rows,
        matched_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
    )

    assert len(rows) == 1
    assert rows[0]["fp_player_id"] == "aj-brown"
    assert rows[0]["yahoo_player_id"] == 101
    assert rows[0]["match_method"] == "exact"


def test_crosswalk_fuzzy_match_uses_first_three_chars_last_name_and_position() -> None:
    fp_players = [
        {
            "fp_player_id": "jonathan-taylor",
            "full_name": "Jonathan Taylor",
            "first_name": "Jonathan",
            "last_name": "Taylor",
            "position": "RB",
            "team": "IND",
        }
    ]
    yahoo_players = [
        {
            "yahoo_player_id": 202,
            "full_name": "Jon Taylor",
            "first_name": "Jon",
            "last_name": "Taylor",
            "display_position": "RB",
        }
    ]

    rows = build_fp_yahoo_crosswalk(fp_players=fp_players, yahoo_players=yahoo_players)

    assert len(rows) == 1
    assert rows[0]["match_method"] == "fuzzy"
