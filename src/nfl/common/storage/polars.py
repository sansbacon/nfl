"""Polars local file persistence adapter.

Writes Polars DataFrames as local Parquet, CSV, or NDJSON files.
Used for local development and testing workflows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import polars as pl


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
