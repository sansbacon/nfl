"""Notebook-focused helper utilities for Yahoo Fantasy workflows."""

from __future__ import annotations

from typing import Callable, Protocol

import polars as pl


class _TableLoaderClient(Protocol):
    def load_table(self, table_identifier: str) -> pl.DataFrame:
        ...

    def maybe_load(self, table_identifier: str) -> pl.DataFrame | None:
        ...


def configure_polars_display(rows: int = 50, cols: int = 20, str_length: int = 100) -> None:
    """Apply notebook-friendly Polars display defaults."""
    pl.Config.set_tbl_rows(rows)
    pl.Config.set_tbl_cols(cols)
    pl.Config.set_fmt_str_lengths(str_length)


def make_table_loaders(
    client: _TableLoaderClient,
) -> tuple[Callable[[str], pl.DataFrame], Callable[[str], pl.DataFrame | None]]:
    """Return bound load helpers that are convenient for notebooks."""
    return client.load_table, client.maybe_load
