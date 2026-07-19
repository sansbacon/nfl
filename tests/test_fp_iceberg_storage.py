from __future__ import annotations

from pathlib import Path

import polars as pl

from nfl.fantasypros_fantasy.storage.iceberg import (
    IcebergNamespaceConfig,
    persist_to_iceberg,
    resolve_table_identifier,
)


def test_resolve_table_identifier_uses_fantasypros_namespaces() -> None:
    namespaces = IcebergNamespaceConfig(nfl="fpnfl", common="fpcommon")

    nfl_identifier, nfl_entity, nfl_sport = resolve_table_identifier("nfl_fp_adp_snapshot", namespaces)
    common_identifier, common_entity, common_sport = resolve_table_identifier("fp_player", namespaces)

    assert nfl_identifier == "fpnfl.fp_adp_snapshot"
    assert nfl_entity == "fp_adp_snapshot"
    assert nfl_sport == "nfl"

    assert common_identifier == "fpcommon.fp_player"
    assert common_entity == "fp_player"
    assert common_sport is None


def test_persist_to_iceberg_dry_run_upsert_and_idempotency(tmp_path: Path) -> None:
    frames = {
        "nfl_fp_adp_snapshot": pl.DataFrame(
            {
                "fp_player_id": ["p1", "p1"],
                "season": [2025, 2025],
                "rank": [1, 1],
                "adp": [1.4, 1.4],
                "effective_date": ["2026-07-18", "2026-07-18"],
                "is_current": [True, True],
            }
        )
    }

    store_path = tmp_path / "fp_write_log.json"

    first = persist_to_iceberg(
        frames=frames,
        namespace_config=IcebergNamespaceConfig(nfl="fpnfl", common="fpcommon"),
        idempotency_store_path=store_path,
        dry_run=True,
    )

    assert len(first) == 1
    assert first[0].table_identifier == "fpnfl.fp_adp_snapshot"
    assert first[0].written_rows == 1
    assert first[0].skipped_by_idempotency is False

    second = persist_to_iceberg(
        frames=frames,
        namespace_config=IcebergNamespaceConfig(nfl="fpnfl", common="fpcommon"),
        idempotency_store_path=store_path,
        dry_run=True,
    )

    assert len(second) == 1
    assert second[0].written_rows == 0
    assert second[0].skipped_by_idempotency is True
