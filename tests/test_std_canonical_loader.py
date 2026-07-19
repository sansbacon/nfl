from __future__ import annotations

import sys
import types

from nfl.entity_standardization.canonical import CanonicalRegistryLoader


class _FakeTable:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def to_dict(self, orient: str):
        assert orient == "records"
        return self._rows


def test_loader_uses_nflreadpy_sources(monkeypatch) -> None:
    fake_nflreadpy = types.SimpleNamespace(
        load_players=lambda: _FakeTable(
            [
                {
                    "gsis_id": "GSIS_1",
                    "display_name": "Austin Ekeler",
                    "first_name": "Austin",
                    "last_name": "Ekeler",
                    "recent_team": "LAC",
                    "position": "RB",
                }
            ]
        ),
        load_ff_playerids=lambda: _FakeTable(
            [
                {
                    "gsis_id": "GSIS_1",
                    "yahoo_id": "1001",
                    "fantasypros_id": "austin-ekeler",
                }
            ]
        ),
        load_schedules=lambda: _FakeTable(
            [
                {"home_team": "LAC", "away_team": "KC"},
                {"home_team": "WAS", "away_team": "DAL"},
            ]
        ),
    )
    monkeypatch.setitem(sys.modules, "nflreadpy", fake_nflreadpy)

    registry = CanonicalRegistryLoader().load_registry()

    assert len(registry.players) == 1
    assert registry.players[0]["canonical_player_id"] == "GSIS_1"
    assert registry.players[0]["cross_source_ids"]["yahoo"] == "1001"
    assert any(row["source_system"] == "fantasypros" for row in registry.source_to_canonical_map)
    assert {team["canonical_team_id"] for team in registry.teams} >= {"LAC", "KC", "WAS", "DAL"}
