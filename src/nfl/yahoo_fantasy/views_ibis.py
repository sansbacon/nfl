"""Materialized analytical views derived from transformed Yahoo tables (Ibis).

Drop-in replacement for ``views.py`` that operates on ``ibis.Table``
expressions instead of ``pl.DataFrame`` objects.

Key Ibis translations from the Polars original:
- ``pl.struct([...]).rank().over(...)`` → ``ibis.dense_rank().over(window)``
- ``frame.explode("stats")`` → ``table.unnest("stats")``
- ``pl.when(...).then(...).otherwise(...)`` → ``ibis.cases().when(...).then(...).else_(...).end()``
- ``frame.join(..., on=..., how=...)`` → ``table.join(..., predicates=...)``

Requires: pip install nfl[ibis]
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING

import ibis
import ibis.expr.types as ir
import pyarrow as pa

if TYPE_CHECKING:
    pass

VIEW_DRAFT_RESULTS = "vw_draft_results"
VIEW_PLAYER_FANTASY_SCORING = "v_player_fantasy_scoring"

AVAILABLE_VIEWS: tuple[str, ...] = (
    VIEW_DRAFT_RESULTS,
    VIEW_PLAYER_FANTASY_SCORING,
)


# --- Empty table factories ---

def _empty_draft_results() -> ibis.Table:
    """Empty draft results table with correct schema."""
    return ibis.memtable(
        pa.table({
            "league_key": pa.array([], type=pa.string()),
            "season": pa.array([], type=pa.int64()),
            "league_name": pa.array([], type=pa.string()),
            "team_key": pa.array([], type=pa.string()),
            "team_name": pa.array([], type=pa.string()),
            "team_owner": pa.array([], type=pa.string()),
            "player_key": pa.array([], type=pa.string()),
            "player_name": pa.array([], type=pa.string()),
            "player_position": pa.array([], type=pa.string()),
            "player_team": pa.array([], type=pa.string()),
            "round": pa.array([], type=pa.int64()),
            "pick": pa.array([], type=pa.int64()),
            "cost": pa.array([], type=pa.int64()),
            "position_pick": pa.array([], type=pa.int64()),
            "position_cost": pa.array([], type=pa.int64()),
        })
    )


def _empty_player_fantasy_scoring() -> ibis.Table:
    """Empty player fantasy scoring table with correct schema."""
    return ibis.memtable(
        pa.table({
            "player_key": pa.array([], type=pa.string()),
            "league_key": pa.array([], type=pa.string()),
            "week": pa.array([], type=pa.int64()),
            "player_name": pa.array([], type=pa.string()),
            "display_position": pa.array([], type=pa.string()),
            "stat_id": pa.array([], type=pa.string()),
            "stat_name": pa.array([], type=pa.string()),
            "stat_full_name": pa.array([], type=pa.string()),
            "raw_value": pa.array([], type=pa.float64()),
            "stat_points": pa.array([], type=pa.float64()),
            "bonus_points": pa.array([], type=pa.float64()),
            "total_stat_points": pa.array([], type=pa.float64()),
        })
    )


# --- View builders ---

def _build_vw_draft_results(tables: Mapping[str, ibis.Table]) -> ibis.Table:
    """Build draft results view with position-relative rankings.

    Translates the Polars window rank pattern:
        pl.struct(["round", "pick"]).rank(method="dense").over(["season", "player_position"])
    Into Ibis:
        ibis.dense_rank().over(window(group_by=..., order_by=...))
    """
    required = ("draft_pick", "league", "team", "player")
    if any(name not in tables for name in required):
        return _empty_draft_results()

    draft = tables["draft_pick"].select(
        "league_key",
        "season",
        "team_key",
        "player_key",
        tables["draft_pick"].round_number.name("round"),
        tables["draft_pick"].pick_number.name("pick"),
        "cost",
    )
    leagues = tables["league"].select(
        "league_key", "season", "league_name",
    )
    teams = tables["team"].select(
        "league_key",
        "team_key",
        "team_name",
        tables["team"].owner_name.name("team_owner"),
    )
    players = tables["player"].select(
        "player_key",
        tables["player"].full_name.name("player_name"),
        tables["player"].display_position.name("player_position"),
        tables["player"].editorial_team_abbr.name("player_team"),
    )

    # Multi-table join
    joined = (
        draft
        .join(leagues, ["league_key", "season"])
        .join(teams, ["league_key", "team_key"])
        .join(players, "player_key", how="left")
    )

    # Window functions for position-relative rankings
    # position_pick: dense_rank by (round, pick) within (season, player_position)
    pick_window = ibis.window(
        group_by=[joined.season, joined.player_position],
        order_by=[joined["round"], joined["pick"]],
    )
    # position_cost: dense_rank by cost DESC within (season, player_position)
    cost_window = ibis.window(
        group_by=[joined.season, joined.player_position],
        order_by=ibis.desc(joined.cost),
    )

    # Ibis dense_rank() is 0-based; add 1 for 1-based ranks matching Polars
    out = joined.mutate(
        position_pick=ibis.dense_rank().over(pick_window) + 1,
        position_cost=ibis.dense_rank().over(cost_window) + 1,
    ).select(
        "league_key",
        "season",
        "league_name",
        "team_key",
        "team_name",
        "team_owner",
        "player_key",
        "player_name",
        "player_position",
        "player_team",
        "round",
        "pick",
        "cost",
        "position_pick",
        "position_cost",
    ).order_by("season", "round", "pick")

    return out


def _build_v_player_fantasy_scoring(tables: Mapping[str, ibis.Table]) -> ibis.Table:
    """Build player fantasy scoring view.

    Translates the Polars struct-explode + conditional scoring pattern:
        .explode("stats")
        .with_columns(pl.col("stats").struct.field("stat_id")...)
        pl.when(condition).then(...).otherwise(...)
    Into Ibis:
        .unnest("stats")
        ibis.cases().when(...).then(...).else_(...).end()

    NOTE: The unnest operation requires the "stats" column to be an
    array-of-structs type. If the source data stores stats as a JSON
    string or other format, pre-processing is needed before this view.
    """
    required = ("nfl_player_stats_weekly", "player", "scoring_rule", "league", "stat_category")
    if any(name not in tables for name in required):
        return _empty_player_fantasy_scoring()

    stats = tables["nfl_player_stats_weekly"].select(
        "player_key", "league_key", "week", "stats",
    )

    # Check if stats table is empty
    if int(stats.count().execute()) == 0:
        return _empty_player_fantasy_scoring()

    # Explode the stats array-of-structs and extract fields
    # In Ibis, unnest() flattens array columns into rows
    exploded = (
        stats
        .filter(stats.stats.notnull())
        .unnest("stats")
        .filter(lambda t: t.stats.notnull())
    )

    # Extract struct fields
    # After unnest, "stats" becomes individual struct rows; extract fields
    exploded = exploded.mutate(
        stat_id=exploded.stat_id.cast("string"),
        raw_value=exploded.value.cast("float64"),
    ).drop("value")

    if int(exploded.count().execute()) == 0:
        return _empty_player_fantasy_scoring()

    players = tables["player"].select(
        "player_key",
        tables["player"].full_name.name("player_name"),
        "display_position",
    )
    rules = tables["scoring_rule"].select(
        "league_key", "stat_id", "points_per_unit", "bonus_target", "bonus_points",
    )
    leagues = tables["league"].select("league_key", "game_id")
    categories = tables["stat_category"].select(
        "game_id", "stat_id", "display_name", "name",
    )

    # Multi-table join
    joined = (
        exploded
        .join(rules, ["league_key", "stat_id"])
        .join(leagues, "league_key")
        .join(categories, ["game_id", "stat_id"])
        .join(players, "player_key", how="left")
    )

    # Compute scoring columns
    stat_points = (joined.raw_value * joined.points_per_unit).cast("float64")

    bonus_points_expr = ibis.cases(
        (
            joined.bonus_target.notnull() & (joined.raw_value >= joined.bonus_target),
            ibis.coalesce(joined.bonus_points, ibis.literal(0.0)),
        ),
        else_=ibis.literal(0.0),
    ).cast("float64")

    scored = joined.mutate(
        stat_points=stat_points,
        bonus_points=bonus_points_expr,
    ).mutate(
        total_stat_points=lambda t: (t.stat_points + t.bonus_points).cast("float64"),
    )

    return scored.select(
        "player_key",
        "league_key",
        "week",
        "player_name",
        "display_position",
        "stat_id",
        scored.display_name.name("stat_name"),
        scored.name.name("stat_full_name"),
        "raw_value",
        "stat_points",
        "bonus_points",
        "total_stat_points",
    ).order_by("league_key", "week", "player_key", "stat_id")


# --- Public entry point ---

def build_materialized_views(
    tables: Mapping[str, ibis.Table],
    requested_views: Iterable[str] | None = None,
) -> dict[str, ibis.Table]:
    """Build materialized analytical views from transformed Ibis tables.

    Parameters
    ----------
    tables : Mapping[str, ibis.Table]
        Transformed entity tables (output of ``transform()``).
    requested_views : Iterable[str] | None
        Which views to build. Defaults to all available views.

    Returns
    -------
    dict[str, ibis.Table]
        View name to Ibis table mapping.
    """
    selected = set(requested_views or AVAILABLE_VIEWS)
    built: dict[str, ibis.Table] = {}

    if VIEW_DRAFT_RESULTS in selected:
        built[VIEW_DRAFT_RESULTS] = _build_vw_draft_results(tables)
    if VIEW_PLAYER_FANTASY_SCORING in selected:
        built[VIEW_PLAYER_FANTASY_SCORING] = _build_v_player_fantasy_scoring(tables)

    return built
