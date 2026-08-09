"""Unit tests for nfl_databricks.connector module."""

import pytest

from nfl_databricks.connector.connector import (
    LakeflowConnect,
    TABLE_REGISTRY,
    _parse_seasons,
    _parse_season_type,
)


class TestParseSeasons:
    def test_single_season(self):
        assert _parse_seasons({"seasons": "2024"}) == [2024]

    def test_multiple_seasons(self):
        assert _parse_seasons({"seasons": "2022, 2023, 2024"}) == [2022, 2023, 2024]

    def test_missing_raises(self):
        with pytest.raises(ValueError, match="'seasons' option is required"):
            _parse_seasons({})

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="'seasons' option is required"):
            _parse_seasons({"seasons": ""})


class TestParseSeasonType:
    def test_default(self):
        assert _parse_season_type({}) == "REG"

    def test_post(self):
        assert _parse_season_type({"season_type": "post"}) == "POST"

    def test_reg_post(self):
        assert _parse_season_type({"season_type": "REG_POST"}) == "REG_POST"


class TestTableRegistry:
    def test_all_tables_have_required_keys(self):
        required_keys = {"load", "ingestion_type", "primary_keys", "cursor_field"}
        for table_name, entry in TABLE_REGISTRY.items():
            missing = required_keys - set(entry.keys())
            assert not missing, f"{table_name} missing keys: {missing}"

    def test_play_by_play_has_no_load(self):
        assert TABLE_REGISTRY["play_by_play"]["load"] is None
        assert TABLE_REGISTRY["play_by_play"]["ingestion_type"] == "cdc"

    def test_snapshot_tables_have_load(self):
        for name, entry in TABLE_REGISTRY.items():
            if name == "play_by_play":
                continue
            assert entry["load"] is not None, f"{name} should have a load function"
            assert entry["ingestion_type"] == "snapshot"


class TestLakeflowConnect:
    def test_list_tables(self):
        connector = LakeflowConnect({"seasons": "2024"})
        tables = connector.list_tables()
        assert "player_stats_weekly" in tables
        assert "schedules" in tables
        assert "play_by_play" in tables
        assert len(tables) == len(TABLE_REGISTRY)

    def test_read_table_metadata(self):
        connector = LakeflowConnect({"seasons": "2024"})
        meta = connector.read_table_metadata("schedules", {})
        assert meta["primary_keys"] == ["game_id"]
        assert meta["ingestion_type"] == "snapshot"

    def test_read_table_deletes_not_supported(self):
        connector = LakeflowConnect({"seasons": "2024"})
        with pytest.raises(NotImplementedError):
            connector.read_table_deletes("schedules", {}, {})


@pytest.mark.integration
class TestLakeflowConnectIntegration:
    """Tests that hit nflreadpy (network). Run with: pytest -m integration"""

    def test_read_teams(self):
        connector = LakeflowConnect({"seasons": "2024"})
        rows_iter, offset = connector.read_table("teams", {}, {})
        rows = list(rows_iter)
        assert len(rows) == 32  # NFL has 32 teams
        assert offset == {"completed": True}
