"""Persistence helpers for standardization tables."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import polars as pl

from nfl.common.storage import (
    UCTableConfig,
    UCVolumeConfig,
    UCWriteResult,
    VolumeFileFormat,
    persist_to_uc_tables,
    persist_to_uc_volume,
)
from nfl.common.storage import (
    WriteMode as UCWriteMode,
)
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


@dataclass(frozen=True, slots=True)
class StandardizationUCTableConfig:
    """UC table configuration for entity standardization."""

    catalog: str = "nfl"
    schema: str = "std"
    write_mode: UCWriteMode = "overwrite"
    merge_keys: tuple[str, ...] = ()
    table_prefix: str = "std_"
    table_properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StandardizationUCVolumeConfig:
    """UC volume configuration for entity standardization."""

    catalog: str = "nfl"
    schema: str = "std"
    volume: str = "std_volume"
    file_format: VolumeFileFormat = "parquet"
    subdirectory: str = "standardization_output"

    @property
    def base_path(self) -> str:
        parts = f"/Volumes/{self.catalog}/{self.schema}/{self.volume}"
        if self.subdirectory:
            parts = f"{parts}/{self.subdirectory.strip('/')}"
        return parts


def persist_to_uc_tables_std(
    frames: Mapping[str, pl.DataFrame],
    config: StandardizationUCTableConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write standardization DataFrames as UC Delta tables."""
    cfg = config or StandardizationUCTableConfig()
    table_config = UCTableConfig(
        catalog=cfg.catalog,
        schema=cfg.schema,
        write_mode=cfg.write_mode,
        merge_keys=cfg.merge_keys,
        table_prefix=cfg.table_prefix,
        table_properties=cfg.table_properties,
    )
    return persist_to_uc_tables(frames, config=table_config, dry_run=dry_run)


def persist_to_uc_volume_std(
    frames: Mapping[str, pl.DataFrame],
    config: StandardizationUCVolumeConfig | None = None,
    dry_run: bool = False,
) -> list[UCWriteResult]:
    """Write standardization DataFrames as files to a UC Volume."""
    cfg = config or StandardizationUCVolumeConfig()
    volume_config = UCVolumeConfig(
        catalog=cfg.catalog,
        schema=cfg.schema,
        volume=cfg.volume,
        file_format=cfg.file_format,
        subdirectory=cfg.subdirectory,
    )
    return persist_to_uc_volume(frames, config=volume_config, dry_run=dry_run)
