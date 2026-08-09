"""Unit tests for nfl_databricks.storage module."""

import pytest
import polars as pl

from nfl_databricks.storage import (
    UCTableConfig,
    UCVolumeConfig,
    UCWriteResult,
    persist_to_uc_tables,
    persist_to_uc_volume,
)


class TestUCTableConfig:
    def test_defaults(self):
        cfg = UCTableConfig()
        assert cfg.catalog == "nfl"
        assert cfg.schema == "default"
        assert cfg.write_mode == "overwrite"
        assert cfg.merge_keys == ()

    def test_custom_config(self):
        cfg = UCTableConfig(catalog="dev", schema="test", write_mode="merge", merge_keys=("id",))
        assert cfg.catalog == "dev"
        assert cfg.write_mode == "merge"
        assert cfg.merge_keys == ("id",)


class TestUCVolumeConfig:
    def test_base_path_no_subdir(self):
        cfg = UCVolumeConfig(catalog="nfl", schema="nv", volume="output")
        assert cfg.base_path == "/Volumes/nfl/nv/output"

    def test_base_path_with_subdir(self):
        cfg = UCVolumeConfig(catalog="nfl", schema="nv", volume="output", subdirectory="weekly")
        assert cfg.base_path == "/Volumes/nfl/nv/output/weekly"


class TestPersistToUCTablesDryRun:
    def test_dry_run_reports_writes(self):
        frames = {
            "players": pl.DataFrame({"id": [1, 2], "name": ["A", "B"]}),
            "teams": pl.DataFrame({"abbr": ["KC", "BUF"]}),
        }
        results = persist_to_uc_tables(frames, dry_run=True)
        assert len(results) == 2
        assert all(isinstance(r, UCWriteResult) for r in results)
        assert results[0].source_rows == 2
        assert results[0].target_type == "table"
        assert results[0].mode == "overwrite"

    def test_dry_run_empty_frame(self):
        frames = {"empty": pl.DataFrame({"x": []})}
        results = persist_to_uc_tables(frames, dry_run=True)
        assert results[0].source_rows == 0
        assert results[0].written_rows == 0


class TestPersistToUCVolumeDryRun:
    def test_dry_run_reports_writes(self):
        frames = {"stats": pl.DataFrame({"val": [1.0, 2.0]})}
        cfg = UCVolumeConfig(catalog="nfl", schema="nv", volume="out")
        results = persist_to_uc_volume(frames, config=cfg, dry_run=True)
        assert len(results) == 1
        assert results[0].target == "/Volumes/nfl/nv/out/stats.parquet"
        assert results[0].target_type == "volume"


@pytest.mark.integration
class TestPersistToUCTablesIntegration:
    """Tests requiring a live Spark session. Run with: pytest -m integration"""

    def test_overwrite_creates_table(self):
        pytest.skip("Requires Databricks runtime")
