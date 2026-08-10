"""Unified Ibis persistence layer.

Writes Ibis table expressions to the active backend using
``backend.create_table()`` (overwrite) or ``backend.insert()`` (append).
This replaces the per-backend adapters (polars.py, duckdb.py, iceberg.py)
with a single backend-agnostic write path.

Requires: pip install nfl[ibis]
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    import ibis

WriteMode = Literal["overwrite", "append"]


@dataclass(frozen=True, slots=True)
class WriteResult:
    """Result of a single Ibis table write operation.

    Attributes
    ----------
    entity : str
        Logical entity name (e.g. "dim_players", "fact_etr_ranks").
    target : str
        Fully qualified table name written to (e.g. "main.dim_players").
    mode : WriteMode
        Write mode used.
    source_rows : int
        Number of rows in the source expression.
    written_rows : int
        Number of rows actually written (0 for dry_run).
    """

    entity: str
    target: str
    mode: WriteMode
    source_rows: int
    written_rows: int


def _fully_qualified_name(schema: str, name: str, table_prefix: str) -> str:
    """Build schema-qualified table name with optional prefix."""
    table_name = f"{table_prefix}{name}" if table_prefix else name
    return f"{schema}.{table_name}"


def _parse_table_name(fq_name: str) -> tuple[str | None, str]:
    """Split 'schema.table' into (schema, table) for Ibis create_table.

    Ibis create_table takes the table name and schema (called 'database')
    as separate arguments. Passing 'schema.table' as the name creates a
    table literally named 'schema.table' which breaks raw SQL access.
    """
    if "." in fq_name:
        parts = fq_name.rsplit(".", 1)
        return parts[0], parts[1]
    return None, fq_name


def _count_rows(table: ibis.Table) -> int:
    """Materialize row count from an Ibis table expression."""
    return int(table.count().execute())


def persist_tables(
    tables: Mapping[str, ibis.Table],
    backend: ibis.BaseBackend,
    *,
    schema: str = "main",
    write_mode: WriteMode = "overwrite",
    table_prefix: str = "",
    dry_run: bool = False,
) -> list[WriteResult]:
    """Write Ibis table expressions to the active backend.

    Parameters
    ----------
    tables : Mapping[str, ibis.Table]
        Entity name to Ibis table expression mapping.
    backend : ibis.BaseBackend
        Connected Ibis backend to write to.
    schema : str
        Target schema (created if not exists on backends that support it).
    write_mode : WriteMode
        ``"overwrite"`` replaces the table; ``"append"`` inserts rows.
    table_prefix : str
        Optional prefix prepended to entity names when building the
        target table name.
    dry_run : bool
        If True, reports what would be written without executing writes.

    Returns
    -------
    list[WriteResult]
        Write results for each entity.

    Examples
    --------
    >>> import ibis
    >>> from nfl.common.storage.ibis_writer import persist_tables
    >>> backend = ibis.duckdb.connect(":memory:")
    >>> t = ibis.memtable({"player": ["Mahomes"], "rank": [1]})
    >>> results = persist_tables({"rankings": t}, backend)
    >>> results[0].target
    'main.rankings'
    """
    results: list[WriteResult] = []

    for entity, table in tables.items():
        fq_name = _fully_qualified_name(schema, entity, table_prefix)
        source_rows = _count_rows(table)

        if dry_run:
            results.append(
                WriteResult(
                    entity=entity,
                    target=fq_name,
                    mode=write_mode,
                    source_rows=source_rows,
                    written_rows=0,
                )
            )
            continue

        if source_rows == 0:
            # Skip empty tables but record the result
            results.append(
                WriteResult(
                    entity=entity,
                    target=fq_name,
                    mode=write_mode,
                    source_rows=0,
                    written_rows=0,
                )
            )
            continue

        db, tbl = _parse_table_name(fq_name)

        if write_mode == "overwrite":
            backend.create_table(tbl, table, database=db, overwrite=True)
        elif write_mode == "append":
            # create_table if not exists, then insert
            try:
                backend.table(tbl, database=db)
            except Exception:
                # Table doesn't exist yet — create it
                backend.create_table(tbl, table, database=db)
                results.append(
                    WriteResult(
                        entity=entity,
                        target=fq_name,
                        mode=write_mode,
                        source_rows=source_rows,
                        written_rows=source_rows,
                    )
                )
                continue
            backend.insert(tbl, table)
        else:
            raise ValueError(f"Unsupported write_mode: {write_mode!r}")

        results.append(
            WriteResult(
                entity=entity,
                target=fq_name,
                mode=write_mode,
                source_rows=source_rows,
                written_rows=source_rows,
            )
        )

    return results


def persist_from_polars(
    frames: Mapping[str, Any],
    backend: ibis.BaseBackend,
    *,
    schema: str = "main",
    write_mode: WriteMode = "overwrite",
    table_prefix: str = "",
    dry_run: bool = False,
) -> list[WriteResult]:
    """Convert Polars DataFrames to Ibis memtables and persist.

    Convenience bridge for code still producing pl.DataFrame outputs.
    Converts via Arrow (zero-copy) then delegates to ``persist_tables``.

    Parameters
    ----------
    frames : Mapping[str, pl.DataFrame]
        Entity name to Polars DataFrame mapping.
    backend : ibis.BaseBackend
        Connected Ibis backend.
    schema : str
        Target schema.
    write_mode : WriteMode
        Write mode.
    table_prefix : str
        Optional prefix for table names.
    dry_run : bool
        If True, reports without writing.

    Returns
    -------
    list[WriteResult]
    """
    import ibis

    ibis_tables: dict[str, ibis.Table] = {}
    for entity, frame in frames.items():
        ibis_tables[entity] = ibis.memtable(frame.to_arrow())

    return persist_tables(
        ibis_tables,
        backend,
        schema=schema,
        write_mode=write_mode,
        table_prefix=table_prefix,
        dry_run=dry_run,
    )
