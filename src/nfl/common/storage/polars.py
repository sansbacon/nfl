"""Polars local file persistence adapter.

Writes Polars DataFrames as local Parquet, CSV, or NDJSON files.
Used for local development and testing workflows.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import polars as pl


def write_parquet(
    frames: Mapping[str, pl.DataFrame],
    output_dir: str | Path = "./output",
) -> dict[str, Path]:
    """Write Polars DataFrames as Parquet files with no catalog setup required.

    This is the lowest-friction persistence path: no Iceberg catalog, no
    additional infrastructure.  The resulting Parquet files are directly
    readable by DuckDB (``read_parquet``), Spark, and Unity Catalog external
    tables without re-ingestion.

    Parameters
    ----------
    frames : Mapping[str, pl.DataFrame]
        Entity name to DataFrame mapping.
    output_dir : str | Path
        Directory to write files into (created if missing).
        Defaults to ``./output``.

    Returns
    -------
    dict[str, Path]
        Entity name to written file path mapping.
    """
    return persist_with_polars(frames, output_dir=output_dir, file_format="parquet")


def persist_with_polars(
    frames: Mapping[str, pl.DataFrame],
    output_dir: str | Path,
    file_format: str = "parquet",
) -> dict[str, Path]:
    """Write Polars DataFrames as local files.

    Parameters
    ----------
    frames : Mapping[str, pl.DataFrame]
        Entity name to DataFrame mapping.
    output_dir : str | Path
        Directory to write files into (created if missing).
    file_format : str
        One of: parquet, csv, ndjson.

    Returns
    -------
    dict[str, Path]
        Entity name to written file path mapping.
    """
    fmt = file_format.strip().lower()
    if fmt not in {"parquet", "csv", "ndjson"}:
        raise ValueError("file_format must be one of: parquet, csv, ndjson")

    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for entity, frame in frames.items():
        path = base / f"{entity}.{fmt}"
        if fmt == "parquet":
            frame.write_parquet(path)
        elif fmt == "csv":
            frame.write_csv(path)
        else:
            frame.write_ndjson(path)
        written[entity] = path

    return written
