"""Shared base configuration types for pipeline modules.

Source-specific pipeline configs (Yahoo, FantasyPros, Sleeper, etc.) can
inherit from PipelineConfigBase to get a consistent interface for common
fields while adding their own source-specific options.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

# "unity_catalog" and "uc_volume" require the nfl-databricks package.
StorageTarget = Literal["none", "polars", "unity_catalog", "uc_volume", "iceberg", "both"]


@dataclass(frozen=True, slots=True)
class PipelineConfigBase:
    """Base configuration shared by all source pipelines.

    Subclasses add source-specific fields (API keys, source URLs,
    custom table configs, etc.) while inheriting the universal options.

    Parameters
    ----------
    season : int
        NFL season year to process.
    storage_target : StorageTarget
        Where to persist output frames.
    polars_output_dir : str | Path
        Directory for local Polars file output.
    polars_file_format : str
        File format for Polars output ('parquet' or 'csv').
    dry_run : bool
        If True, reports what would be written without executing writes.
    ingestion_date : date | None
        Override for the ingestion timestamp (defaults to today).
    """

    season: int = 2025
    storage_target: StorageTarget = "none"
    polars_output_dir: str | Path = "./output"
    polars_file_format: str = "parquet"
    dry_run: bool = True
    ingestion_date: date | None = None

    @property
    def effective_date(self) -> date:
        """Resolved ingestion date (defaults to today if not set)."""
        return self.ingestion_date or date.today()
