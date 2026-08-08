"""Tests for nfl.fantasypros_fantasy.matching.fp_adp_records_to_fp_players."""

from __future__ import annotations

from nfl.fantasypros_fantasy.matching import fp_adp_records_to_fp_players


def test_basic_conversion_splits_name_and_builds_id() -> None:
    records = [
        {"player_name": "Justin Jefferson", "team": "MIN", "position": "WR"},
    ]
    result = fp_adp_records_to_fp_players(records)

    assert len(result) == 1
    player = result[0]
    assert player["full_name"] == "Justin Jefferson"
    assert player["first_name"] == "Justin"
    assert player["last_name"] == "Jefferson"
    assert player["team"] == "MIN"
    assert player["position"] == "WR"
    assert player["fp_player_id"] == "justin-jefferson_min"


def test_single_name_player_has_empty_last_name() -> None:
    records = [{"player_name": "Gronk", "team": "NE", "position": "TE"}]
    result = fp_adp_records_to_fp_players(records)

    assert result[0]["first_name"] == "Gronk"
    assert result[0]["last_name"] == ""


def test_no_team_produces_id_without_suffix() -> None:
    records = [{"player_name": "Christian McCaffrey", "team": "", "position": "RB"}]
    result = fp_adp_records_to_fp_players(records)

    assert result[0]["fp_player_id"] == "christian-mccaffrey"


def test_missing_team_key_uses_empty_string() -> None:
    records = [{"player_name": "Christian McCaffrey", "position": "RB"}]
    result = fp_adp_records_to_fp_players(records)

    assert result[0]["team"] == ""
    assert result[0]["fp_player_id"] == "christian-mccaffrey"


def test_missing_position_key_uses_empty_string() -> None:
    records = [{"player_name": "Tyreek Hill", "team": "MIA"}]
    result = fp_adp_records_to_fp_players(records)

    assert result[0]["position"] == ""


def test_empty_player_name_is_skipped() -> None:
    records = [
        {"player_name": "", "team": "MIN", "position": "WR"},
        {"player_name": "Davante Adams", "team": "LV", "position": "WR"},
    ]
    result = fp_adp_records_to_fp_players(records)

    assert len(result) == 1
    assert result[0]["full_name"] == "Davante Adams"


def test_none_player_name_is_skipped() -> None:
    records = [
        {"player_name": None, "team": "MIN", "position": "WR"},
    ]
    result = fp_adp_records_to_fp_players(records)

    assert result == []


def test_multiple_records_preserves_order() -> None:
    records = [
        {"player_name": "Christian McCaffrey", "team": "SF", "position": "RB"},
        {"player_name": "Justin Jefferson", "team": "MIN", "position": "WR"},
        {"player_name": "Travis Kelce", "team": "KC", "position": "TE"},
    ]
    result = fp_adp_records_to_fp_players(records)

    assert [r["full_name"] for r in result] == [
        "Christian McCaffrey",
        "Justin Jefferson",
        "Travis Kelce",
    ]


def test_special_characters_in_name_are_slugified() -> None:
    records = [{"player_name": "D'Andre Swift", "team": "CHI", "position": "RB"}]
    result = fp_adp_records_to_fp_players(records)

    assert result[0]["fp_player_id"] == "d-andre-swift_chi"


def test_output_has_required_fp_player_keys() -> None:
    records = [{"player_name": "Saquon Barkley", "team": "PHI", "position": "RB"}]
    result = fp_adp_records_to_fp_players(records)

    required = {"fp_player_id", "full_name", "first_name", "last_name", "position", "team"}
    assert required <= set(result[0].keys())
