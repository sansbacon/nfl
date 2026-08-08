"""Tests for ESPN Fantasy pipeline."""

from datetime import date
from unittest.mock import MagicMock, patch

from nfl.espn_fantasy.api import EspnPlayer
from nfl.espn_fantasy.pipeline import PipelineConfig, PipelineRunResult, run_pipeline


def _mock_players() -> list[EspnPlayer]:
    return [
        EspnPlayer(
            espn_id=3139477,
            full_name="Patrick Mahomes",
            first_name="Patrick",
            last_name="Mahomes",
            position="QB",
            team="KC",
            pro_team_id=12,
            rank_standard=5,
            rank_ppr=5,
            auction_value_standard=55,
            auction_value_ppr=55,
            percent_owned=99.5,
            percent_started=98.0,
            season_projection={"pass_yds": 4900.0, "pass_td": 37.0},
            season_projected_total=380.5,
            weekly_projections={1: {"pass_yds": 290.0}, 2: {"pass_yds": 310.0}},
            weekly_projected_totals={1: 22.5, 2: 24.0},
        ),
        EspnPlayer(
            espn_id=4429795,
            full_name="Justin Jefferson",
            first_name="Justin",
            last_name="Jefferson",
            position="WR",
            team="MIN",
            pro_team_id=16,
            rank_standard=3,
            rank_ppr=1,
            auction_value_standard=48,
            auction_value_ppr=60,
            percent_owned=98.2,
            percent_started=95.0,
            season_projection={"rec": 105.0, "rec_yds": 1450.0},
            season_projected_total=325.0,
            weekly_projections={1: {"rec": 6.0}, 2: {"rec": 7.0}},
            weekly_projected_totals={1: 19.5, 2: 21.0},
        ),
    ]


class TestEspnPipeline:
    @patch("nfl.espn_fantasy.pipeline.EspnFantasyClient")
    def test_pipeline_no_storage(self, mock_client_cls):
        """Pipeline produces frames without persisting."""
        mock_client_cls.return_value.fetch_all_players.return_value = _mock_players()

        result = run_pipeline(
            config=PipelineConfig(
                season=2025,
                storage_target="none",
                ingestion_date=date(2025, 8, 1),
            )
        )

        assert isinstance(result, PipelineRunResult)
        assert result.season == 2025
        assert result.player_count == 2
        assert "fact_espn_ranks" in result.frames
        assert "fact_espn_projections" in result.frames
        assert "fact_espn_weekly_projections" in result.frames
        assert result.polars_outputs == {}

    @patch("nfl.espn_fantasy.pipeline.EspnFantasyClient")
    def test_pipeline_ranks_frame_content(self, mock_client_cls):
        """Ranks frame contains expected columns and row count."""
        mock_client_cls.return_value.fetch_all_players.return_value = _mock_players()

        result = run_pipeline(config=PipelineConfig(season=2025))

        ranks = result.frames["fact_espn_ranks"]
        assert ranks.height == 2
        assert "espn_id" in ranks.columns
        assert "player" in ranks.columns
        assert "position" in ranks.columns
        assert "season" in ranks.columns

    @patch("nfl.espn_fantasy.pipeline.EspnFantasyClient")
    def test_pipeline_weekly_projections_frame(self, mock_client_cls):
        """Weekly projections frame has one row per player per week."""
        mock_client_cls.return_value.fetch_all_players.return_value = _mock_players()

        result = run_pipeline(config=PipelineConfig(season=2025))

        weekly = result.frames["fact_espn_weekly_projections"]
        # 2 players × 2 weeks each = 4 rows
        assert weekly.height == 4
        assert "week" in weekly.columns

    @patch("nfl.espn_fantasy.pipeline.EspnFantasyClient")
    def test_pipeline_empty_response(self, mock_client_cls):
        """Pipeline handles empty API response gracefully."""
        mock_client_cls.return_value.fetch_all_players.return_value = []

        result = run_pipeline(config=PipelineConfig(season=2025))

        assert result.player_count == 0
        assert result.frames["fact_espn_ranks"].height == 0

    @patch("nfl.espn_fantasy.pipeline.EspnFantasyClient")
    def test_pipeline_accepts_api_client(self, mock_client_cls):
        """Pipeline accepts a pre-built api_client and skips building one."""
        mock_client = MagicMock()
        mock_client.fetch_all_players.return_value = _mock_players()

        result = run_pipeline(config=PipelineConfig(season=2025), api_client=mock_client)

        mock_client_cls.assert_not_called()
        assert result.player_count == 2

    def test_pipeline_config_inherits_base(self):
        """PipelineConfig inherits from PipelineConfigBase."""
        from nfl.common.config import PipelineConfigBase

        cfg = PipelineConfig()
        assert isinstance(cfg, PipelineConfigBase)
        assert cfg.season == 2025
        assert cfg.storage_target == "none"
        assert cfg.polars_output_dir == "./output/espn_polars"
        assert cfg.dry_run is True

    def test_pipeline_config_defaults(self):
        """PipelineConfig has sensible ESPN-specific defaults."""
        cfg = PipelineConfig()
        assert cfg.timeout_seconds == 30
        assert cfg.max_players > 0
        assert cfg.batch_size > 0
