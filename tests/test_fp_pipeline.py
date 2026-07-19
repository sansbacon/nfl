from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl

from nfl.fantasypros_fantasy.pipeline import PipelineConfig, run_pipeline
from nfl.fantasypros_fantasy.storage.iceberg import IcebergNamespaceConfig


class _FakeClient:
    def get_players(self, season: int) -> list[dict]:
        _ = season
        return [
            {
                "fp_player_id": "justin-jefferson",
                "full_name": "Justin Jefferson",
                "first_name": "Justin",
                "last_name": "Jefferson",
                "position": "WR",
                "team": "MIN",
            }
        ]

    def get_adp_snapshots(self, season: int, effective_date: date | None = None) -> list[dict]:
        return [
            {
                "fp_player_id": "justin-jefferson",
                "season": season,
                "rank": 1,
                "adp": 1.4,
                "effective_date": effective_date or date(2026, 7, 18),
                "is_current": True,
                "end_date": None,
            }
        ]


def test_run_pipeline_without_persistence() -> None:
    yahoo_players = [
        {
            "yahoo_player_id": 1001,
            "full_name": "Justin Jefferson",
            "first_name": "Justin",
            "last_name": "Jefferson",
            "display_position": "WR",
        }
    ]

    result = run_pipeline(
        season=2025,
        sport="nfl",
        api_client=_FakeClient(),
        yahoo_players=yahoo_players,
        config=PipelineConfig(storage_target="none", effective_date=date(2026, 7, 18)),
    )

    assert result.season == 2025
    assert "fp_player" in result.frames
    assert "nfl_fp_adp_snapshot" in result.frames
    assert "nfl_fp_yahoo_player_map" in result.frames
    assert "nfl_fp_current_adp" in result.frames
    assert result.frames["nfl_fp_current_adp"].height == 1
    assert result.frames["nfl_fp_current_adp"]["position_rank"].to_list() == [1]
    assert result.polars_outputs == {}
    assert result.iceberg_outputs == []


def test_run_pipeline_with_both_persistence_targets(tmp_path: Path) -> None:
    result = run_pipeline(
        season=2025,
        sport="nfl",
        api_client=_FakeClient(),
        yahoo_players=[],
        config=PipelineConfig(
            storage_target="both",
            effective_date=date(2026, 7, 18),
            polars_output_dir=tmp_path / "polars",
            polars_file_format="parquet",
            iceberg_dry_run=True,
            iceberg_idempotency_store=tmp_path / "iceberg" / "write_log.json",
            iceberg_namespaces=IcebergNamespaceConfig(nfl="fpnfl", common="fpcommon"),
        ),
    )

    assert result.polars_outputs
    assert all(path.exists() for path in result.polars_outputs.values())
    assert result.iceberg_outputs
    assert any(
        write_result.table_identifier.startswith("fpnfl.") or write_result.table_identifier.startswith("fpcommon.")
        for write_result in result.iceberg_outputs
    )


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
                                "source_system": ["fantasypros"],
                                "source_entity_id": ["justin-jefferson"],
                                "canonical_player_id": ["P1"],
                                "canonical_team_id": ["MIN"],
                                "canonical_position_code": ["WR"],
                                "standardized_player_name": ["Justin Jefferson"],
                                "standardized_team_name": ["MIN"],
                                "standardized_position": ["WR"],
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

    monkeypatch.setattr("nfl.fantasypros_fantasy.pipeline.EntityStandardizer", _FakeStandardizer)

    result = run_pipeline(
        season=2025,
        sport="nfl",
        api_client=_FakeClient(),
        yahoo_players=[],
        config=PipelineConfig(
            storage_target="none",
            effective_date=date(2026, 7, 18),
            standardization_enabled=True,
        ),
    )

    assert result.standardization_result is not None
    assert "std_standardized_outputs" in result.frames
