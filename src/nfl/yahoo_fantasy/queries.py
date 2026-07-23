"""Reusable Polars query functions for Yahoo Fantasy warehouse datasets."""

from __future__ import annotations

from typing import Literal

import polars as pl

PointsSource = Literal["player_stats", "matchups", "unavailable"]


def league_team_info(league_df: pl.DataFrame, team_df: pl.DataFrame) -> pl.DataFrame:
    return (
        team_df.join(
            league_df.select(["league_key", "season", "league_name"]),
            on="league_key",
            how="left",
        )
        .select(["league_key", "season", "league_name", "team_key", "team_name", "owner_name"])
        .sort(["season", "league_key", "team_key"])
    )


def standings_summary(
    standings_df: pl.DataFrame,
    league_df: pl.DataFrame | None = None,
    team_df: pl.DataFrame | None = None,
) -> pl.DataFrame:
    out = standings_df

    if league_df is not None:
        out = out.join(
            league_df.select(["league_key", "season", "league_name"]),
            on=["league_key", "season"],
            how="left",
        )

    if team_df is not None:
        out = out.join(
            team_df.select(["league_key", "team_key", "team_name", "owner_name"]),
            on=["league_key", "team_key"],
            how="left",
        )

    for col_name in ["league_name", "team_name", "owner_name"]:
        if col_name not in out.columns:
            out = out.with_columns(pl.lit(None, dtype=pl.Utf8).alias(col_name))

    return out.sort(["season", "wins", "points_for"], descending=[False, True, True]).select(
        [
            "league_key",
            "season",
            "league_name",
            "team_name",
            "owner_name",
            "rank",
            "wins",
            "losses",
            "points_for",
            "points_against",
            "team_key",
        ]
    )


def build_player_weekly_points(roster_df: pl.DataFrame, stats_df: pl.DataFrame) -> pl.DataFrame:
    return (
        roster_df.select(
            [
                "league_key",
                "season",
                "week",
                "team_key",
                "player_key",
                "selected_position",
                "is_starting",
                pl.col("points").alias("roster_points"),
            ]
        )
        .join(
            stats_df.select(["league_key", "season", "week", "player_key", "fantasy_points"]),
            on=["league_key", "season", "week", "player_key"],
            how="left",
        )
        .with_columns(
            pl.coalesce([pl.col("roster_points"), pl.col("fantasy_points"), pl.lit(0.0)]).alias("player_points")
        )
    )


def weekly_team_points(
    stats_df: pl.DataFrame | None,
    roster_df: pl.DataFrame | None,
    matchups_df: pl.DataFrame | None,
) -> tuple[pl.DataFrame, PointsSource]:
    if stats_df is not None and roster_df is not None:
        points_available = (
            stats_df.select(pl.max("fantasy_points").alias("max_fp")).item() is not None
            and stats_df.select(pl.max("fantasy_points").alias("max_fp")).item() > 0
        ) or (
            roster_df.select(pl.max("points").alias("max_points")).item() is not None
            and roster_df.select(pl.max("points").alias("max_points")).item() > 0
        )

        if points_available:
            weekly_points = (
                stats_df.join(
                    roster_df.select(["league_key", "week", "team_key", "player_key"]),
                    on=["league_key", "week", "player_key"],
                    how="left",
                )
                .group_by(["league_key", "season", "week", "team_key"])
                .agg(
                    [
                        pl.sum("fantasy_points").alias("team_points"),
                        pl.n_unique("player_key").alias("players_counted"),
                    ]
                )
                .sort(["season", "week", "team_points"], descending=[False, False, True])
            )
            return weekly_points, "player_stats"

    if matchups_df is not None:
        weekly_points = matchups_df.select(
            ["league_key", "season", "week", "team_key", pl.col("points").alias("team_points")]
        ).sort(["season", "week", "team_points"], descending=[False, False, True])
        return weekly_points, "matchups"

    empty = pl.DataFrame(
        schema={
            "league_key": pl.Utf8,
            "season": pl.Int64,
            "week": pl.Int64,
            "team_key": pl.Utf8,
            "team_points": pl.Float64,
            "players_counted": pl.Int64,
        }
    )
    return empty, "unavailable"


def team_weekly_fallback_from_matchups(matchups_df: pl.DataFrame) -> pl.DataFrame:
    """Build team-week totals from matchups points."""
    return matchups_df.select(
        ["league_key", "season", "week", "team_key", pl.col("points").alias("team_points")]
    ).sort(["season", "week", "team_points"], descending=[False, False, True])


def weekly_team_points_resolved(
    stats_df: pl.DataFrame | None,
    roster_df: pl.DataFrame | None,
    matchups_df: pl.DataFrame | None,
) -> tuple[pl.DataFrame, PointsSource]:
    """Return team-week totals, falling back to matchups when player-stats totals are all zero."""
    weekly_points, points_source = weekly_team_points(
        stats_df=stats_df,
        roster_df=roster_df,
        matchups_df=matchups_df,
    )

    if points_source == "player_stats" and weekly_points.height > 0 and matchups_df is not None:
        max_team_points = weekly_points.select(pl.max("team_points")).item()
        if max_team_points is None or max_team_points == 0.0:
            weekly_points = team_weekly_fallback_from_matchups(matchups_df)
            points_source = "matchups"

    return weekly_points, points_source


def enrich_weekly_team_points(
    weekly_points: pl.DataFrame,
    league_df: pl.DataFrame | None = None,
    team_df: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Attach optional league/team friendly names and return a stable column layout."""
    out = weekly_points

    if league_df is not None:
        out = out.join(
            league_df.select(["league_key", "season", "league_name"]),
            on=["league_key", "season"],
            how="left",
        )

    if team_df is not None:
        out = out.join(
            team_df.select(["league_key", "team_key", "team_name", "owner_name"]),
            on=["league_key", "team_key"],
            how="left",
        )

    for col_name in ["league_name", "team_name", "owner_name"]:
        if col_name not in out.columns:
            out = out.with_columns(pl.lit(None, dtype=pl.Utf8).alias(col_name))

    desired = [
        "season",
        "week",
        "league_name",
        "team_name",
        "owner_name",
        "team_points",
    ]
    if "players_counted" in out.columns:
        desired.append("players_counted")
    desired.extend(["league_key", "team_key"])

    select_cols = [c for c in desired if c in out.columns]
    return out.select(select_cols)


def league_average_by_position(avg_scoring_by_team_position: pl.DataFrame) -> pl.DataFrame:
    """Summarize league-wide average position scoring across teams."""
    return (
        avg_scoring_by_team_position.group_by(["season", "position"])
        .agg(
            [
                pl.mean("avg_points_per_week").alias("league_avg_points_per_week"),
                pl.mean("avg_pct_of_team_points").alias("league_avg_pct_of_team_points"),
            ]
        )
        .with_columns(
            pl.when(pl.col("position") == "QB")
            .then(1)
            .when(pl.col("position") == "RB")
            .then(2)
            .when(pl.col("position") == "WR")
            .then(3)
            .when(pl.col("position") == "TE")
            .then(4)
            .when(pl.col("position") == "FLEX")
            .then(5)
            .when(pl.col("position") == "DEF")
            .then(6)
            .otherwise(99)
            .alias("position_order")
        )
        .sort(["position_order"])
        .drop("position_order")
    )


def player_points_health(stats_df: pl.DataFrame, roster_df: pl.DataFrame | None = None) -> dict[str, int]:
    """Return compact diagnostics for player-level points availability."""
    non_zero_fantasy_points = int(stats_df.select((pl.col("fantasy_points").fill_null(0) != 0).sum()).item() or 0)
    stats_payload_entries = int(stats_df.select(pl.col("stats").list.len().fill_null(0).sum()).item() or 0)

    out = {
        "non_zero_fantasy_points": non_zero_fantasy_points,
        "stats_payload_entries": stats_payload_entries,
    }

    if roster_df is not None and "points" in roster_df.columns:
        out["non_zero_roster_points"] = int(roster_df.select((pl.col("points").fill_null(0) != 0).sum()).item() or 0)

    return out


def position_weekly_points(player_weekly_points: pl.DataFrame) -> pl.DataFrame:
    return (
        player_weekly_points.filter(pl.col("is_starting"))
        .group_by(["league_key", "season", "week", "selected_position"])
        .agg(
            [
                pl.sum("player_points").alias("total_points"),
                pl.mean("player_points").alias("avg_points_per_player"),
                pl.n_unique("player_key").alias("players_counted"),
            ]
        )
        .sort(["season", "week", "total_points"], descending=[False, False, True])
    )


def team_position_weekly_points(player_weekly_points: pl.DataFrame) -> pl.DataFrame:
    return (
        player_weekly_points.filter(pl.col("is_starting"))
        .group_by(["league_key", "season", "week", "team_key", "selected_position"])
        .agg(
            [
                pl.sum("player_points").alias("total_points"),
                pl.n_unique("player_key").alias("players_counted"),
            ]
        )
        .sort(["season", "week", "team_key", "total_points"], descending=[False, False, False, True])
    )


def position_usage_counts(roster_df: pl.DataFrame) -> pl.DataFrame:
    return (
        roster_df.filter(pl.col("is_starting"))
        .group_by(["league_key", "season", "week", "selected_position"])
        .agg(pl.n_unique("player_key").alias("players_counted"))
        .sort(["season", "week", "selected_position"])
    )


def latest_roster_snapshot(
    team_key: str,
    roster_df: pl.DataFrame,
    stats_df: pl.DataFrame | None = None,
    player_df: pl.DataFrame | None = None,
) -> pl.DataFrame:
    latest_week = roster_df.select(pl.max("week")).item()
    my_roster = roster_df.filter((pl.col("team_key") == team_key) & (pl.col("week") == latest_week))

    if stats_df is not None:
        stats_for_week = stats_df.select(
            [
                "league_key",
                "season",
                "week",
                "player_key",
                pl.col("fantasy_points").alias("stats_points"),
            ]
        )
        my_roster = (
            my_roster.join(
                stats_for_week,
                on=["league_key", "season", "week", "player_key"],
                how="left",
            ).with_columns(
                pl.coalesce([pl.col("points"), pl.col("stats_points"), pl.lit(0.0)]).alias("slot_points")
            )
        )

    if player_df is not None:
        my_roster = my_roster.join(
            player_df.select(["player_key", "full_name", "display_position"]),
            on="player_key",
            how="left",
        )

    return my_roster.sort(["selected_position", "is_starting"], descending=[False, True])


def average_scoring_by_position_by_team(
    roster_df: pl.DataFrame,
    stats_df: pl.DataFrame,
    team_df: pl.DataFrame,
    weekly_points: pl.DataFrame | None = None,
) -> pl.DataFrame:
    player_weekly_points_local = build_player_weekly_points(roster_df=roster_df, stats_df=stats_df)

    position_team_week = (
        player_weekly_points_local.filter(pl.col("is_starting"))
        .with_columns(
            pl.when(pl.col("selected_position") == "W/R/T")
            .then(pl.lit("FLEX"))
            .otherwise(pl.col("selected_position"))
            .alias("position")
        )
        .group_by(["league_key", "season", "week", "team_key", "position"])
        .agg(
            [
                pl.sum("player_points").alias("position_points"),
                pl.n_unique("player_key").alias("starters_count"),
            ]
        )
    )

    team_week_totals = None
    if weekly_points is not None:
        if "team_points" in weekly_points.columns:
            team_week_totals = weekly_points.select(["league_key", "season", "week", "team_key", "team_points"])
        elif "points" in weekly_points.columns:
            team_week_totals = weekly_points.select(
                ["league_key", "season", "week", "team_key", pl.col("points").alias("team_points")]
            )

    base = position_team_week.join(
        team_df.select(["league_key", "team_key", "team_name"]),
        on=["league_key", "team_key"],
        how="left",
    )

    if team_week_totals is not None:
        base = base.join(team_week_totals, on=["league_key", "season", "week", "team_key"], how="left").with_columns(
            pl.when(pl.col("team_points") > 0)
            .then((pl.col("position_points") / pl.col("team_points")) * 100.0)
            .otherwise(None)
            .alias("position_share_pct")
        )
    else:
        base = base.with_columns(pl.lit(None, dtype=pl.Float64).alias("position_share_pct"))

    return (
        base.group_by(["league_key", "season", "team_name", "position"])
        .agg(
            [
                pl.mean("position_points").alias("avg_points_per_week"),
                pl.median("position_points").alias("median_points_per_week"),
                pl.min("position_points").alias("min_week_points"),
                pl.max("position_points").alias("max_week_points"),
                pl.mean("starters_count").alias("avg_starters"),
                pl.n_unique("week").alias("weeks_counted"),
                pl.mean("position_share_pct").alias("avg_pct_of_team_points"),
            ]
        )
        .with_columns(
            pl.when(pl.col("position") == "QB")
            .then(1)
            .when(pl.col("position") == "RB")
            .then(2)
            .when(pl.col("position") == "WR")
            .then(3)
            .when(pl.col("position") == "TE")
            .then(4)
            .when(pl.col("position") == "FLEX")
            .then(5)
            .when(pl.col("position") == "DEF")
            .then(6)
            .otherwise(99)
            .alias("position_order")
        )
        .sort(["team_name", "position_order"])
        .drop("position_order")
    )


def scoring_quality_by_week(stats_df: pl.DataFrame, roster_df: pl.DataFrame | None = None) -> pl.DataFrame:
    stats_with_flags = stats_df.with_columns(
        pl.when(pl.col("stats").is_null()).then(False).otherwise(pl.col("stats").list.len() > 0).alias("has_stats_payload")
    )

    by_week = (
        stats_with_flags.group_by(["season", "week"])
        .agg(
            [
                pl.len().alias("player_rows"),
                pl.sum("has_stats_payload").alias("rows_with_stats_payload"),
                pl.col("fantasy_points").is_not_null().sum().alias("rows_with_fantasy_points"),
                (pl.col("fantasy_points").fill_null(0) != 0).sum().alias("rows_with_non_zero_fantasy_points"),
            ]
        )
        .with_columns(
            [
                (pl.col("rows_with_stats_payload") == 0).alias("missing_stats_payload_week"),
                (pl.col("rows_with_non_zero_fantasy_points") == 0).alias("all_zero_fantasy_points_week"),
            ]
        )
        .sort(["season", "week"])
    )

    if roster_df is not None and "points" in roster_df.columns:
        roster_by_week = roster_df.group_by(["season", "week"]).agg(
            [
                pl.len().alias("roster_rows"),
                pl.col("points").is_not_null().sum().alias("roster_rows_with_points"),
                (pl.col("points").fill_null(0) != 0).sum().alias("roster_rows_with_non_zero_points"),
            ]
        )
        by_week = by_week.join(roster_by_week, on=["season", "week"], how="left")

    return by_week
