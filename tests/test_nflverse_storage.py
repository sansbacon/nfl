from __future__ import annotations

from pathlib import Path

import polars as pl

from nfl.nflverse_fantasy.storage.iceberg import IcebergNamespaceConfig, persist_to_iceberg, resolve_table_identifier


def test_resolve_table_identifier_uses_nvnfl_namespace() -> None:
    identifier, entity = resolve_table_identifier("nvnfl_players", IcebergNamespaceConfig())
    assert identifier == "nvnfl.players"
    assert entity == "players"


def test_persist_to_iceberg_dry_run_idempotency(tmp_path: Path) -> None:
    frames = {
        "nvnfl_players": pl.DataFrame(
            {
                "_record_hash": ["r1", "r1"],
                "_dataset": ["players", "players"],
                "_loaded_at": ["2026-07-18T00:00:00Z", "2026-07-18T00:00:00Z"],
                "gsis_id": ["GSIS_1", "GSIS_1"],
            }
        )
    }

    store = tmp_path / "nflverse_write_log.json"
    first = persist_to_iceberg(frames, idempotency_store_path=store, dry_run=True)
    assert first[0].written_rows == 1

    second = persist_to_iceberg(frames, idempotency_store_path=store, dry_run=True)
    assert second[0].written_rows == 0
    assert second[0].skipped_by_idempotency is True
