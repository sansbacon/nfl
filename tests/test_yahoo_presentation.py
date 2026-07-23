from __future__ import annotations

import polars as pl

from nfl.yahoo_fantasy.presentation import format_table_for_display


def test_format_table_for_display_drops_key_and_id_columns_by_default() -> None:
    df = pl.DataFrame(
        {
            "league_key": ["l1"],
            "team_id": [10],
            "season": [2025],
            "week": [1],
            "team_points": [101.2345],
        }
    )

    out = format_table_for_display(df)

    assert out.columns == ["season", "week", "team_points"]


def test_format_table_for_display_keeps_requested_hidden_columns() -> None:
    df = pl.DataFrame(
        {
            "league_key": ["l1"],
            "team_key": ["t1"],
            "team_id": [10],
            "week": [1],
            "team_points": [55.555],
        }
    )

    out = format_table_for_display(df, keep_cols=["team_key"])

    assert "team_key" in out.columns
    assert "league_key" not in out.columns
    assert "team_id" not in out.columns


def test_format_table_for_display_rounds_float_columns() -> None:
    df = pl.DataFrame({"x": [1.239, 2.345]})

    out = format_table_for_display(df, drop_keys=False, decimal_places=2)

    assert out["x"].to_list() == [1.24, 2.35]


def test_format_table_for_display_never_returns_empty_selection() -> None:
    df = pl.DataFrame({"league_key": ["l1"], "team_id": [10]})

    out = format_table_for_display(df)

    assert out.columns == ["league_key", "team_id"]
