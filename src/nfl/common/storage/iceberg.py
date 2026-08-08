"""Shared PyIceberg persistence infrastructure.

Provides the common machinery for writing Polars DataFrames to Iceberg tables
via a local SQLite catalog. Source-specific modules supply their own namespace
configs and contract resolvers, then delegate to persist_to_iceberg().
"""

from __future__ import annotations

import contextlib
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

import polars as pl

IcebergWriteMode = Literal["append", "upsert"]


class ContractLike(Protocol):
    """Minimal interface for a validation contract (primary_key lookup)."""

    primary_key: tuple[str, ...]


# Type alias for a callable that resolves an entity name to its primary key tuple.
# Signature: (entity: str, sport: str | None) -> tuple[str, ...]
PrimaryKeyResolver = Callable[[str, str | None], tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class IcebergCatalogConfig:
    """Configuration for loading a PyIceberg catalog."""

    catalog_type: Literal["sql"] = "sql"
    catalog_name: str = "default"
    uri: str = "sqlite:///iceberg_catalog.db"
    warehouse: str = "./warehouse"


@dataclass(frozen=True, slots=True)
class IcebergNamespaceConfig:
    """Base namespace configuration for Iceberg routing.

    Subclass or replace with source-specific configs that map
    sport codes to namespace strings.
    """

    nfl: str = "nfl"
    common: str = "common"

    def resolve(self, sport: str | None) -> str:
        """Resolve a sport code to an Iceberg namespace."""
        if sport == "nfl":
            return self.nfl
        return self.common


@dataclass(frozen=True, slots=True)
class IcebergWriteResult:
    """Result of a single Iceberg write operation."""

    entity: str
    table_identifier: str
    mode: IcebergWriteMode
    source_rows: int
    written_rows: int
    skipped_by_idempotency: bool


class IdempotencyStore:
    """File-backed set of write digests to prevent duplicate writes."""

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
        self.store_path.write_text(
            json.dumps(sorted(self._entries), indent=2), encoding="utf-8"
        )


# ---------------------------------------------------------------------------
# Frame preparation utilities
# ---------------------------------------------------------------------------


def dedupe_for_upsert(frame: pl.DataFrame, primary_key: tuple[str, ...]) -> pl.DataFrame:
    """Deduplicate a frame by primary key columns (keeping first occurrence)."""
    keys = [k for k in primary_key if k in frame.columns]
    if not keys:
        return frame
    return frame.unique(subset=keys, keep="first").sort(keys)


def frame_digest(table_identifier: str, mode: IcebergWriteMode, frame: pl.DataFrame) -> str:
    """Compute a SHA-256 digest of a frame write operation for idempotency."""
    payload = {
        "table": table_identifier,
        "mode": mode,
        "columns": frame.columns,
        "rows": frame.to_dicts(),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def normalize_null_dtypes(frame: pl.DataFrame) -> pl.DataFrame:
    """Cast Null and List(Null) columns to Utf8 for Iceberg compatibility."""
    null_cols = [name for name, dtype in frame.schema.items() if dtype == pl.Null]
    list_null_cols = [
        name for name, dtype in frame.schema.items() if str(dtype) == "List(Null)"
    ]
    if not null_cols and not list_null_cols:
        return frame
    casts: list[pl.Expr] = [
        pl.col(col).cast(pl.Utf8, strict=False).alias(col) for col in null_cols
    ]
    casts.extend(
        pl.col(col).cast(pl.List(pl.Utf8), strict=False).alias(col)
        for col in list_null_cols
    )
    return frame.with_columns(casts)


# ---------------------------------------------------------------------------
# PyIceberg catalog operations
# ---------------------------------------------------------------------------


def load_pyiceberg_catalog(config: IcebergCatalogConfig) -> Any:
    """Load a PyIceberg catalog from configuration."""
    try:
        from pyiceberg.catalog import load_catalog
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pyiceberg is not installed in the active environment."
        ) from exc

    return load_catalog(
        config.catalog_name,
        type=config.catalog_type,
        uri=config.uri,
        warehouse=config.warehouse,
    )


def ensure_table_exists(
    catalog: Any, table_identifier: str, frame: pl.DataFrame
) -> Any:
    """Load an Iceberg table, creating it (and namespace) if needed."""
    from pyiceberg.exceptions import NamespaceAlreadyExistsError, NoSuchTableError

    try:
        return catalog.load_table(table_identifier)
    except NoSuchTableError:
        namespace, _table_name = table_identifier.rsplit(".", 1)
        with contextlib.suppress(NamespaceAlreadyExistsError):
            catalog.create_namespace(namespace)
        try:
            return catalog.create_table(
                identifier=table_identifier, schema=frame.to_arrow().schema
            )
        except Exception:
            return catalog.load_table(table_identifier)


def table_exists(catalog: Any, table_identifier: str) -> bool:
    """Check whether an Iceberg table exists."""
    try:
        catalog.load_table(table_identifier)
        return True
    except Exception:
        return False


def write_frame(catalog: Any, table_identifier: str, frame: pl.DataFrame) -> None:
    """Append a Polars DataFrame to an Iceberg table."""
    try:
        tbl = ensure_table_exists(catalog, table_identifier, frame)
    except Exception as exc:
        raise RuntimeError(
            f"Iceberg table '{table_identifier}' not found."
        ) from exc

    try:
        tbl.append(frame.to_arrow())
    except Exception as exc:
        raise RuntimeError(
            f"Failed appending to Iceberg table '{table_identifier}': {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# High-level persist orchestrator
# ---------------------------------------------------------------------------


def parse_entity_and_sport(
    frame_name: str, prefixes: tuple[str, ...] = ("nfl_", "nba_")
) -> tuple[str, str | None]:
    """Extract entity name and sport from a prefixed frame name."""
    for prefix in prefixes:
        if frame_name.startswith(prefix):
            sport = prefix.rstrip("_")
            return frame_name.removeprefix(prefix), sport
    return frame_name, None


def persist_to_iceberg(
    frames: Mapping[str, pl.DataFrame],
    *,
    catalog_config: IcebergCatalogConfig | None = None,
    namespace_config: IcebergNamespaceConfig | None = None,
    primary_key_resolver: PrimaryKeyResolver | None = None,
    frame_preprocessor: Callable[[str, pl.DataFrame], pl.DataFrame] | None = None,
    default_mode: IcebergWriteMode = "upsert",
    idempotency_store_path: str | Path = ".iceberg/write_log.json",
    sport_prefixes: tuple[str, ...] = ("nfl_", "nba_"),
    dry_run: bool = False,
) -> list[IcebergWriteResult]:
    """Write Polars DataFrames to Iceberg tables.

    Parameters
    ----------
    frames : Mapping[str, pl.DataFrame]
        Frame name (optionally sport-prefixed) to DataFrame mapping.
    catalog_config : IcebergCatalogConfig | None
        PyIceberg catalog connection config.
    namespace_config : IcebergNamespaceConfig | None
        Namespace routing config (sport → namespace).
    primary_key_resolver : PrimaryKeyResolver | None
        Callable (entity, sport) -> primary_key tuple for dedup.
        If None, no deduplication is performed.
    frame_preprocessor : Callable | None
        Optional (frame_name, frame) -> frame hook for source-specific
        transformations before write (e.g. stats serialization).
    default_mode : IcebergWriteMode
        Write mode: "append" or "upsert" (dedup then append).
    idempotency_store_path : str | Path
        Path to the JSON idempotency log.
    sport_prefixes : tuple[str, ...]
        Prefixes to parse from frame names to determine sport.
    dry_run : bool
        If True, computes results without writing to Iceberg.

    Returns
    -------
    list[IcebergWriteResult]
    """
    cat_cfg = catalog_config or IcebergCatalogConfig()
    ns_cfg = namespace_config or IcebergNamespaceConfig()
    store = IdempotencyStore(idempotency_store_path)

    catalog = None if dry_run else load_pyiceberg_catalog(cat_cfg)
    results: list[IcebergWriteResult] = []

    for frame_name, frame in frames.items():
        entity, sport = parse_entity_and_sport(frame_name, sport_prefixes)
        namespace = ns_cfg.resolve(sport)
        table_identifier = f"{namespace}.{entity}"
        mode: IcebergWriteMode = default_mode

        source_rows = frame.height

        # Dedup if upsert mode and resolver provided
        if mode == "upsert" and primary_key_resolver is not None:
            pk = primary_key_resolver(entity, sport)
            write_frame_data = dedupe_for_upsert(frame, pk)
        else:
            write_frame_data = frame

        # Source-specific preprocessing
        if frame_preprocessor is not None:
            write_frame_data = frame_preprocessor(frame_name, write_frame_data)

        # Normalize null types for Arrow/Iceberg compatibility
        write_frame_data = normalize_null_dtypes(write_frame_data)

        # Idempotency check
        digest = frame_digest(table_identifier, mode, write_frame_data)
        should_skip = store.contains(digest)
        if (
            should_skip
            and not dry_run
            and catalog is not None
            and not table_exists(catalog, table_identifier)
        ):
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

        # Write
        if not dry_run and write_frame_data.height > 0:
            write_frame(catalog, table_identifier, write_frame_data)

        store.add(digest)
        results.append(
            IcebergWriteResult(
                entity=frame_name,
                table_identifier=table_identifier,
                mode=mode,
                source_rows=source_rows,
                written_rows=write_frame_data.height,
                skipped_by_idempotency=False,
            )
        )

    return results
