"""SCD Type 2 merge via Ibis (hybrid approach).

Uses Ibis expressions for reads and change detection, then dispatches
backend-specific MERGE SQL for the mutation (UPDATE expired rows +
INSERT new/changed rows). For backends without MERGE support (Polars,
DataFusion), falls back to a full-table relational rebuild.

Requires: pip install nfl[ibis]
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import ibis


def _parse_table_name(fq_name: str) -> tuple[str | None, str]:
    """Split 'schema.table' into (schema, table) for Ibis create_table."""
    if "." in fq_name:
        parts = fq_name.rsplit(".", 1)
        return parts[0], parts[1]
    return None, fq_name


def compute_record_hash(
    table: ibis.Table,
    *,
    exclude_columns: tuple[str, ...] = (),
    include_columns: tuple[str, ...] | None = None,
    hash_column: str = "_record_hash",
    separator: str = "|",
) -> ibis.Table:
    """Compute a deterministic content hash for each row in an Ibis table.

    Concatenates selected column values (cast to string) with a separator,
    then applies a hash function. The result is appended as ``hash_column``.

    Parameters
    ----------
    table : ibis.Table
        Input table expression.
    exclude_columns : tuple[str, ...]
        Columns to exclude from the hash. Ignored if ``include_columns`` is set.
    include_columns : tuple[str, ...] | None
        If provided, only these columns are hashed.
    hash_column : str
        Name of the output hash column.
    separator : str
        Separator between column values before hashing.

    Returns
    -------
    ibis.Table
        Original table with ``hash_column`` appended.
    """
    import ibis
    from ibis import _

    if include_columns is not None:
        cols_to_hash = [c for c in table.columns if c in include_columns]
    elif exclude_columns:
        cols_to_hash = [c for c in table.columns if c not in exclude_columns]
    else:
        cols_to_hash = list(table.columns)

    if not cols_to_hash:
        raise ValueError(
            "No columns selected for hashing. Check include_columns/exclude_columns."
        )

    # Cast all columns to string, coalesce nulls, concat with separator, then hash
    str_exprs = [
        table[col].cast("string").fill_null("__NULL__") for col in cols_to_hash
    ]

    # Build concatenated string via reduce
    concat_expr = str_exprs[0]
    for expr in str_exprs[1:]:
        concat_expr = concat_expr.concat(separator).concat(expr)

    return table.mutate(**{hash_column: concat_expr.hash().cast("string")})


def merge_scd2(
    source: ibis.Table,
    target_name: str,
    natural_keys: tuple[str, ...],
    backend: ibis.BaseBackend,
    *,
    hash_column: str = "_record_hash",
    ingestion_date_column: str = "ingestion_date",
    end_date_column: str = "end_date",
    is_current_column: str = "is_current",
    end_date_sentinel: str = "9999-12-31",
) -> dict[str, int]:
    """Perform an SCD Type 2 merge into a target table via Ibis.

    Implements the standard pattern:
    1. Match incoming rows to current target rows on ``natural_keys``.
    2. If ``hash_column`` differs: expire the old row and insert the new one.
    3. If no match exists: insert as a new current row.
    4. Unmatched target rows are left untouched.

    Dispatches backend-specific SQL for mutation (DuckDB, PySpark/Delta).
    Falls back to relational rebuild for backends without MERGE.

    Parameters
    ----------
    source : ibis.Table
        Incoming rows (new snapshot). Must already contain ``hash_column``.
    target_name : str
        Schema-qualified target table name.
    natural_keys : tuple[str, ...]
        Columns forming the business key.
    backend : ibis.BaseBackend
        Connected Ibis backend.
    hash_column : str
        Column containing a content hash for change detection.
    ingestion_date_column : str
        Column for effective-from date.
    end_date_column : str
        Column for effective-to date.
    is_current_column : str
        Boolean column indicating the active row.
    end_date_sentinel : str
        Date string representing "no end".

    Returns
    -------
    dict[str, int]
        Counts: ``{"expired": N, "inserted": N, "unchanged": N}``.
    """
    import ibis

    # Check if target table exists
    try:
        _db, _tbl = _parse_table_name(target_name)
        target = backend.table(_tbl, database=_db)
    except Exception:
        # Bootstrap: create target from source with SCD2 metadata columns
        bootstrapped = source.mutate(
            **{
                ingestion_date_column: ibis.literal(date.today()),
                end_date_column: ibis.literal(date.fromisoformat(end_date_sentinel)),
                is_current_column: ibis.literal(True),
            }
        )
        _db, _tbl = _parse_table_name(target_name)
        backend.create_table(_tbl, bootstrapped, database=_db)
        row_count = int(source.count().execute())
        return {"expired": 0, "inserted": row_count, "unchanged": 0}

    # Register source as a temp table for SQL-based backends
    source_temp_name = "_scd2_source"
    backend.create_table(source_temp_name, source, temp=True, overwrite=True)  # temp tables: no schema

    # Dispatch by backend
    match backend.name:
        case "duckdb":
            result = _scd2_duckdb(
                backend,
                target_name,
                source_temp_name,
                natural_keys,
                hash_column,
                ingestion_date_column,
                end_date_column,
                is_current_column,
                end_date_sentinel,
                int(source.count().execute()),
            )
        case "pyspark":
            result = _scd2_delta(
                backend,
                target_name,
                source_temp_name,
                natural_keys,
                hash_column,
                ingestion_date_column,
                end_date_column,
                is_current_column,
                end_date_sentinel,
                int(source.count().execute()),
            )
        case _:
            result = _scd2_relational_rebuild(
                backend,
                source,
                target,
                target_name,
                natural_keys,
                hash_column,
                ingestion_date_column,
                end_date_column,
                is_current_column,
                end_date_sentinel,
            )

    # Clean up temp table
    try:
        backend.drop_table(source_temp_name)
    except Exception:
        pass  # Some backends auto-drop temp tables

    return result


def _scd2_duckdb(
    backend: ibis.BaseBackend,
    target_name: str,
    source_name: str,
    natural_keys: tuple[str, ...],
    hash_column: str,
    ingestion_date_column: str,
    end_date_column: str,
    is_current_column: str,
    end_date_sentinel: str,
    source_row_count: int,
) -> dict[str, int]:
    """DuckDB-specific SCD2 merge using UPDATE + INSERT SQL."""
    join_cond = " AND ".join(
        f't."{k}" = s."{k}"' for k in natural_keys
    )

    # Count expired rows before
    expired_before = backend.raw_sql(
        f"SELECT COUNT(*) as cnt FROM {target_name} "
        f"WHERE {is_current_column} = FALSE"
    ).fetchone()[0]

    row_count_before = backend.raw_sql(
        f"SELECT COUNT(*) as cnt FROM {target_name}"
    ).fetchone()[0]

    # Step 1: Expire changed rows
    backend.raw_sql(
        f"UPDATE {target_name} AS t "
        f"SET {is_current_column} = FALSE, "
        f"    {end_date_column} = CURRENT_DATE "
        f"FROM {source_name} AS s "
        f"WHERE {join_cond} "
        f"  AND t.{is_current_column} = TRUE "
        f'  AND t."{hash_column}" != s."{hash_column}"'
    )

    expired_after = backend.raw_sql(
        f"SELECT COUNT(*) as cnt FROM {target_name} "
        f"WHERE {is_current_column} = FALSE"
    ).fetchone()[0]
    expired_count = expired_after - expired_before

    # Step 2: Insert new or changed rows
    backend.raw_sql(
        f"INSERT INTO {target_name} "
        f"SELECT s.*, CURRENT_DATE AS {ingestion_date_column}, "
        f"DATE '{end_date_sentinel}' AS {end_date_column}, "
        f"TRUE AS {is_current_column} "
        f"FROM {source_name} s "
        f"WHERE NOT EXISTS ("
        f"  SELECT 1 FROM {target_name} t "
        f"  WHERE {join_cond} "
        f"    AND t.{is_current_column} = TRUE "
        f'    AND t."{hash_column}" = s."{hash_column}"'
        f")"
    )

    row_count_after = backend.raw_sql(
        f"SELECT COUNT(*) as cnt FROM {target_name}"
    ).fetchone()[0]
    inserted_count = row_count_after - row_count_before

    unchanged_count = source_row_count - inserted_count
    return {
        "expired": expired_count,
        "inserted": inserted_count,
        "unchanged": max(unchanged_count, 0),
    }


def _scd2_delta(
    backend: ibis.BaseBackend,
    target_name: str,
    source_name: str,
    natural_keys: tuple[str, ...],
    hash_column: str,
    ingestion_date_column: str,
    end_date_column: str,
    is_current_column: str,
    end_date_sentinel: str,
    source_row_count: int,
) -> dict[str, int]:
    """PySpark/Delta-specific SCD2 merge using Delta MERGE INTO.

    Uses two separate operations since Delta MERGE doesn't natively
    support the SCD2 expire-and-insert-new pattern in one statement.
    """
    join_cond = " AND ".join(
        f"t.`{k}` = s.`{k}`" for k in natural_keys
    )

    # Step 1: Expire changed rows
    backend.raw_sql(
        f"MERGE INTO {target_name} AS t "
        f"USING {source_name} AS s "
        f"ON {join_cond} AND t.{is_current_column} = TRUE "
        f"WHEN MATCHED AND t.`{hash_column}` != s.`{hash_column}` THEN "
        f"  UPDATE SET t.{is_current_column} = FALSE, "
        f"    t.{end_date_column} = current_date()"
    )

    # Step 2: Insert new/changed rows
    backend.raw_sql(
        f"INSERT INTO {target_name} "
        f"SELECT s.*, current_date() AS {ingestion_date_column}, "
        f"DATE '{end_date_sentinel}' AS {end_date_column}, "
        f"TRUE AS {is_current_column} "
        f"FROM {source_name} s "
        f"WHERE NOT EXISTS ("
        f"  SELECT 1 FROM {target_name} t "
        f"  WHERE {join_cond} "
        f"    AND t.{is_current_column} = TRUE "
        f"    AND t.`{hash_column}` = s.`{hash_column}`"
        f")"
    )

    # Count results (Delta doesn't easily give us row-level counts from MERGE)
    expired_count = int(
        backend.raw_sql(
            f"SELECT COUNT(*) as cnt FROM {target_name} "
            f"WHERE {is_current_column} = FALSE "
            f"AND {end_date_column} = current_date()"
        ).fetchone()[0]
    )
    total_rows = int(
        backend.raw_sql(
            f"SELECT COUNT(*) as cnt FROM {target_name}"
        ).fetchone()[0]
    )
    # Approximate: inserted = expired (re-inserts) + truly new
    inserted_count = expired_count + max(
        0, source_row_count - expired_count - (source_row_count - expired_count)
    )
    # Simpler: count current rows that were just inserted today
    inserted_count = int(
        backend.raw_sql(
            f"SELECT COUNT(*) as cnt FROM {target_name} "
            f"WHERE {is_current_column} = TRUE "
            f"AND {ingestion_date_column} = current_date()"
        ).fetchone()[0]
    )
    unchanged_count = source_row_count - inserted_count

    return {
        "expired": expired_count,
        "inserted": inserted_count,
        "unchanged": max(unchanged_count, 0),
    }


def _scd2_relational_rebuild(
    backend: ibis.BaseBackend,
    source: ibis.Table,
    target: ibis.Table,
    target_name: str,
    natural_keys: tuple[str, ...],
    hash_column: str,
    ingestion_date_column: str,
    end_date_column: str,
    is_current_column: str,
    end_date_sentinel: str,
) -> dict[str, int]:
    """Relational rebuild fallback for backends without MERGE.

    Reads the full target, computes diffs via anti-join + union,
    and overwrites the target table. Works on Polars, DataFusion,
    and any other Ibis backend.
    """
    import ibis

    today = ibis.literal(date.today())
    sentinel = ibis.literal(date.fromisoformat(end_date_sentinel))

    # Current target rows
    current_target = target.filter(target[is_current_column] == True)  # noqa: E712

    # Join current target with source on natural keys to find changes
    join_predicates = [
        current_target[k] == source[k] for k in natural_keys
    ]
    matched = current_target.join(source, predicates=join_predicates)

    # Changed rows: hash differs
    changed_keys = matched.filter(
        matched[f"{hash_column}_right"] != matched[hash_column]
    ).select([current_target[k] for k in natural_keys])

    # Expire changed rows in target
    expired_join = target.join(
        changed_keys, predicates=[target[k] == changed_keys[k] for k in natural_keys]
    ).filter(target[is_current_column] == True)  # noqa: E712

    expired_rows = expired_join.mutate(
        **{is_current_column: ibis.literal(False), end_date_column: today}
    )
    expired_count = int(expired_rows.count().execute())

    # Unchanged target rows (everything NOT in the expired set)
    # This is: all target rows MINUS the ones we just expired
    unchanged_target = target.anti_join(
        expired_rows, predicates=[target[k] == expired_rows[k] for k in natural_keys]
    ).filter(
        (target[is_current_column] == True)  # noqa: E712
        | (target[is_current_column] == False)  # noqa: E712
    )
    # Simpler: just keep all rows that aren't in the expired key set while current
    # Actually, keep ALL original target rows, then replace the expired ones
    non_expired_target = target.anti_join(
        changed_keys, predicates=[target[k] == changed_keys[k] for k in natural_keys]
    )

    # New rows to insert: source rows with no current match having same hash
    new_rows = source.anti_join(
        current_target,
        predicates=[source[k] == current_target[k] for k in natural_keys],
    ).mutate(
        **{
            ingestion_date_column: today,
            end_date_column: sentinel,
            is_current_column: ibis.literal(True),
        }
    )

    # Changed rows to re-insert as current
    reinserts = source.join(
        changed_keys, predicates=[source[k] == changed_keys[k] for k in natural_keys]
    ).mutate(
        **{
            ingestion_date_column: today,
            end_date_column: sentinel,
            is_current_column: ibis.literal(True),
        }
    )

    # Final table: non-expired target + expired (updated) + new + reinserts
    final = ibis.union(
        non_expired_target,
        expired_rows,
        new_rows,
        reinserts,
    )

    inserted_count = int(new_rows.count().execute()) + int(reinserts.count().execute())

    # Overwrite target
    _db, _tbl = _parse_table_name(target_name)
    backend.create_table(_tbl, final, database=_db, overwrite=True)

    source_count = int(source.count().execute())
    unchanged_count = source_count - inserted_count

    return {
        "expired": expired_count,
        "inserted": inserted_count,
        "unchanged": max(unchanged_count, 0),
    }
