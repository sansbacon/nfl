"""Presentation helpers for formatting Yahoo Fantasy query outputs."""

from __future__ import annotations

import polars as pl


def _presentation_columns(
    columns: list[str],
    keep_cols: list[str] | None = None,
    drop_cols: list[str] | None = None,
) -> list[str]:
    """Return a readable subset of columns for display.

    Keys/ids are hidden by default except for columns listed in keep_cols.
    Additional columns can be hidden explicitly with drop_cols.
    """
    keep_set = set(keep_cols or [])
    drop_set = set(drop_cols or [])

    hidden = set()
    for col in columns:
        is_key = col.endswith("_key")
        is_id = col.endswith("_id") and col not in {"game_id", "season", "week"}
        if (is_key or is_id) and col not in keep_set:
            hidden.add(col)

    hidden.update(drop_set)
    selected = [c for c in columns if c not in hidden]

    # Never return an empty view due to aggressive hiding rules.
    return selected or columns


def format_table_for_display(
    df: pl.DataFrame,
    drop_keys: bool = True,
    keep_cols: list[str] | None = None,
    drop_cols: list[str] | None = None,
    decimal_places: int = 2,
) -> pl.DataFrame:
    """Format a Polars DataFrame for notebook-friendly display."""
    out = df

    if drop_keys:
        selected = _presentation_columns(out.columns, keep_cols=keep_cols, drop_cols=drop_cols)
        out = out.select(selected)

    round_exprs = [
        pl.col(col).round(decimal_places).alias(col)
        for col, dtype in out.schema.items()
        if dtype in {pl.Float32, pl.Float64} or str(dtype).startswith("Decimal")
    ]
    if round_exprs:
        out = out.with_columns(round_exprs)

    return out
