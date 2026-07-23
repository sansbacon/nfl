from __future__ import annotations

from pathlib import Path

import polars as pl

from nfl.yahoo_fantasy.pipeline import PipelineConfig, run_pipeline
from nfl.yahoo_fantasy.storage.iceberg import IcebergNamespaceConfig


class _FakeClient:
    def get_league_metadata(self, league_key: str) -> dict:
        return {
            "league_key": league_key,
            "league_id": "717896",
            "game_id": 461,
            "game_code": "nfl",
            "season": 2025,
            "league_name": "League X",
            "scoring_type": "head",
            "league_type": "private",
            "num_teams": 12,
            "start_week": 1,
            "end_week": 2,
            "current_week": 2,
        }

    def get_teams(self, league_key: str) -> list[dict]:
        return [
            {
                "team_key": f"{league_key}.t.1",
                "league_key": league_key,
                "team_id": 1,
                "team_name": "Team One",
                "owner_name": "Owner One",
                "draft_position": 2,
            }
        ]

    def get_draft_picks(self, league_key: str, season: int | None = None) -> list[dict]:
        _ = season
        return [
            {
                "league_key": league_key,
                "season": 2025,
                "team_key": f"{league_key}.t.1",
                "player_key": "461.p.123",
                "pick_number": 1,
                "round_number": 1,
                "cost": None,
            }
        ]

    def get_players(self, league_key: str) -> list[dict]:
        _ = league_key
        return [
            {
                "player_key": "461.p.123",
                "player_id": 123,
                "game_id": 461,
                "full_name": "Player One",
                "display_position": "WR",
                "editorial_team_abbr": "LAC",
            }
        ]

    def get_transactions(self, league_key: str, season: int | None = None) -> list[dict]:
        _ = season
        return [
            {
                "transaction_key": f"{league_key}.tr.100",
                "league_key": league_key,
                "season": 2025,
                "transaction_type": "add",
                "status": "successful",
                "player_key": "461.p.123",
                "source_team_key": None,
                "destination_team_key": f"{league_key}.t.1",
            }
        ]

    def get_stat_categories(self, league_key: str, game_id: int | None = None) -> list[dict]:
        _ = (league_key, game_id)
        return [
            {
                "game_id": 461,
                "stat_id": "5",
                "display_name": "Pass Yds",
                "name": "Passing Yards",
            }
        ]

    def get_scoring_rules(self, league_key: str, season: int | None = None) -> list[dict]:
        _ = season
        return [
            {
                "league_key": league_key,
                "season": 2025,
                "stat_id": "5",
                "points_per_unit": 0.04,
                "bonus_target": None,
                "bonus_points": None,
            }
        ]

    def get_standings(self, league_key: str, sport: str | None = None) -> list[dict]:
        if sport == "nfl":
            return [
                {
                    "league_key": league_key,
                    "season": 2025,
                    "team_key": f"{league_key}.t.1",
                    "rank": 1,
                    "wins": 10,
                    "losses": 3,
                    "ties": 0,
                    "points_for": 1450.2,
                    "points_against": 1320.1,
                }
            ]

        return [
            {
                "league_key": league_key,
                "season": 2025,
                "team_key": f"{league_key}.t.1",
                "rank": 1,
                "scoring_type": "roto",
                "points_for": 95.0,
            }
        ]

    def get_matchups(self, league_key: str, season: int, weeks: list[int]) -> list[dict]:
        _ = season
        return [
            {
                "league_key": league_key,
                "season": 2025,
                "week": weeks[0],
                "team_key": f"{league_key}.t.1",
                "opponent_team_key": f"{league_key}.t.2",
                "points": 123.4,
                "opponent_points": 117.2,
                "is_playoff": False,
                "is_consolation": False,
            }
        ]

    def get_roster_entries(self, league_key: str, season: int, weeks: list[int], team_keys: list[str]) -> list[dict]:
        _ = season
        return [
            {
                "league_key": league_key,
                "season": 2025,
                "week": weeks[0],
                "team_key": team_keys[0] if team_keys else f"{league_key}.t.1",
                "player_key": "461.p.123",
                "selected_position": "WR",
                "is_starting": True,
                "points": 18.3,
            }
        ]

    def get_player_stats_weekly(self, league_key: str, season: int, roster_entries: list[dict]) -> list[dict]:
        _ = season
        return [
            {
                "league_key": league_key,
                "season": 2025,
                "week": int(roster_entries[0]["week"]),
                "player_key": "461.p.123",
                "fantasy_points": 18.3,
                "status": None,
                "bye_week": None,
                "stats": [{"stat_id": "5", "value": 457.5}],
            }
        ]


def test_run_pipeline_without_persistence() -> None:
    result = run_pipeline(
        league_key="461.l.717896",
        sport="nfl",
        api_client=_FakeClient(),
        config=PipelineConfig(storage_target="none"),
    )

    assert result.league_key == "461.l.717896"
    assert "league" in result.frames
    assert "player" in result.frames
    assert "stat_category" in result.frames
    assert "scoring_rule" in result.frames
    assert "nfl_standings" in result.frames
    assert "nfl_matchups" in result.frames
    assert "nfl_roster_entries" in result.frames
    assert "nfl_player_stats_weekly" in result.frames
    assert result.frames["player"].height == 1
    assert result.frames["nfl_matchups"].height == 1
    assert result.frames["nfl_roster_entries"].height == 1
    assert result.frames["nfl_player_stats_weekly"].height == 1
    assert result.polars_outputs == {}
    assert result.iceberg_outputs == []


def test_run_pipeline_with_both_persistence_targets(tmp_path: Path) -> None:
    result = run_pipeline(
        league_key="461.l.717896",
        sport="nfl",
        api_client=_FakeClient(),
        config=PipelineConfig(
            storage_target="both",
            polars_output_dir=tmp_path / "polars",
            polars_file_format="parquet",
            iceberg_dry_run=True,
            iceberg_idempotency_store=tmp_path / "iceberg" / "write_log.json",
            iceberg_namespaces=IcebergNamespaceConfig(nfl="yhnfl", nba="ynbna"),
        ),
    )

    assert result.polars_outputs
    assert all(path.exists() for path in result.polars_outputs.values())
    assert result.iceberg_outputs
    assert any(
        write_result.table_identifier.startswith("yhnfl.")
        for write_result in result.iceberg_outputs
    )


def test_run_pipeline_with_standardization_enabled(monkeypatch) -> None:
    class _FakeStandardizer:
        def __init__(self, config=None):
            _ = config

        def standardize_batch(self, records):
            _ = records
            return type(
                "_StdResult",
                (),
                {
                    "tables": {
                        "std_standardized_outputs": pl.DataFrame(
                            {
                                "source_system": ["yahoo"],
                                "source_entity_id": ["461.l.717896.t.1"],
                                "canonical_player_id": [""],
                                "canonical_team_id": [""],
                                "canonical_position_code": [""],
                                "standardized_player_name": [""],
                                "standardized_team_name": ["Team One"],
                                "standardized_position": [""],
                                "player_confidence": [0.0],
                                "team_confidence": [0.0],
                                "position_confidence": [0.0],
                                "match_method_player": ["unresolved"],
                                "match_method_team": ["unresolved"],
                                "match_method_position": ["unresolved"],
                                "explanation_json": ["{}"],
                                "needs_review": [True],
                                "rescued": [True],
                            }
                        ),
                        "std_match_queue": pl.DataFrame([]),
                        "std_rescued_records": pl.DataFrame([]),
                        "std_source_to_canonical_map": pl.DataFrame([]),
                    }
                },
            )()

    monkeypatch.setattr("nfl.yahoo_fantasy.pipeline.EntityStandardizer", _FakeStandardizer)

    result = run_pipeline(
        league_key="461.l.717896",
        sport="nfl",
        api_client=_FakeClient(),
        config=PipelineConfig(storage_target="none", standardization_enabled=True),
    )

    assert result.standardization_result is not None
    assert "std_standardized_outputs" in result.frames


def test_run_pipeline_with_materialized_views_enabled() -> None:
    result = run_pipeline(
        league_key="461.l.717896",
        sport="nfl",
        api_client=_FakeClient(),
        config=PipelineConfig(storage_target="none", materialized_views_enabled=True),
    )

    assert "vw_draft_results" in result.frames
    assert "v_player_fantasy_scoring" in result.frames

    draft_view = result.frames["vw_draft_results"]
    scoring_view = result.frames["v_player_fantasy_scoring"]

    assert draft_view.height == 1
    assert set(
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
    ).issubset(set(draft_view.columns))

    assert scoring_view.height == 1
    assert set(
        [
            "player_key",
            "league_key",
            "week",
            "player_name",
            "display_position",
            "stat_id",
            "stat_name",
            "stat_full_name",
            "raw_value",
            "stat_points",
            "bonus_points",
            "total_stat_points",
        ]
    ).issubset(set(scoring_view.columns))
    assert scoring_view["stat_points"][0] == 18.3
    assert scoring_view["total_stat_points"][0] == 18.3


def test_player_weekly_points_match_scoring_rule_rollup_for_2025() -> None:
    result = run_pipeline(
        league_key="461.l.717896",
        sport="nfl",
        api_client=_FakeClient(),
        config=PipelineConfig(storage_target="none", materialized_views_enabled=True),
    )

    scoring_view = result.frames["v_player_fantasy_scoring"]
    weekly_stats = result.frames["nfl_player_stats_weekly"]

    weekly_rollup = (
        scoring_view.group_by(["league_key", "week", "player_key"])
        .agg(pl.sum("total_stat_points").alias("computed_points"))
        .sort(["league_key", "week", "player_key"])
    )

    weekly_points = (
        weekly_stats.select(["league_key", "week", "player_key", "fantasy_points"])
        .sort(["league_key", "week", "player_key"])
    )

    joined = weekly_rollup.join(
        weekly_points,
        on=["league_key", "week", "player_key"],
        how="inner",
    )

    assert joined.height == 1
    assert joined["computed_points"][0] == joined["fantasy_points"][0] == 18.3
