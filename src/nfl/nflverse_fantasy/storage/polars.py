"""Polars persistence adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import polars as pl


def persist_with_polars(
    frames: Mapping[str, pl.DataFrame],
    output_dir: str | Path,
    file_format: str = "parquet",
) -> dict[str, Path]:
    fmt = file_format.strip().lower()
    if fmt not in {"parquet", "csv", "ndjson"}:
        raise ValueError("file_format must be one of: parquet, csv, ndjson")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for entity, frame in frames.items():
        path = out_dir / f"{entity}.{fmt}"
        if fmt == "parquet":
            frame.write_parquet(path)
        elif fmt == "csv":
            frame.write_csv(path)
        else:
            frame.write_ndjson(path)
        written[entity] = path
    return written
