from __future__ import annotations

import polars as pl

from nfl.yahoo_fantasy.notebook import make_table_loaders


class _FakeClient:
    def __init__(self) -> None:
        self._table = pl.DataFrame({"x": [1, 2]})

    def load_table(self, table_identifier: str) -> pl.DataFrame:
        if table_identifier == "ok.table":
            return self._table
        raise ValueError("missing")

    def maybe_load(self, table_identifier: str) -> pl.DataFrame | None:
        if table_identifier == "ok.table":
            return self._table
        return None


def test_make_table_loaders_returns_bound_client_callables() -> None:
    client = _FakeClient()

    load_table_as_polars, maybe_load = make_table_loaders(client)

    loaded = load_table_as_polars("ok.table")
    maybe = maybe_load("ok.table")
    missing = maybe_load("missing.table")

    assert loaded.shape == (2, 1)
    assert maybe is not None
    assert maybe.shape == (2, 1)
    assert missing is None
