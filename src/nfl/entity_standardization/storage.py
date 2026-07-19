"""Persistence helpers for standardization tables."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

import polars as pl

from nfl.entity_standardization.validation import get_contract

WriteMode = Literal["append", "upsert"]


@dataclass(frozen=True, slots=True)
class StandardizationIcebergNamespaceConfig:
    core: str = "std"


@dataclass(frozen=True, slots=True)
class StandardizationIcebergWriteResult:
    entity: str
    table_identifier: str
    mode: WriteMode
    source_rows: int
    written_rows: int
    skipped_by_idempotency: bool


def persist_with_polars(
    frames: Mapping[str, pl.DataFrame],
    output_dir: str | Path,
    file_format: str = "parquet",
) -> dict[str, Path]:
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


def _table_identifier(entity: str, namespace: StandardizationIcebergNamespaceConfig) -> str:
    return f"{namespace.core}.{entity}"


def _dedupe_for_upsert(frame: pl.DataFrame, entity: str) -> pl.DataFrame:
    contract = get_contract(entity)
    keys = [k for k in contract.primary_key if k in frame.columns]
    if not keys:
        return frame
    return frame.unique(subset=keys, keep="first").sort(keys)


def _frame_digest(table_identifier: str, mode: WriteMode, frame: pl.DataFrame) -> str:
    payload = {
        "table": table_identifier,
        "mode": mode,
        "columns": frame.columns,
        "rows": frame.to_dicts(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def persist_to_iceberg(
    frames: Mapping[str, pl.DataFrame],
    namespace_config: StandardizationIcebergNamespaceConfig | None = None,
    default_mode: WriteMode = "upsert",
    idempotency_store_path: str | Path = ".iceberg/std_write_log.json",
    dry_run: bool = True,
) -> list[StandardizationIcebergWriteResult]:
    ns = namespace_config or StandardizationIcebergNamespaceConfig()
    store_path = Path(idempotency_store_path)
    if store_path.exists():
        entries = set(json.loads(store_path.read_text(encoding="utf-8")))
    else:
        entries = set()

    results: list[StandardizationIcebergWriteResult] = []
    for entity, frame in frames.items():
        table_identifier = _table_identifier(entity, ns)
        write_frame = _dedupe_for_upsert(frame, entity) if default_mode == "upsert" else frame
        digest = _frame_digest(table_identifier, default_mode, write_frame)
        if digest in entries:
            results.append(
                StandardizationIcebergWriteResult(
                    entity=entity,
                    table_identifier=table_identifier,
                    mode=default_mode,
                    source_rows=frame.height,
                    written_rows=0,
                    skipped_by_idempotency=True,
                )
            )
            continue

        if not dry_run and write_frame.height > 0:
            # Placeholder for catalog append implementation.
            pass

        entries.add(digest)
        results.append(
            StandardizationIcebergWriteResult(
                entity=entity,
                table_identifier=table_identifier,
                mode=default_mode,
                source_rows=frame.height,
                written_rows=write_frame.height,
                skipped_by_idempotency=False,
            )
        )

    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(sorted(entries), indent=2), encoding="utf-8")
    return results
