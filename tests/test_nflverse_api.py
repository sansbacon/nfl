from __future__ import annotations

import sys
import types

from nfl.nflverse_fantasy.api import NflverseApiClient


class _FakeTable:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def to_dict(self, orient: str):
        assert orient == "records"
        return self._rows


def test_api_wraps_mandatory_nflreadpy_loaders(monkeypatch) -> None:
    fake_nflreadpy = types.SimpleNamespace(
        load_pbp=lambda **kwargs: _FakeTable([{"play_id": 1, "season": 2024, **kwargs}]),
        load_player_stats=lambda **kwargs: _FakeTable([{"player_id": "p1", "season": 2024, **kwargs}]),
        load_team_stats=lambda **kwargs: _FakeTable([{"team": "LAC", "season": 2024, **kwargs}]),
        load_schedules=lambda **kwargs: _FakeTable([{"game_id": "g1", "season": 2024, **kwargs}]),
        load_players=lambda: _FakeTable([{"gsis_id": "GSIS_1", "display_name": "Austin Ekeler"}]),
        load_rosters=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_rosters_weekly=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_snap_counts=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_nextgen_stats=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_ftn_charting=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_participation=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_draft_picks=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_injuries=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_contracts=lambda: _FakeTable([{"player_id": "p1"}]),
        load_officials=lambda **kwargs: _FakeTable([{"game_id": "g1", **kwargs}]),
        load_combine=lambda: _FakeTable([{"player_id": "p1"}]),
        load_depth_charts=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_trades=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_ff_playerids=lambda: _FakeTable([{"gsis_id": "GSIS_1", "yahoo_id": "1001"}]),
        load_ff_rankings=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
        load_ff_opportunity=lambda **kwargs: _FakeTable([{"player_id": "p1", **kwargs}]),
    )
    monkeypatch.setitem(sys.modules, "nflreadpy", fake_nflreadpy)

    api = NflverseApiClient()
    rows = api.get_pbp(seasons=[2024])

    assert rows
    assert rows[0]["_dataset"] == "pbp"
    assert "_record_hash" in rows[0]

    assert api.get_players()[0]["_dataset"] == "players"
    assert api.get_ff_playerids()[0]["_dataset"] == "ff_playerids"
