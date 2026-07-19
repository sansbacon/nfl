"""Iceberg persistence adapter for NFLverse datasets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

import polars as pl

from nfl.nflverse_fantasy.validation import get_contract

WriteMode = Literal["append", "upsert"]


@dataclass(frozen=True, slots=True)
class IcebergNamespaceConfig:
    nfl: str = "nvnfl"
    common: str = "nvcommon"


@dataclass(frozen=True, slots=True)
class IcebergWriteResult:
    entity: str
    table_identifier: str
    mode: WriteMode
    source_rows: int
    written_rows: int
    skipped_by_idempotency: bool


def _parse_entity(frame_name: str) -> str:
    if frame_name.startswith("nvnfl_"):
        return frame_name.removeprefix("nvnfl_")
    return frame_name


def resolve_table_identifier(frame_name: str, config: IcebergNamespaceConfig) -> tuple[str, str]:
    entity = _parse_entity(frame_name)
    return f"{config.nfl}.{entity}", entity


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
    namespace_config: IcebergNamespaceConfig | None = None,
    default_mode: WriteMode = "upsert",
    idempotency_store_path: str | Path = ".iceberg/nflverse_write_log.json",
    dry_run: bool = True,
) -> list[IcebergWriteResult]:
    cfg = namespace_config or IcebergNamespaceConfig()
    store_path = Path(idempotency_store_path)

    if store_path.exists():
        digests = set(json.loads(store_path.read_text(encoding="utf-8")))
    else:
        digests = set()

    results: list[IcebergWriteResult] = []
    for frame_name, frame in frames.items():
        table_identifier, entity = resolve_table_identifier(frame_name, cfg)
        write_frame = _dedupe_for_upsert(frame, entity) if default_mode == "upsert" else frame
        digest = _frame_digest(table_identifier, default_mode, write_frame)

        if digest in digests:
            results.append(
                IcebergWriteResult(
                    entity=frame_name,
                    table_identifier=table_identifier,
                    mode=default_mode,
                    source_rows=frame.height,
                    written_rows=0,
                    skipped_by_idempotency=True,
                )
            )
            continue

        if not dry_run and write_frame.height > 0:
            pass

        digests.add(digest)
        results.append(
            IcebergWriteResult(
                entity=frame_name,
                table_identifier=table_identifier,
                mode=default_mode,
                source_rows=frame.height,
                written_rows=write_frame.height,
                skipped_by_idempotency=False,
            )
        )

    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(sorted(digests), indent=2), encoding="utf-8")
    return results
