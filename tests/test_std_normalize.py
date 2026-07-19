from __future__ import annotations

from nfl.entity_standardization.normalize import normalize_position, normalize_team_code


def test_normalize_position_maps_fb_hb_to_rb() -> None:
    assert normalize_position("FB") == "RB"
    assert normalize_position("hb") == "RB"


def test_normalize_team_code_maps_legacy_aliases() -> None:
    assert normalize_team_code("San Diego") == "LAC"
    assert normalize_team_code("OAK") == "LV"
    assert normalize_team_code("WFT") == "WAS"
