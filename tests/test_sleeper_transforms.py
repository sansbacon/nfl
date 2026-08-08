"""Unit tests for Sleeper transform functions."""

from datetime import date

from nfl.sleeper_fantasy.api import SleeperPlayer
from nfl.sleeper_fantasy.transforms import players_to_adp_rows, players_to_dim_rows


def _make_player(**overrides) -> SleeperPlayer:
    defaults = {
        "sleeper_id": "4046",
        "full_name": "Patrick Mahomes",
        "first_name": "Patrick",
        "last_name": "Mahomes",
        "position": "QB",
        "team": "KC",
        "age": 29,
        "years_exp": 8,
        "college": "Texas Tech",
        "status": "Active",
        "adp_half_ppr": 55.2,
        "adp_ppr": 60.1,
        "adp_std": 50.0,
        "adp_2qb": 10.5,
        "adp_dynasty": 30.0,
    }
    defaults.update(overrides)
    return SleeperPlayer(**defaults)


class TestPlayersToDimRows:
    def test_basic_conversion(self):
        players = [_make_player()]
        rows = players_to_dim_rows(players)
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        row = rows[0]
        assert row["sleeper_player_id"] == "4046"
        assert row["full_name"] == "Patrick Mahomes"
        assert row["position"] == "QB"
        assert row["team"] == "KC"
        assert row["age"] == 29
        assert row["college"] == "Texas Tech"

    def test_multiple_players(self):
        players = [
            _make_player(sleeper_id="4046", full_name="Patrick Mahomes"),
            _make_player(
                sleeper_id="6794", full_name="Justin Jefferson", position="WR", team="MIN"
            ),
        ]
        rows = players_to_dim_rows(players)
        assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
        ids = {r["sleeper_player_id"] for r in rows}
        assert ids == {"4046", "6794"}, f"Unexpected IDs: {ids}"

    def test_empty_input(self):
        rows = players_to_dim_rows([])
        assert rows == [], f"Expected empty list, got {rows}"


class TestPlayersToAdpRows:
    def test_basic_conversion(self):
        players = [_make_player()]
        rows = players_to_adp_rows(players, season=2025, ingestion_date=date(2025, 8, 1))
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        row = rows[0]
        assert row["season"] == 2025
        assert row["sleeper_player_id"] == "4046"
        assert row["adp_half_ppr"] == 55.2
        assert row["adp_ppr"] == 60.1
        assert row["adp_std"] == 50.0
        assert row["adp_2qb"] == 10.5
        assert row["adp_dynasty"] == 30.0
        assert row["ingestion_date"] == date(2025, 8, 1)
        assert row["is_current"] is True
        assert row["end_date"] is None

    def test_excludes_null_adp(self):
        """Players with adp_half_ppr=None should be excluded."""
        players = [
            _make_player(sleeper_id="100", adp_half_ppr=10.0),
            _make_player(sleeper_id="200", adp_half_ppr=None),
        ]
        rows = players_to_adp_rows(players, season=2025)
        ids = [r["sleeper_player_id"] for r in rows]
        assert "100" in ids, f"Expected '100' in {ids}"
        assert "200" not in ids, f"'200' should be excluded, got {ids}"

    def test_default_ingestion_date(self):
        """When no ingestion_date is given, defaults to today."""
        players = [_make_player()]
        rows = players_to_adp_rows(players, season=2025)
        assert rows[0]["ingestion_date"] == date.today()
