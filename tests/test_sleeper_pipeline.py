"""Integration tests for Sleeper pipeline (dry-run mode)."""

from datetime import date
from unittest.mock import patch

from nfl.sleeper_fantasy.api import SleeperPlayer
from nfl.sleeper_fantasy.pipeline import PipelineConfig, run_pipeline


def _mock_players() -> list[SleeperPlayer]:
    return [
        SleeperPlayer(
            sleeper_id="4046",
            full_name="Patrick Mahomes",
            first_name="Patrick",
            last_name="Mahomes",
            position="QB",
            team="KC",
            age=29,
            years_exp=8,
            college="Texas Tech",
            status="Active",
            adp_half_ppr=55.2,
            adp_ppr=60.1,
            adp_std=50.0,
            adp_2qb=10.5,
            adp_dynasty=30.0,
        ),
        SleeperPlayer(
            sleeper_id="6794",
            full_name="Justin Jefferson",
            first_name="Justin",
            last_name="Jefferson",
            position="WR",
            team="MIN",
            age=25,
            years_exp=5,
            college="LSU",
            status="Active",
            adp_half_ppr=8.3,
            adp_ppr=7.5,
            adp_std=9.0,
            adp_2qb=12.0,
            adp_dynasty=2.1,
        ),
    ]


class TestSleeperPipeline:
    @patch("nfl.sleeper_fantasy.pipeline.SleeperClient")
    def test_pipeline_no_storage(self, mock_client_cls):
        """Pipeline produces frames without persisting."""
        mock_client_cls.return_value.fetch_players_with_adp.return_value = _mock_players()

        result = run_pipeline(
            config=PipelineConfig(
                season=2025,
                storage_target="none",
                ingestion_date=date(2025, 8, 1),
            )
        )

        assert result.season == 2025, f"Expected season=2025, got {result.season}"
        assert "dim_sl_players" in result.frames, f"Missing dim_sl_players in {result.frames.keys()}"
        assert "fact_sl_adp" in result.frames, f"Missing fact_sl_adp in {result.frames.keys()}"
        assert result.player_count == 2, f"Expected 2 players, got {result.player_count}"
        assert result.adp_count == 2, f"Expected 2 ADP rows, got {result.adp_count}"
        assert result.frames["dim_sl_players"].height == 2
        assert result.frames["fact_sl_adp"].height == 2

    @patch("nfl.sleeper_fantasy.pipeline.SleeperClient")
    def test_pipeline_uc_dry_run(self, mock_client_cls):
        """Pipeline with unity_catalog target in dry_run produces UCWriteResults."""
        mock_client_cls.return_value.fetch_players_with_adp.return_value = _mock_players()

        result = run_pipeline(
            config=PipelineConfig(
                season=2025,
                storage_target="unity_catalog",
                uc_dry_run=True,
                ingestion_date=date(2025, 8, 1),
            )
        )

        assert len(result.uc_outputs) == 2, f"Expected 2 UC outputs, got {len(result.uc_outputs)}"
        targets = {r.target for r in result.uc_outputs}
        assert "nfl.sl.dim_sl_players" in targets, f"Expected dim_sl_players in {targets}"
        assert "nfl.sl.fact_sl_adp" in targets, f"Expected fact_sl_adp in {targets}"

    @patch("nfl.sleeper_fantasy.pipeline.SleeperClient")
    def test_pipeline_empty_response(self, mock_client_cls):
        """Pipeline handles empty API response gracefully."""
        mock_client_cls.return_value.fetch_players_with_adp.return_value = []

        result = run_pipeline(
            config=PipelineConfig(season=2025, storage_target="none")
        )

        assert result.player_count == 0, f"Expected 0 players, got {result.player_count}"
        assert result.adp_count == 0, f"Expected 0 ADP rows, got {result.adp_count}"
