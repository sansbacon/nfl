"""Warehouse and Iceberg catalog query utilities for Yahoo Fantasy datasets."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import polars as pl

DEFAULT_NAMESPACES: tuple[str, ...] = ("yahoo_common", "yhnfl")


@dataclass(frozen=True, slots=True)
class CatalogPaths:
    project_root: Path
    catalog_db_path: Path
    warehouse_path: Path
    catalog_uri: str
    warehouse_uri: str


@dataclass(frozen=True, slots=True)
class RegistrationReport:
    normalized_rows: int
    registered_tables: int
    tables_before: int
    tables_after: int


class WarehouseQueryError(RuntimeError):
    """Raised when a warehouse query action cannot be completed."""


class YahooWarehouseClient:
    """Helper for discovering and loading Yahoo Fantasy Iceberg tables as Polars frames."""

    def __init__(self, catalog: Any, paths: CatalogPaths) -> None:
        self._catalog = catalog
        self.paths = paths

    @classmethod
    def from_project_root(
        cls,
        project_root: str | Path | None = None,
        catalog_name: str = "yahoo",
        catalog_db_name: str = "iceberg_catalog.db",
        warehouse_dir: str = "warehouse",
    ) -> "YahooWarehouseClient":
        paths = _resolve_catalog_paths(
            project_root=project_root,
            catalog_db_name=catalog_db_name,
            warehouse_dir=warehouse_dir,
        )

        try:
            from pyiceberg.catalog import load_catalog
        except ModuleNotFoundError as exc:
            raise WarehouseQueryError("pyiceberg is not installed in the active environment.") from exc

        catalog = load_catalog(
            catalog_name,
            type="sql",
            uri=paths.catalog_uri,
            warehouse=paths.warehouse_uri,
        )
        return cls(catalog=catalog, paths=paths)

    @property
    def catalog(self) -> Any:
        return self._catalog

    def list_namespaces(self) -> list[str]:
        try:
            raw = self._catalog.list_namespaces()
        except Exception as exc:
            raise WarehouseQueryError(f"Could not list namespaces: {exc}") from exc

        normalized: list[str] = []
        for item in raw:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, tuple):
                normalized.append(".".join(str(part) for part in item))
            else:
                normalized.append(str(item))

        return sorted(set(normalized))

    def list_tables(self, namespace: str | None = None) -> list[str]:
        if namespace:
            return self._list_namespace_tables(namespace)

        tables: list[str] = []
        for ns in self.list_namespaces():
            tables.extend(self._list_namespace_tables(ns))
        return sorted(set(tables))

    def _list_namespace_tables(self, namespace: str) -> list[str]:
        try:
            listed = self._catalog.list_tables(namespace)
        except Exception:
            return []

        out: list[str] = []
        for item in listed:
            if isinstance(item, tuple) and len(item) == 2:
                out.append(f"{item[0]}.{item[1]}")
            else:
                out.append(str(item))
        return sorted(out)

    def load_table(self, table_identifier: str) -> pl.DataFrame:
        try:
            table = self._catalog.load_table(table_identifier)
            return pl.from_arrow(table.scan().to_arrow())
        except Exception as exc:
            raise WarehouseQueryError(f"Could not load table '{table_identifier}': {exc}") from exc

    def maybe_load(self, table_identifier: str) -> pl.DataFrame | None:
        try:
            return self.load_table(table_identifier)
        except WarehouseQueryError:
            return None

    def ensure_registered(self, namespaces: Iterable[str] = DEFAULT_NAMESPACES) -> RegistrationReport:
        normalized_rows = normalize_catalog_metadata_locations(
            catalog_db_path=self.paths.catalog_db_path,
            project_root=self.paths.project_root,
        )

        tables_before = sum(len(self._list_namespace_tables(ns)) for ns in namespaces)
        registered_tables = 0
        if tables_before == 0:
            registered_tables = register_tables_from_warehouse(
                catalog=self._catalog,
                warehouse=self.paths.warehouse_path,
                project_root=self.paths.project_root,
                namespaces=namespaces,
            )

        tables_after = sum(len(self._list_namespace_tables(ns)) for ns in namespaces)
        return RegistrationReport(
            normalized_rows=normalized_rows,
            registered_tables=registered_tables,
            tables_before=tables_before,
            tables_after=tables_after,
        )


def find_project_root(start_path: str | Path | None = None) -> Path:
    current = Path(start_path or Path.cwd()).resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            if current.name.lower() == "examples":
                raise WarehouseQueryError("Invalid project root resolved to 'examples'.")
            return current
        current = current.parent
    raise WarehouseQueryError("Cannot locate project root. Expected pyproject.toml in repository root.")


def _resolve_catalog_paths(
    project_root: str | Path | None,
    catalog_db_name: str,
    warehouse_dir: str,
) -> CatalogPaths:
    root = find_project_root(project_root)
    catalog_db_path = (root / catalog_db_name).resolve()
    warehouse_path = (root / warehouse_dir).resolve()
    return CatalogPaths(
        project_root=root,
        catalog_db_path=catalog_db_path,
        warehouse_path=warehouse_path,
        catalog_uri=f"sqlite:///{catalog_db_path.as_posix()}",
        warehouse_uri=warehouse_path.as_uri(),
    )


def _to_repo_relative_path(location: str, project_root: Path) -> str:
    value = location.replace("\\", "/")

    if value.lower().startswith("file:///"):
        value = value[8:]

    if re.match(r"^/[A-Za-z]:/", value):
        value = value[1:]

    root_prefix = project_root.as_posix().rstrip("/") + "/"
    if value.startswith(root_prefix):
        return value[len(root_prefix) :]

    return value


def normalize_catalog_metadata_locations(catalog_db_path: Path, project_root: Path) -> int:
    if not catalog_db_path.exists():
        return 0

    conn = sqlite3.connect(str(catalog_db_path))
    try:
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT catalog_name, table_namespace, table_name, metadata_location, previous_metadata_location FROM iceberg_tables"
        ).fetchall()

        updates: list[tuple[str, str | None, str, str, str]] = []
        for catalog_name, table_namespace, table_name, metadata_location, previous_metadata_location in rows:
            new_meta = (
                _to_repo_relative_path(metadata_location, project_root) if metadata_location else metadata_location
            )
            new_prev = (
                _to_repo_relative_path(previous_metadata_location, project_root)
                if previous_metadata_location
                else previous_metadata_location
            )
            if new_meta != metadata_location or new_prev != previous_metadata_location:
                updates.append((new_meta, new_prev, catalog_name, table_namespace, table_name))

        if updates:
            cur.executemany(
                """
                UPDATE iceberg_tables
                SET metadata_location = ?, previous_metadata_location = ?
                WHERE catalog_name = ? AND table_namespace = ? AND table_name = ?
                """,
                updates,
            )
            conn.commit()

        return len(updates)
    finally:
        conn.close()


def _latest_metadata_file(table_dir: Path) -> Path | None:
    metadata_dir = table_dir / "metadata"
    if not metadata_dir.exists():
        return None

    metadata_files = sorted(
        metadata_dir.glob("*.metadata.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return metadata_files[0] if metadata_files else None


def register_tables_from_warehouse(
    catalog: Any,
    warehouse: Path,
    project_root: Path,
    namespaces: Iterable[str],
) -> int:
    registered = 0
    for namespace in namespaces:
        ns_dir = warehouse / namespace
        if not ns_dir.exists():
            continue

        try:
            catalog.create_namespace(namespace)
        except Exception:
            pass

        for table_dir in [p for p in ns_dir.iterdir() if p.is_dir()]:
            table_identifier = f"{namespace}.{table_dir.name}"
            try:
                catalog.load_table(table_identifier)
                continue
            except Exception:
                pass

            metadata_file = _latest_metadata_file(table_dir)
            if metadata_file is None:
                continue

            metadata_rel = metadata_file.resolve().relative_to(project_root).as_posix()
            try:
                catalog.register_table(table_identifier, metadata_rel)
                registered += 1
            except Exception:
                continue

    return registered
