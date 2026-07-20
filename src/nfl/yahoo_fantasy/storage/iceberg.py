"""PyIceberg persistence adapter interfaces."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Literal

import polars as pl

from nfl.yahoo_fantasy.validation import get_contract

WriteMode = Literal["append", "upsert"]
SportCode = Literal["nfl", "nba"]


@dataclass(frozen=True, slots=True)
class IcebergCatalogConfig:
    catalog_type: Literal["sql"] = "sql"
    catalog_name: str = "yahoo"
    uri: str = "sqlite:///iceberg_catalog.db"
    warehouse: str = "./warehouse"


@dataclass(frozen=True, slots=True)
class IcebergNamespaceConfig:
    nfl: str = "yhnfl"
    nba: str = "ynbna"


@dataclass(frozen=True, slots=True)
class IcebergWriteResult:
    entity: str
    table_identifier: str
    mode: WriteMode
    source_rows: int
    written_rows: int
    skipped_by_idempotency: bool


class _IdempotencyStore:
    def __init__(self, store_path: str | Path) -> None:
        self.store_path = Path(store_path)
        self._entries = self._load()

    def _load(self) -> set[str]:
        if not self.store_path.exists():
            return set()
        try:
            payload = json.loads(self.store_path.read_text(encoding="utf-8"))
            return set(str(item) for item in payload) if isinstance(payload, list) else set()
        except (OSError, json.JSONDecodeError):
            return set()

    def contains(self, digest: str) -> bool:
        return digest in self._entries

    def add(self, digest: str) -> None:
        self._entries.add(digest)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(sorted(self._entries), indent=2), encoding="utf-8")


def _parse_entity_and_sport(frame_name: str) -> tuple[str, SportCode | None]:
    if frame_name.startswith("nfl_"):
        return frame_name.removeprefix("nfl_"), "nfl"
    if frame_name.startswith("nba_"):
        return frame_name.removeprefix("nba_"), "nba"
    return frame_name, None


def resolve_namespace(sport: SportCode | None, namespace_config: IcebergNamespaceConfig) -> str:
    if sport == "nfl":
        return namespace_config.nfl
    if sport == "nba":
        return namespace_config.nba
    return "yahoo_common"


def resolve_table_identifier(
    frame_name: str,
    namespace_config: IcebergNamespaceConfig,
) -> tuple[str, str, SportCode | None]:
    entity, sport = _parse_entity_and_sport(frame_name)
    return f"{resolve_namespace(sport, namespace_config)}.{entity}", entity, sport


def _dedupe_for_upsert(frame: pl.DataFrame, primary_key: tuple[str, ...]) -> pl.DataFrame:
    keys = [k for k in primary_key if k in frame.columns]
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


def _normalize_null_dtypes(frame: pl.DataFrame) -> pl.DataFrame:
    null_cols = [name for name, dtype in frame.schema.items() if dtype == pl.Null]
    list_null_cols = [name for name, dtype in frame.schema.items() if str(dtype) == "List(Null)"]
    if not null_cols and not list_null_cols:
        return frame
    casts: list[pl.Expr] = [pl.col(col).cast(pl.Utf8, strict=False).alias(col) for col in null_cols]
    casts.extend(pl.col(col).cast(pl.List(pl.Utf8), strict=False).alias(col) for col in list_null_cols)
    return frame.with_columns(casts)


def _load_pyiceberg_catalog(config: IcebergCatalogConfig) -> Any:
    try:
        from pyiceberg.catalog import load_catalog
    except ModuleNotFoundError as exc:
        raise RuntimeError("pyiceberg is not installed in the active environment.") from exc

    return load_catalog(
        config.catalog_name,
        type=config.catalog_type,
        uri=config.uri,
        warehouse=config.warehouse,
    )


def _ensure_table_exists(catalog: Any, table_identifier: str, frame: pl.DataFrame) -> Any:
    from pyiceberg.exceptions import NamespaceAlreadyExistsError, NoSuchTableError

    try:
        return catalog.load_table(table_identifier)
    except NoSuchTableError:
        namespace, _table_name = table_identifier.rsplit(".", 1)
        try:
            catalog.create_namespace(namespace)
        except NamespaceAlreadyExistsError:
            pass
        return catalog.create_table(identifier=table_identifier, schema=frame.to_arrow().schema)


def _write_frame_with_pyiceberg(catalog: Any, table_identifier: str, frame: pl.DataFrame) -> None:
    try:
        table = _ensure_table_exists(catalog, table_identifier, frame)
    except Exception as exc:
        raise RuntimeError(f"Iceberg table '{table_identifier}' not found.") from exc

    try:
        table.append(frame.to_arrow())
    except Exception as exc:
        raise RuntimeError(f"Failed appending to Iceberg table '{table_identifier}': {exc}") from exc


def _table_exists(catalog: Any, table_identifier: str) -> bool:
    try:
        catalog.load_table(table_identifier)
        return True
    except Exception:
        return False


def persist_to_iceberg(
    frames: Mapping[str, pl.DataFrame],
    catalog_config: IcebergCatalogConfig | None = None,
    namespace_config: IcebergNamespaceConfig | None = None,
    default_mode: WriteMode = "upsert",
    idempotency_store_path: str | Path = ".iceberg/write_log.json",
    dry_run: bool = False,
) -> list[IcebergWriteResult]:
    catalog_cfg = catalog_config or IcebergCatalogConfig()
    ns_cfg = namespace_config or IcebergNamespaceConfig()
    store = _IdempotencyStore(idempotency_store_path)

    catalog = None if dry_run else _load_pyiceberg_catalog(catalog_cfg)
    results: list[IcebergWriteResult] = []

    for frame_name, frame in frames.items():
        table_identifier, entity, sport = resolve_table_identifier(frame_name, ns_cfg)
        mode: WriteMode = default_mode

        source_rows = frame.height
        contract = get_contract(entity=entity, sport=sport)
        write_frame = _dedupe_for_upsert(frame, contract.primary_key) if mode == "upsert" else frame
        write_frame = _normalize_null_dtypes(write_frame)

        digest = _frame_digest(table_identifier, mode, write_frame)
        should_skip = store.contains(digest)
        if should_skip and not dry_run and catalog is not None and not _table_exists(catalog, table_identifier):
            should_skip = False

        if should_skip:
            results.append(
                IcebergWriteResult(
                    entity=frame_name,
                    table_identifier=table_identifier,
                    mode=mode,
                    source_rows=source_rows,
                    written_rows=0,
                    skipped_by_idempotency=True,
                )
            )
            continue

        if not dry_run and write_frame.height > 0:
            _write_frame_with_pyiceberg(catalog, table_identifier, write_frame)

        store.add(digest)
        results.append(
            IcebergWriteResult(
                entity=frame_name,
                table_identifier=table_identifier,
                mode=mode,
                source_rows=source_rows,
                written_rows=write_frame.height,
                skipped_by_idempotency=False,
            )
        )

    return results
