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

# Ibis backend type — the primary mechanism for selecting execution engine.
BackendType = Literal["duckdb", "polars", "pyspark", "datafusion"]


@dataclass(frozen=True, slots=True)
class PipelineConfigBase:
    """Base configuration shared by all source pipelines.

    Subclasses add source-specific fields (API keys, source URLs,
    custom table configs, etc.) while inheriting the universal options.

    Parameters
    ----------
    season : int
        NFL season year to process.
    backend : BackendType
        Ibis backend for transforms and persistence.
    duckdb_path : str | Path
        Path to the DuckDB database file (used when backend="duckdb").
    pyspark_catalog : str
        Unity Catalog name (used when backend="pyspark").
    pyspark_schema : str
        Schema name (used when backend="pyspark").
    dry_run : bool
        If True, reports what would be written without executing writes.
    ingestion_date : date | None
        Override for the ingestion timestamp (defaults to today).
    """

    season: int = 2025
    backend: BackendType = "duckdb"
    duckdb_path: str | Path = "./output/nfl.duckdb"
    pyspark_catalog: str = "nfl"
    pyspark_schema: str = "default"
    dry_run: bool = True
    ingestion_date: date | None = None

    @property
    def effective_date(self) -> date:
        """Resolved ingestion date (defaults to today if not set)."""
        return self.ingestion_date or date.today()
