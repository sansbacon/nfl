from __future__ import annotations

from pathlib import Path

import polars as pl

from nfl.fantasypros_fantasy.storage.iceberg import (
    IcebergNamespaceConfig,
    persist_to_iceberg,
    resolve_table_identifier,
)


class _FakeTable:
    def __init__(self) -> None:
        self.appended_rows = 0

    def append(self, arrow_table):
        self.appended_rows += arrow_table.num_rows


class _FakeCatalog:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {}
        self.namespaces: set[str] = set()

    def load_table(self, table_identifier: str):
        if table_identifier not in self.tables:
            raise RuntimeError("missing table")
        return self.tables[table_identifier]

    def create_namespace(self, namespace: str):
        self.namespaces.add(namespace)

    def create_table(self, identifier: str, schema):
        _ = schema
        table = _FakeTable()
        self.tables[identifier] = table
        return table


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


def test_persist_to_iceberg_creates_missing_table(monkeypatch, tmp_path: Path) -> None:
    frames = {
        "fp_player": pl.DataFrame(
            {
                "fp_player_id": ["jamarr-chase"],
                "full_name": ["Ja'Marr Chase"],
                "first_name": ["Ja'Marr"],
                "last_name": ["Chase"],
                "position": ["WR"],
                "team": ["CIN"],
            }
        )
    }

    fake_catalog = _FakeCatalog()
    monkeypatch.setattr("nfl.fantasypros_fantasy.storage.iceberg._load_pyiceberg_catalog", lambda _cfg: fake_catalog)

    results = persist_to_iceberg(
        frames=frames,
        namespace_config=IcebergNamespaceConfig(nfl="fpnfl", common="fpcommon"),
        idempotency_store_path=tmp_path / "fp_write_log.json",
        dry_run=False,
    )

    assert len(results) == 1
    assert results[0].table_identifier == "fpcommon.fp_player"
    assert results[0].written_rows == 1
    assert results[0].skipped_by_idempotency is False
    assert "fpcommon" in fake_catalog.namespaces
    assert "fpcommon.fp_player" in fake_catalog.tables
    assert fake_catalog.tables["fpcommon.fp_player"].appended_rows == 1


def test_idempotency_does_not_skip_when_table_missing(monkeypatch, tmp_path: Path) -> None:
    frames = {
        "fp_player": pl.DataFrame(
            {
                "fp_player_id": ["bijan-robinson"],
                "full_name": ["Bijan Robinson"],
                "first_name": ["Bijan"],
                "last_name": ["Robinson"],
                "position": ["RB"],
                "team": ["ATL"],
            }
        )
    }

    store_path = tmp_path / "fp_write_log.json"
    _ = persist_to_iceberg(
        frames=frames,
        namespace_config=IcebergNamespaceConfig(nfl="fpnfl", common="fpcommon"),
        idempotency_store_path=store_path,
        dry_run=True,
    )

    fake_catalog = _FakeCatalog()
    monkeypatch.setattr("nfl.fantasypros_fantasy.storage.iceberg._load_pyiceberg_catalog", lambda _cfg: fake_catalog)

    results = persist_to_iceberg(
        frames=frames,
        namespace_config=IcebergNamespaceConfig(nfl="fpnfl", common="fpcommon"),
        idempotency_store_path=store_path,
        dry_run=False,
    )

    assert len(results) == 1
    assert results[0].skipped_by_idempotency is False
    assert results[0].written_rows == 1
    assert "fpcommon.fp_player" in fake_catalog.tables


def test_persist_to_iceberg_handles_null_typed_columns(monkeypatch, tmp_path: Path) -> None:
    frames = {
        "nfl_fp_adp_snapshot": pl.DataFrame(
            {
                "fp_player_id": ["p1"],
                "season": [2025],
                "rank": [1],
                "adp": [1.4],
                "adp_espn": [None],
                "adp_sleeper": [None],
                "adp_cbs": [None],
                "adp_nfl": [None],
                "adp_rtsports": [None],
                "adp_fantrax": [None],
                "adp_realtime": [None],
                "adp_formatted": ["1.01"],
                "high": [None],
                "low": [None],
                "stdev": [None],
                "bye_week": [None],
                "effective_date": ["2026-07-26"],
                "end_date": [None],
                "is_current": [True],
            },
            strict=False,
        )
    }

    fake_catalog = _FakeCatalog()
    monkeypatch.setattr("nfl.fantasypros_fantasy.storage.iceberg._load_pyiceberg_catalog", lambda _cfg: fake_catalog)

    results = persist_to_iceberg(
        frames=frames,
        namespace_config=IcebergNamespaceConfig(nfl="fpnfl", common="fpcommon"),
        idempotency_store_path=tmp_path / "fp_write_log.json",
        dry_run=False,
    )

    assert len(results) == 1
    assert results[0].table_identifier == "fpnfl.fp_adp_snapshot"
    assert results[0].written_rows == 1
    assert "fpnfl.fp_adp_snapshot" in fake_catalog.tables
