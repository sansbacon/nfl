"""Materialized analytical views derived from transformed Yahoo frames."""

from __future__ import annotations

from typing import Iterable, Mapping

import polars as pl

VIEW_DRAFT_RESULTS = "vw_draft_results"
VIEW_PLAYER_FANTASY_SCORING = "v_player_fantasy_scoring"

AVAILABLE_VIEWS: tuple[str, ...] = (
    VIEW_DRAFT_RESULTS,
    VIEW_PLAYER_FANTASY_SCORING,
)


def _empty_draft_results() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "league_key": pl.Utf8,
            "season": pl.Int64,
            "league_name": pl.Utf8,
            "team_key": pl.Utf8,
            "team_name": pl.Utf8,
            "team_owner": pl.Utf8,
            "player_key": pl.Utf8,
            "player_name": pl.Utf8,
            "player_position": pl.Utf8,
            "player_team": pl.Utf8,
            "round": pl.Int64,
            "pick": pl.Int64,
            "cost": pl.Int64,
            "position_pick": pl.Int64,
            "position_cost": pl.Int64,
        }
    )


def _empty_player_fantasy_scoring() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "player_key": pl.Utf8,
            "league_key": pl.Utf8,
            "week": pl.Int64,
            "player_name": pl.Utf8,
            "display_position": pl.Utf8,
            "stat_id": pl.Utf8,
            "stat_name": pl.Utf8,
            "stat_full_name": pl.Utf8,
            "raw_value": pl.Float64,
            "stat_points": pl.Float64,
            "bonus_points": pl.Float64,
            "total_stat_points": pl.Float64,
        }
    )


def _build_vw_draft_results(frames: Mapping[str, pl.DataFrame]) -> pl.DataFrame:
    required = ("draft_pick", "league", "team", "player")
    if any(name not in frames for name in required):
        return _empty_draft_results()

    draft = frames["draft_pick"].select(
        [
            "league_key",
            "season",
            "team_key",
            "player_key",
            pl.col("round_number").alias("round"),
            pl.col("pick_number").alias("pick"),
            "cost",
        ]
    )
    leagues = frames["league"].select(["league_key", "season", pl.col("league_name")])
    teams = frames["team"].select(["league_key", "team_key", "team_name", pl.col("owner_name").alias("team_owner")])
    players = frames["player"].select(
        [
            "player_key",
            pl.col("full_name").alias("player_name"),
            pl.col("display_position").alias("player_position"),
            pl.col("editorial_team_abbr").alias("player_team"),
        ]
    )

    out = (
        draft.join(leagues, on=["league_key", "season"], how="inner")
        .join(teams, on=["league_key", "team_key"], how="inner")
        .join(players, on=["player_key"], how="left")
        .with_columns(
            [
                pl.struct(["round", "pick"]).rank(method="dense").over(["season", "player_position"]).cast(pl.Int64).alias("position_pick"),
                pl.col("cost").rank(method="dense", descending=True).over(["season", "player_position"]).cast(pl.Int64).alias("position_cost"),
            ]
        )
        .select(
            [
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
            ]
        )
        .sort(["season", "round", "pick"])
    )
    return out


def _build_v_player_fantasy_scoring(frames: Mapping[str, pl.DataFrame]) -> pl.DataFrame:
    required = ("nfl_player_stats_weekly", "player", "scoring_rule", "league", "stat_category")
    if any(name not in frames for name in required):
        return _empty_player_fantasy_scoring()

    stats = frames["nfl_player_stats_weekly"].select(
        [
            "player_key",
            "league_key",
            "week",
            "stats",
        ]
    )
    if stats.height == 0:
        return _empty_player_fantasy_scoring()

    exploded = (
        stats.filter(pl.col("stats").is_not_null())
        .explode("stats")
        .filter(pl.col("stats").is_not_null())
        .with_columns(
            [
                pl.col("stats").struct.field("stat_id").cast(pl.Utf8).alias("stat_id"),
                pl.col("stats").struct.field("value").cast(pl.Float64).alias("raw_value"),
            ]
        )
        .drop("stats")
    )
    if exploded.height == 0:
        return _empty_player_fantasy_scoring()

    players = frames["player"].select(
        [
            "player_key",
            pl.col("full_name").alias("player_name"),
            "display_position",
        ]
    )
    rules = frames["scoring_rule"].select(
        [
            "league_key",
            "stat_id",
            "points_per_unit",
            "bonus_target",
            "bonus_points",
        ]
    )
    leagues = frames["league"].select(["league_key", "game_id"])
    categories = frames["stat_category"].select(["game_id", "stat_id", "display_name", "name"])

    return (
        exploded.join(rules, on=["league_key", "stat_id"], how="inner")
        .join(leagues, on="league_key", how="inner")
        .join(categories, on=["game_id", "stat_id"], how="inner")
        .join(players, on="player_key", how="left")
        .with_columns(
            [
                (pl.col("raw_value") * pl.col("points_per_unit")).cast(pl.Float64).alias("stat_points"),
                pl.when(
                    pl.col("bonus_target").is_not_null() & (pl.col("raw_value") >= pl.col("bonus_target"))
                )
                .then(pl.coalesce(pl.col("bonus_points"), pl.lit(0.0)))
                .otherwise(pl.lit(0.0))
                .cast(pl.Float64)
                .alias("bonus_points"),
            ]
        )
        .with_columns((pl.col("stat_points") + pl.col("bonus_points")).cast(pl.Float64).alias("total_stat_points"))
        .select(
            [
                "player_key",
                "league_key",
                "week",
                "player_name",
                "display_position",
                "stat_id",
                pl.col("display_name").alias("stat_name"),
                pl.col("name").alias("stat_full_name"),
                "raw_value",
                "stat_points",
                "bonus_points",
                "total_stat_points",
            ]
        )
        .sort(["league_key", "week", "player_key", "stat_id"])
    )


def build_materialized_views(
    frames: Mapping[str, pl.DataFrame],
    requested_views: Iterable[str] | None = None,
) -> dict[str, pl.DataFrame]:
    selected = set(requested_views or AVAILABLE_VIEWS)
    built: dict[str, pl.DataFrame] = {}

    if VIEW_DRAFT_RESULTS in selected:
        built[VIEW_DRAFT_RESULTS] = _build_vw_draft_results(frames)
    if VIEW_PLAYER_FANTASY_SCORING in selected:
        built[VIEW_PLAYER_FANTASY_SCORING] = _build_v_player_fantasy_scoring(frames)

    return built