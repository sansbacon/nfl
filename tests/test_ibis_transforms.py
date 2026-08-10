"""Tests for all source module transforms_ibis.

Covers: fantasypros, yahoo, sleeper, espn, nflverse, entity_standardization.
All tests use DuckDB :memory: via ibis.memtable().
"""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import ibis
import pytest


# ---------------------------------------------------------------------------
# FantasyPros
# ---------------------------------------------------------------------------


class TestFantasyProsTransforms:
    def test_transform_entity_fp_player(self):
        from nfl.fantasypros_fantasy.transforms_ibis import transform_entity

        records = [
            {"fp_player_id": "100", "full_name": "Josh Allen", "position": "QB", "team": "BUF"},
            {"fp_player_id": "101", "full_name": "Ja'Marr Chase", "position": "WR", "team": "CIN"},
        ]
        t = transform_entity(records, entity="fp_player")
        df = t.execute()
        assert len(df) == 2
        assert "fp_player_id" in df.columns
        assert "full_name" in df.columns

    def test_transform_entity_empty(self):
        from nfl.fantasypros_fantasy.transforms_ibis import transform_entity

        t = transform_entity([], entity="fp_player")
        assert int(t.count().execute()) == 0

    def test_transform_returns_all_entities(self):
        from nfl.fantasypros_fantasy.transforms_ibis import transform

        records = [
            {"fp_player_id": "1", "full_name": "Test", "position": "QB", "team": "NYJ"},
        ]
        result = transform(
            common_entities={"fp_player": records},
            nfl_entities={"fp_adp_snapshot": [], "fp_yahoo_player_map": []},
        )
        assert "fp_player" in result
        assert "nfl_fp_adp_snapshot" in result
        assert "nfl_fp_yahoo_player_map" in result


# ---------------------------------------------------------------------------
# Sleeper
# ---------------------------------------------------------------------------


class TestSleeperTransforms:
    def test_players_to_dim_table(self):
        from nfl.sleeper_fantasy.api import SleeperPlayer
        from nfl.sleeper_fantasy.transforms_ibis import players_to_dim_table

        players = [
            SleeperPlayer(
                sleeper_id="1", full_name="Test Player", first_name="Test",
                last_name="Player", position="QB", team="KC", age=28,
                years_exp=6, college="Texas Tech", status="Active",
            ),
        ]
        t = players_to_dim_table(players)
        df = t.execute()
        assert len(df) == 1
        assert df["full_name"].iloc[0] == "Test Player"
        assert df["age"].dtype == "int64"

    def test_players_to_adp_table(self):
        from nfl.sleeper_fantasy.api import SleeperPlayer
        from nfl.sleeper_fantasy.transforms_ibis import players_to_adp_table

        players = [
            SleeperPlayer(
                sleeper_id="1", full_name="Test", first_name="T",
                last_name="P", position="QB", team="KC", age=28,
                years_exp=6, college="MIT", status="Active",
                adp_half_ppr=5.2, adp_ppr=4.8, adp_std=6.1,
                adp_2qb=2.0, adp_dynasty=3.5,
            ),
        ]
        t = players_to_adp_table(players, season=2025, ingestion_date=date(2025, 7, 1))
        df = t.execute()
        assert len(df) == 1
        assert df["season"].dtype == "int64"
        assert df["adp_half_ppr"].dtype == "float64"

    def test_empty_players_returns_empty_table(self):
        from nfl.sleeper_fantasy.transforms_ibis import players_to_dim_table

        t = players_to_dim_table([])
        assert int(t.count().execute()) == 0


# ---------------------------------------------------------------------------
# ESPN
# ---------------------------------------------------------------------------


class TestEspnTransforms:
    def test_players_to_ranks_table(self):
        from nfl.espn_fantasy.api import EspnPlayer
        from nfl.espn_fantasy.transforms_ibis import players_to_ranks_table

        players = [
            EspnPlayer(
                espn_id=123, full_name="Patrick Mahomes", first_name="Patrick",
                last_name="Mahomes", position="QB", team="KC", pro_team_id=12,
                rank_ppr=1, rank_standard=2,
                auction_value_ppr=45.0, auction_value_standard=42.0,
                percent_owned=99.5, percent_started=95.0,
            ),
        ]
        t = players_to_ranks_table(players, season=2025)
        df = t.execute()
        assert len(df) == 1
        assert df["espn_id"].dtype == "int64"
        assert df["percent_owned"].dtype == "float64"

    def test_empty_players_returns_empty(self):
        from nfl.espn_fantasy.transforms_ibis import players_to_ranks_table

        t = players_to_ranks_table([], season=2025)
        assert int(t.count().execute()) == 0


# ---------------------------------------------------------------------------
# NFLverse
# ---------------------------------------------------------------------------


class TestNflverseTransforms:
    def test_transform_entity_player_stats(self):
        from nfl.nflverse_fantasy.transforms_ibis import transform_entity

        records = [
            {"_record_hash": "abc", "_dataset": "player_stats", "_loaded_at": "2025-01-15",
             "season": "2024", "week": "1", "completions": "28", "attempts": "39",
             "carries": "3", "passing_yards": "291.0", "fantasy_points_ppr": "22.8"},
        ]
        t = transform_entity(records, entity="player_stats")
        df = t.execute()
        assert len(df) == 1
        assert df["season"].dtype == "int64"
        assert df["passing_yards"].dtype == "float64"

    def test_boolean_coercion(self):
        from nfl.nflverse_fantasy.transforms_ibis import transform_entity

        records = [
            {"_record_hash": "x", "_dataset": "injuries", "_loaded_at": "2025-01-01",
             "season": "2024", "week": "5",
             "did_not_practice": "true", "questionable": "1",
             "doubtful": "false", "out": "0"},
        ]
        t = transform_entity(records, entity="injuries")
        df = t.execute()
        assert df["did_not_practice"].iloc[0] is True
        assert df["out"].iloc[0] is False

    def test_transform_empty_entity(self):
        from nfl.nflverse_fantasy.transforms_ibis import transform_entity

        t = transform_entity([], entity="pbp")
        assert int(t.count().execute()) == 0

    def test_transform_orchestrator(self):
        from nfl.nflverse_fantasy.transforms_ibis import transform

        records = [
            {"_record_hash": "a", "_dataset": "combine", "_loaded_at": "2025-03-01",
             "year": "2025", "height": "73", "weight": "185", "forty": "4.38"},
        ]
        result = transform({"combine": records})
        assert "nvnfl_combine" in result
        df = result["nvnfl_combine"].execute()
        assert df["year"].dtype == "int64"
        assert df["forty"].dtype == "float64"


# ---------------------------------------------------------------------------
# Entity Standardization adapter
# ---------------------------------------------------------------------------


class TestEntityStandardizationAdapter:
    def test_result_tables_to_ibis(self):
        import polars as pl
        from nfl.entity_standardization.ibis_adapter import result_tables_to_ibis
        from nfl.entity_standardization.pipeline import StandardizationResult

        mock_result = StandardizationResult(
            standardized_records=[],
            tables={"std_test": pl.DataFrame({"id": [1, 2], "value": ["a", "b"]})},
            polars_outputs={},
            iceberg_outputs=[],
        )
        ibis_tables = result_tables_to_ibis(mock_result)
        assert "std_test" in ibis_tables
        assert int(ibis_tables["std_test"].count().execute()) == 2
