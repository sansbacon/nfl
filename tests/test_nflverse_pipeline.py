from __future__ import annotations

from pathlib import Path

import polars as pl

from nfl.nflverse_fantasy.pipeline import PipelineConfig, run_pipeline
from nfl.nflverse_fantasy.storage.iceberg import IcebergNamespaceConfig


class _FakeClient:
    def _rows(self, dataset: str) -> list[dict]:
        return [
            {
                "_record_hash": f"{dataset}_1",
                "_dataset": dataset,
                "_loaded_at": "2026-07-18T00:00:00Z",
                "gsis_id": "GSIS_1",
                "display_name": "Austin Ekeler",
                "recent_team": "LAC",
                "position": "RB",
                "season": 2024,
            }
        ]

    def get_pbp(self, seasons=None):
        _ = seasons
        return self._rows("pbp")

    def get_player_stats(self, seasons=None):
        _ = seasons
        return self._rows("player_stats")

    def get_team_stats(self, seasons=None):
        _ = seasons
        return self._rows("team_stats")

    def get_schedules(self, seasons=None):
        _ = seasons
        return self._rows("schedules")

    def get_players(self):
        return self._rows("players")

    def get_rosters(self, seasons=None):
        _ = seasons
        return self._rows("rosters")

    def get_rosters_weekly(self, seasons=None):
        _ = seasons
        return self._rows("rosters_weekly")

    def get_snap_counts(self, seasons=None):
        _ = seasons
        return self._rows("snap_counts")

    def get_nextgen_stats(self, seasons=None):
        _ = seasons
        return self._rows("nextgen_stats")

    def get_ftn_charting(self, seasons=None):
        _ = seasons
        return self._rows("ftn_charting")

    def get_participation(self, seasons=None):
        _ = seasons
        return self._rows("participation")

    def get_draft_picks(self, seasons=None):
        _ = seasons
        return self._rows("draft_picks")

    def get_injuries(self, seasons=None):
        _ = seasons
        return self._rows("injuries")

    def get_contracts(self):
        return self._rows("contracts")

    def get_officials(self, seasons=None):
        _ = seasons
        return self._rows("officials")

    def get_combine(self):
        return self._rows("combine")

    def get_depth_charts(self, seasons=None):
        _ = seasons
        return self._rows("depth_charts")

    def get_trades(self, seasons=None):
        _ = seasons
        return self._rows("trades")

    def get_ff_playerids(self):
        return self._rows("ff_playerids")

    def get_ff_rankings(self, seasons=None):
        _ = seasons
        return self._rows("ff_rankings")

    def get_ff_opportunity(self, seasons=None):
        _ = seasons
        return self._rows("ff_opportunity")


def test_run_pipeline_without_persistence() -> None:
    result = run_pipeline(config=PipelineConfig(storage_target="none"), api_client=_FakeClient())

    assert "nvnfl_players" in result.frames
    assert "nvnfl_pbp" in result.frames
    assert result.polars_outputs == {}
    assert result.iceberg_outputs == []


def test_run_pipeline_with_both_persistence_targets(tmp_path: Path) -> None:
    result = run_pipeline(
        config=PipelineConfig(
            storage_target="both",
            polars_output_dir=tmp_path / "polars",
            iceberg_dry_run=True,
            iceberg_idempotency_store=tmp_path / "iceberg" / "write_log.json",
            iceberg_namespaces=IcebergNamespaceConfig(nfl="nvnfl", common="nvcommon"),
            enabled_entities=["players", "pbp"],
        ),
        api_client=_FakeClient(),
    )

    assert result.polars_outputs
    assert all(path.exists() for path in result.polars_outputs.values())
    assert result.iceberg_outputs
    assert any(item.table_identifier.startswith("nvnfl.") for item in result.iceberg_outputs)


def test_run_pipeline_with_standardization_enabled(monkeypatch) -> None:
    class _FakeStandardizer:
        def __init__(self, config=None):
            _ = config

        def standardize_batch(self, records):
            _ = records
            return type(
                "_StdResult",
                (),
                {
                    "tables": {
                        "std_standardized_outputs": pl.DataFrame(
                            {
                                "source_system": ["nflverse"],
                                "source_entity_id": ["GSIS_1"],
                                "canonical_player_id": ["P1"],
                                "canonical_team_id": ["LAC"],
                                "canonical_position_code": ["RB"],
                                "standardized_player_name": ["Austin Ekeler"],
                                "standardized_team_name": ["LAC"],
                                "standardized_position": ["RB"],
                                "player_confidence": [1.0],
                                "team_confidence": [1.0],
                                "position_confidence": [1.0],
                                "match_method_player": ["exact"],
                                "match_method_team": ["alias"],
                                "match_method_position": ["alias"],
                                "explanation_json": ["{}"],
                                "needs_review": [False],
                                "rescued": [False],
                            }
                        ),
                        "std_match_queue": pl.DataFrame([]),
                        "std_rescued_records": pl.DataFrame([]),
                        "std_source_to_canonical_map": pl.DataFrame([]),
                    }
                },
            )()

    monkeypatch.setattr("nfl.nflverse_fantasy.pipeline.EntityStandardizer", _FakeStandardizer)

    result = run_pipeline(
        config=PipelineConfig(storage_target="none", standardization_enabled=True, enabled_entities=["players"]),
        api_client=_FakeClient(),
    )

    assert result.standardization_result is not None
    assert "std_standardized_outputs" in result.frames
