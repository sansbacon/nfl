"""Tests for nfl.common Ibis infrastructure.

Covers: backend factory, ibis_writer, scd2, validation, crosswalk.
All tests use DuckDB :memory: for speed.
"""

from __future__ import annotations

import ibis
import pyarrow as pa
import pytest

from nfl.common.backend import get_backend, get_backend_from_env
from nfl.common.config import PipelineConfigBase
from nfl.common.storage import WriteResult, compute_record_hash, merge_scd2, persist_tables
from nfl.common.validation import (
    ContractValidationError,
    EntityContract,
    validate_ibis_table,
    validate_not_empty,
    validate_primary_key,
)


@pytest.fixture
def backend():
    """Fresh DuckDB in-memory backend per test."""
    return ibis.duckdb.connect(":memory:")


# ---------------------------------------------------------------------------
# Backend factory
# ---------------------------------------------------------------------------


class TestBackendFactory:
    def test_get_backend_duckdb_memory(self):
        config = PipelineConfigBase(backend="duckdb", duckdb_path=":memory:")
        b = get_backend(config)
        assert b.name == "duckdb"

    def test_get_backend_explicit_override(self):
        config = PipelineConfigBase(backend="polars")
        b = get_backend(config, backend="duckdb", duckdb_path=":memory:")
        assert b.name == "duckdb"

    def test_get_backend_unsupported_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            get_backend(backend="nosuchbackend")

    def test_get_backend_from_env(self, monkeypatch):
        monkeypatch.setenv("NFL_BACKEND", "duckdb")
        monkeypatch.setenv("NFL_DUCKDB_PATH", ":memory:")
        b = get_backend_from_env()
        assert b.name == "duckdb"


# ---------------------------------------------------------------------------
# persist_tables
# ---------------------------------------------------------------------------


class TestPersistTables:
    def test_persist_and_read_back(self, backend):
        data = ibis.memtable({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        results = persist_tables({"dim_test": data}, backend, schema="main")

        assert len(results) == 1
        assert isinstance(results[0], WriteResult)
        assert results[0].source_rows == 3

        read_back = backend.table("dim_test", database="main")
        assert int(read_back.count().execute()) == 3

    def test_persist_dry_run(self, backend):
        data = ibis.memtable({"x": [1, 2]})
        results = persist_tables({"fact_test": data}, backend, dry_run=True)
        assert results[0].written_rows == 0

    def test_persist_with_prefix(self, backend):
        data = ibis.memtable({"v": [10]})
        results = persist_tables(
            {"scores": data}, backend, schema="main", table_prefix="stg_"
        )
        assert results[0].target == "main.stg_scores"
        read_back = backend.table("stg_scores", database="main")
        assert int(read_back.count().execute()) == 1


# ---------------------------------------------------------------------------
# SCD2
# ---------------------------------------------------------------------------


class TestSCD2:
    def test_compute_record_hash_adds_column(self, backend):
        t = ibis.memtable({"id": [1, 2], "name": ["a", "b"]})
        result = compute_record_hash(t)
        assert "_record_hash" in result.columns
        df = result.execute()
        assert df["_record_hash"].notna().all()

    def test_scd2_bootstrap(self, backend):
        source = ibis.memtable({
            "player_id": ["p1", "p2", "p3"],
            "name": ["Alice", "Bob", "Charlie"],
        })
        source = compute_record_hash(source)

        stats = merge_scd2(
            source=source,
            target_name="main.dim_players",
            natural_keys=("player_id",),
            backend=backend,
        )
        assert stats["inserted"] == 3
        assert stats["expired"] == 0
        assert stats["unchanged"] == 0

    def test_scd2_update_expires_changed(self, backend):
        # Bootstrap
        source_v1 = ibis.memtable({
            "player_id": ["p1", "p2"],
            "name": ["Alice", "Bob"],
        })
        source_v1 = compute_record_hash(source_v1)
        merge_scd2(source_v1, "main.dim_players", ("player_id",), backend)

        # Update: p1 changed, p2 unchanged
        source_v2 = ibis.memtable({
            "player_id": ["p1", "p2"],
            "name": ["Alice Updated", "Bob"],
        })
        source_v2 = compute_record_hash(source_v2)
        stats = merge_scd2(source_v2, "main.dim_players", ("player_id",), backend)

        assert stats["expired"] == 1
        assert stats["inserted"] == 1
        assert stats["unchanged"] == 1

        # Verify total rows
        target = backend.table("dim_players", database="main")
        assert int(target.count().execute()) == 3  # 2 current + 1 expired


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_validate_passes_valid_table(self):
        contract = EntityContract(
            name="test", required=("id", "name"), optional=("team",), primary_key=("id",)
        )
        t = ibis.memtable({"id": [1], "name": ["x"], "team": ["A"]})
        validate_ibis_table(t, contract)  # Should not raise

    def test_validate_missing_required_raises(self):
        contract = EntityContract(
            name="test", required=("id", "name"), optional=(), primary_key=("id",)
        )
        t = ibis.memtable({"id": [1]})
        with pytest.raises(ContractValidationError, match="Missing"):
            validate_ibis_table(t, contract)

    def test_validate_extra_columns_disallowed(self):
        contract = EntityContract(
            name="test", required=("id",), optional=("name",), primary_key=("id",)
        )
        t = ibis.memtable({"id": [1], "name": ["x"], "extra": ["y"]})
        with pytest.raises(ContractValidationError, match="Unexpected"):
            validate_ibis_table(t, contract, allow_extra_columns=False)

    def test_validate_not_empty_raises_on_empty(self):
        t = ibis.memtable(pa.table({"id": pa.array([], type=pa.int64())}))
        with pytest.raises(ContractValidationError, match="empty"):
            validate_not_empty(t, "test_entity")

    def test_validate_primary_key_detects_dupes(self):
        contract = EntityContract(
            name="test", required=("id",), optional=(), primary_key=("id",)
        )
        t = ibis.memtable({"id": [1, 1, 2]})
        with pytest.raises(ContractValidationError, match="duplicate"):
            validate_primary_key(t, contract)


# ---------------------------------------------------------------------------
# Crosswalk
# ---------------------------------------------------------------------------


class TestCrosswalk:
    def test_load_and_read_crosswalk(self, backend, monkeypatch):
        from unittest.mock import patch

        mock_data = pa.table({
            "mfl_id": ["1", "2", "3"],
            "name": ["Player A", "Player B", "Player C"],
            "yahoo_id": ["y1", "y2", "y3"],
        })

        with patch("nfl.common.crosswalk._load_nflreadpy_arrow", return_value=mock_data):
            from nfl.common.crosswalk import load_crosswalk, read_crosswalk

            result = load_crosswalk(backend, database="main")
            assert int(result.count().execute()) == 3

            read_back = read_crosswalk(backend, database="main")
            assert int(read_back.count().execute()) == 3
