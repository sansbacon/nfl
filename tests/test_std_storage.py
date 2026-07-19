from __future__ import annotations

from pathlib import Path

import polars as pl

from nfl.entity_standardization.storage import (
    StandardizationIcebergNamespaceConfig,
    persist_to_iceberg,
    persist_with_polars,
)


def test_persist_with_polars_writes_files(tmp_path: Path) -> None:
    frames = {
        "std_standardized_outputs": pl.DataFrame(
            {
                "source_system": ["fantasypros"],
                "source_entity_id": ["fp_1"],
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
        )
    }

    written = persist_with_polars(frames, output_dir=tmp_path, file_format="parquet")
    assert written["std_standardized_outputs"].exists()


def test_persist_to_iceberg_dry_run_idempotency(tmp_path: Path) -> None:
    frames = {
        "std_source_to_canonical_map": pl.DataFrame(
            {
                "source_system": ["yahoo", "yahoo"],
                "source_entity_id": ["1001", "1001"],
                "canonical_player_id": ["P1", "P1"],
                "provenance": ["m", "m"],
                "valid_from": [None, None],
                "valid_to": [None, None],
            }
        )
    }
    store = tmp_path / "std_write_log.json"

    first = persist_to_iceberg(
        frames,
        namespace_config=StandardizationIcebergNamespaceConfig(core="std"),
        idempotency_store_path=store,
        dry_run=True,
    )
    assert first[0].written_rows == 1

    second = persist_to_iceberg(
        frames,
        namespace_config=StandardizationIcebergNamespaceConfig(core="std"),
        idempotency_store_path=store,
        dry_run=True,
    )
    assert second[0].written_rows == 0
    assert second[0].skipped_by_idempotency is True
