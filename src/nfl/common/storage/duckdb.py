"""DuckDB persistence adapter.

Provides write/read utilities for persisting Polars DataFrames to a local
DuckDB database file (or in-memory). Supports overwrite, append, and
MERGE (upsert) write modes.

Requires: pip install nfl[duckdb]
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import polars as pl

WriteMode = Literal["append", "overwrite", "merge"]


def _import_duckdb() -> Any:
    """Lazy-import duckdb with a helpful error message."""
    try:
        import duckdb
    except ImportError as exc:
        raise ImportError(
            "DuckDB storage requires the duckdb package. "
            "Install it with: pip install nfl[duckdb]"
        ) from exc
    return duckdb


@dataclass(frozen=True, slots=True)
class DuckDBConfig:
    """Configuration for writing to a DuckDB database.

    Parameters
    ----------
    db_path : str | Path
        Path to the DuckDB database file. Use ":memory:" for an
        in-memory database (useful for testing).
    schema : str
        DuckDB schema to write tables into. Created if it does not exist.
    write_mode : WriteMode
        How to write data: "overwrite" replaces the table, "append" adds
        rows, "merge" performs an upsert on ``merge_keys``.
    merge_keys : tuple[str, ...]
        Column names for the MERGE join condition. Required when
        ``write_mode="merge"``.
    table_prefix : str
        Optional prefix prepended to entity names when building
        the target table name.
    """

    db_path: str | Path = "./output/nfl.duckdb"
    schema: str = "main"
    write_mode: WriteMode = "overwrite"
    merge_keys: tuple[str, ...] = ()
    table_prefix: str = ""


@dataclass(frozen=True, slots=True)
class DuckDBWriteResult:
    """Result of a single DuckDB write operation."""

    entity: str
    target: str
    mode: str
    source_rows: int
    written_rows: int


def _fully_qualified_table(config: DuckDBConfig, entity: str) -> str:
    """Build schema-qualified table name."""
    table_name = f"{config.table_prefix}{entity}" if config.table_prefix else entity
    return f"{config.schema}.{table_name}"


def get_connection(
    db_path: str | Path = "./output/nfl.duckdb",
    *,
    read_only: bool = False,
) -> Any:
    """Open (or create) a DuckDB connection.

    Parameters
    ----------
    db_path : str | Path
        Path to the database file, or ":memory:".
    read_only : bool
        If True, open in read-only mode.

    Returns
    -------
    duckdb.DuckDBPyConnection
    """
    duckdb = _import_duckdb()
    path_str = str(db_path)
    return duckdb.connect(path_str, read_only=read_only)


def persist_to_duckdb(
    frames: Mapping[str, pl.DataFrame],
    config: DuckDBConfig | None = None,
    *,
    connection: Any | None = None,
    dry_run: bool = False,
) -> list[DuckDBWriteResult]:
    """Write Polars DataFrames as DuckDB tables.

    Parameters
    ----------
    frames : Mapping[str, pl.DataFrame]
        Entity name to DataFrame mapping.
    config : DuckDBConfig | None
        Write configuration. Defaults to ``./output/nfl.duckdb``, schema ``main``.
    connection : duckdb.DuckDBPyConnection | None
        Optional existing connection. If provided, ``config.db_path`` is
        ignored and this connection is used directly (useful for :memory:
        or connection pooling). The caller is responsible for closing it.
    dry_run : bool
        If True, reports what would be written without executing writes.

    Returns
    -------
    list[DuckDBWriteResult]
        Write results for each entity.
    """
    cfg = config or DuckDBConfig()
    results: list[DuckDBWriteResult] = []

    if dry_run:
        for entity, frame in frames.items():
            results.append(
                DuckDBWriteResult(
                    entity=entity,
                    target=_fully_qualified_table(cfg, entity),
                    mode=cfg.write_mode,
                    source_rows=frame.height,
                    written_rows=frame.height if not frame.is_empty() else 0,
                )
            )
        return results

    conn = connection or get_connection(cfg.db_path)
    owns_connection = connection is None

    try:
        # Ensure schema exists
        if cfg.schema != "main":
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {cfg.schema}")

        for entity, frame in frames.items():
            fq_table = _fully_qualified_table(cfg, entity)
            source_rows = frame.height

            if frame.is_empty():
                results.append(
                    DuckDBWriteResult(
                        entity=entity,
                        target=fq_table,
                        mode=cfg.write_mode,
                        source_rows=0,
                        written_rows=0,
                    )
                )
                continue

            # Register the Polars DataFrame as a named relation (zero-copy via Arrow)
            conn.register("_source_df", frame.to_arrow())

            if cfg.write_mode == "overwrite":
                conn.execute(f"CREATE OR REPLACE TABLE {fq_table} AS SELECT * FROM _source_df")

            elif cfg.write_mode == "append":
                # Create table if it doesn't exist, then insert
                conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {fq_table} AS "
                    f"SELECT * FROM _source_df WHERE 1=0"
                )
                conn.execute(f"INSERT INTO {fq_table} SELECT * FROM _source_df")

            elif cfg.write_mode == "merge":
                if not cfg.merge_keys:
                    raise ValueError(
                        f"merge_keys must be specified for write_mode='merge' "
                        f"(entity: {entity})"
                    )
                _merge_into_table(conn, fq_table, cfg.merge_keys)

            conn.unregister("_source_df")

            results.append(
                DuckDBWriteResult(
                    entity=entity,
                    target=fq_table,
                    mode=cfg.write_mode,
                    source_rows=source_rows,
                    written_rows=source_rows,
                )
            )
    finally:
        if owns_connection:
            conn.close()

    return results


def _merge_into_table(
    conn: Any,
    target_table: str,
    merge_keys: tuple[str, ...],
) -> None:
    """MERGE INTO target using _source_df on merge_keys.

    Creates the target table if it does not exist.
    """
    # Check if target table exists
    schema_part, table_part = target_table.rsplit(".", 1)
    exists = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = ? AND table_name = ?",
        [schema_part, table_part],
    ).fetchone()[0]

    if not exists:
        conn.execute(f"CREATE TABLE {target_table} AS SELECT * FROM _source_df")
        return

    merge_condition = " AND ".join(
        f"target.\"{key}\" = source.\"{key}\"" for key in merge_keys
    )

    conn.execute(f"""
        MERGE INTO {target_table} AS target
        USING _source_df AS source
        ON {merge_condition}
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)


def compute_record_hash(
    frame: pl.DataFrame,
    *,
    exclude_columns: tuple[str, ...] = (),
    include_columns: tuple[str, ...] | None = None,
    hash_column: str = "_record_hash",
    separator: str = "|",
) -> pl.DataFrame:
    """Compute a deterministic content hash for each row in a Polars DataFrame.

    Used to generate the ``_record_hash`` column that ``merge_scd2`` needs
    for change detection. Hashes column values using xxHash-64 for speed.

    Exactly one of ``include_columns`` or ``exclude_columns`` should be
    specified. If neither is set, all columns are hashed.

    Parameters
    ----------
    frame : pl.DataFrame
        Input DataFrame.
    exclude_columns : tuple[str, ...]
        Columns to exclude from the hash (e.g. natural keys, SCD2 metadata).
        Ignored if ``include_columns`` is set.
    include_columns : tuple[str, ...] | None
        If provided, only these columns are hashed. Takes precedence over
        ``exclude_columns``.
    hash_column : str
        Name of the output hash column (default ``"_record_hash"``).
    separator : str
        Separator used between column values before hashing.

    Returns
    -------
    pl.DataFrame
        Original DataFrame with ``hash_column`` appended.

    Examples
    --------
    >>> df = pl.DataFrame({"season": [2024], "player": ["Mahomes"], "rank": [1]})
    >>> hashed = compute_record_hash(df, exclude_columns=("season", "player"))
    >>> hashed.columns
    ['season', 'player', 'rank', '_record_hash']
    """
    if include_columns is not None:
        cols_to_hash = [c for c in frame.columns if c in include_columns]
    elif exclude_columns:
        cols_to_hash = [c for c in frame.columns if c not in exclude_columns]
    else:
        cols_to_hash = frame.columns

    if not cols_to_hash:
        raise ValueError(
            "No columns selected for hashing. Check include_columns/exclude_columns."
        )

    # Cast all selected columns to string, concat with separator, then hash
    hash_expr = pl.concat_str(
        [pl.col(c).cast(pl.Utf8).fill_null("__NULL__") for c in cols_to_hash],
        separator=separator,
    ).hash().cast(pl.Utf8).alias(hash_column)

    return frame.with_columns(hash_expr)


def merge_scd2(
    frame: pl.DataFrame,
    target_table: str,
    natural_keys: tuple[str, ...],
    *,
    hash_column: str = "_record_hash",
    ingestion_date_column: str = "ingestion_date",
    end_date_column: str = "end_date",
    is_current_column: str = "is_current",
    end_date_sentinel: str = "9999-12-31",
    connection: Any | None = None,
    db_path: str | Path = "./output/nfl.duckdb",
) -> dict[str, int]:
    """Perform an SCD Type 2 merge into a DuckDB fact table.

    Implements the standard pattern used across the nfl project:
    1. Match incoming rows to current target rows on ``natural_keys``.
    2. If ``hash_column`` differs (row changed): expire the old row
       (set ``is_current=false``, ``end_date=today``) and insert the
       new row as current.
    3. If no match exists: insert as a new current row.
    4. Unmatched target rows are left untouched.

    The incoming ``frame`` must already contain the ``hash_column``.
    The ``ingestion_date_column``, ``end_date_column``, and
    ``is_current_column`` are managed by this function — they are
    added/overwritten on insert.

    Parameters
    ----------
    frame : pl.DataFrame
        Incoming fact rows (new snapshot).
    target_table : str
        Schema-qualified target table, e.g. ``"nfl.fact_etr_ranks"``.
    natural_keys : tuple[str, ...]
        Columns that form the business key (e.g.
        ``("season", "player", "position", "scoring_format")``).
    hash_column : str
        Column containing a content hash for change detection.
    ingestion_date_column : str
        Column name for the row's effective-from date.
    end_date_column : str
        Column name for the row's effective-to date.
    is_current_column : str
        Boolean column indicating the active row.
    end_date_sentinel : str
        Date string representing "no end" (default ``'9999-12-31'``).
    connection : duckdb.DuckDBPyConnection | None
        Optional existing connection.
    db_path : str | Path
        Path to the DuckDB file. Ignored if ``connection`` is provided.

    Returns
    -------
    dict[str, int]
        Counts: ``{"expired": N, "inserted": N, "unchanged": N}``.
    """
    conn = connection or get_connection(db_path)
    owns_connection = connection is None

    try:
        # Ensure target table exists; if not, create from frame with SCD2 columns
        schema_part, table_part = target_table.rsplit(".", 1)
        exists = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = ? AND table_name = ?",
            [schema_part, table_part],
        ).fetchone()[0]

        if not exists:
            # Bootstrap: create table from frame + SCD2 columns via SQL
            conn.register("_scd2_init", frame.to_arrow())
            conn.execute(
                f"CREATE TABLE {target_table} AS "
                f"SELECT *, CURRENT_DATE AS {ingestion_date_column}, "
                f"DATE '{end_date_sentinel}' AS {end_date_column}, "
                f"TRUE AS {is_current_column} "
                f"FROM _scd2_init"
            )
            conn.unregister("_scd2_init")
            return {"expired": 0, "inserted": frame.height, "unchanged": 0}

        # Register incoming frame
        conn.register("_scd2_source", frame.to_arrow())

        # Build join condition on natural keys
        join_cond = " AND ".join(
            f"t.\"{k}\" = s.\"{k}\"" for k in natural_keys
        )

        # Count state before operations for accurate change tracking
        row_count_before = conn.execute(
            f"SELECT COUNT(*) FROM {target_table}"
        ).fetchone()[0]
        expired_before = conn.execute(
            f"SELECT COUNT(*) FROM {target_table} "
            f"WHERE {is_current_column} = FALSE"
        ).fetchone()[0]

        # Step 1: Expire changed rows
        conn.execute(
            f"UPDATE {target_table} AS t "
            f"SET {is_current_column} = FALSE, "
            f"    {end_date_column} = CURRENT_DATE "
            f"FROM _scd2_source AS s "
            f"WHERE {join_cond} "
            f"  AND t.{is_current_column} = TRUE "
            f"  AND t.\"{hash_column}\" != s.\"{hash_column}\""
        )

        expired_after = conn.execute(
            f"SELECT COUNT(*) FROM {target_table} "
            f"WHERE {is_current_column} = FALSE"
        ).fetchone()[0]
        expired_count = expired_after - expired_before

        # Step 2: Insert new or changed rows
        # A row needs insertion if there is no current matching row with the same hash
        conn.execute(
            f"INSERT INTO {target_table} "
            f"SELECT s.*, CURRENT_DATE AS {ingestion_date_column}, "
            f"DATE '{end_date_sentinel}' AS {end_date_column}, "
            f"TRUE AS {is_current_column} "
            f"FROM _scd2_source s "
            f"WHERE NOT EXISTS ("
            f"  SELECT 1 FROM {target_table} t "
            f"  WHERE {join_cond} "
            f"    AND t.{is_current_column} = TRUE "
            f"    AND t.\"{hash_column}\" = s.\"{hash_column}\""
            f")"
        )

        row_count_after = conn.execute(
            f"SELECT COUNT(*) FROM {target_table}"
        ).fetchone()[0]
        inserted_count = row_count_after - row_count_before

        # Unchanged = source rows - inserted
        unchanged_count = frame.height - inserted_count

        conn.unregister("_scd2_source")

        return {
            "expired": expired_count,
            "inserted": inserted_count,
            "unchanged": max(unchanged_count, 0),
        }
    finally:
        if owns_connection:
            conn.close()


def load_duckdb_table(
    table_identifier: str,
    *,
    db_path: str | Path = "./output/nfl.duckdb",
    connection: Any | None = None,
) -> pl.DataFrame:
    """Load a DuckDB table as a Polars DataFrame.

    Parameters
    ----------
    table_identifier : str
        Schema-qualified table name, e.g. ``"main.dim_players"``.
    db_path : str | Path
        Path to the DuckDB file. Ignored if ``connection`` is provided.
    connection : duckdb.DuckDBPyConnection | None
        Optional existing connection.

    Returns
    -------
    pl.DataFrame
        Contents of the table.
    """
    conn = connection or get_connection(db_path, read_only=True)
    owns_connection = connection is None

    try:
        arrow_table = conn.execute(f"SELECT * FROM {table_identifier}").fetch_arrow_table()
        return pl.from_arrow(arrow_table)
    finally:
        if owns_connection:
            conn.close()


def query_duckdb(
    sql: str,
    *,
    db_path: str | Path = "./output/nfl.duckdb",
    connection: Any | None = None,
    params: list | None = None,
) -> pl.DataFrame:
    """Execute an arbitrary SQL query and return results as a Polars DataFrame.

    Parameters
    ----------
    sql : str
        SQL query to execute.
    db_path : str | Path
        Path to the DuckDB file. Ignored if ``connection`` is provided.
    connection : duckdb.DuckDBPyConnection | None
        Optional existing connection.
    params : list | None
        Optional positional parameters for parameterized queries.

    Returns
    -------
    pl.DataFrame
        Query results.
    """
    conn = connection or get_connection(db_path, read_only=True)
    owns_connection = connection is None

    try:
        if params:
            result = conn.execute(sql, params)
        else:
            result = conn.execute(sql)
        arrow_table = result.fetch_arrow_table()
        return pl.from_arrow(arrow_table)
    finally:
        if owns_connection:
            conn.close()
