"""Persistence helpers for standardization tables."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

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
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def persist_to_iceberg(
    frames: Mapping[str, pl.DataFrame],
    namespace_config: StandardizationIcebergNamespaceConfig | None = None,
    default_mode: WriteMode = "upsert",
    idempotency_store_path: str | Path | None = None,
    dry_run: bool = True,
) -> list[StandardizationIcebergWriteResult]:
    import warnings

    ns = namespace_config or StandardizationIcebergNamespaceConfig()

    store_path: Path | None
    if idempotency_store_path is not None:
        warnings.warn(
            "The .iceberg/write_log.json idempotency store is deprecated and will be "
            "removed in a future release.  Pass idempotency_store_path=None to opt out.",
            DeprecationWarning,
            stacklevel=2,
        )
        store_path = Path(idempotency_store_path)
        if store_path.exists():
            entries: set[str] = set(json.loads(store_path.read_text(encoding="utf-8")))
        else:
            entries = set()
    else:
        store_path = None
        entries = set()

    results: list[StandardizationIcebergWriteResult] = []
    for entity, frame in frames.items():
        table_identifier = _table_identifier(entity, ns)
        write_frame = _dedupe_for_upsert(frame, entity) if default_mode == "upsert" else frame
        digest = _frame_digest(table_identifier, default_mode, write_frame)
        if store_path is not None and digest in entries:
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

        if store_path is not None:
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

    if store_path is not None:
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text(json.dumps(sorted(entries), indent=2), encoding="utf-8")
    return results


def persist_to_uc_tables_std(
    frames: Mapping[str, pl.DataFrame],
    config: Any = None,
    dry_run: bool = False,
) -> list:
    """Write standardization DataFrames as UC Delta tables.

    Requires the ``nfl-databricks`` package.
    """
    try:
        from nfl_databricks.storage import UCTableConfig, persist_to_uc_tables
    except ImportError as exc:
        raise ImportError(
            "Unity Catalog storage requires the nfl-databricks package. "
            "Install it with: pip install nfl-databricks"
        ) from exc

    table_config = UCTableConfig(
        catalog="nfl",
        schema="std",
        write_mode="overwrite",
        table_prefix="std_",
    )
    return persist_to_uc_tables(frames, config=table_config, dry_run=dry_run)


def persist_to_uc_volume_std(
    frames: Mapping[str, pl.DataFrame],
    config: Any = None,
    dry_run: bool = False,
) -> list:
    """Write standardization DataFrames as files to a UC Volume.

    Requires the ``nfl-databricks`` package.
    """
    try:
        from nfl_databricks.storage import UCVolumeConfig, persist_to_uc_volume
    except ImportError as exc:
        raise ImportError(
            "Unity Catalog storage requires the nfl-databricks package. "
            "Install it with: pip install nfl-databricks"
        ) from exc

    volume_config = UCVolumeConfig(
        catalog="nfl",
        schema="std",
        volume="std_volume",
        file_format="parquet",
        subdirectory="standardization_output",
    )
    return persist_to_uc_volume(frames, config=volume_config, dry_run=dry_run)
