from __future__ import annotations

from pathlib import Path

import polars as pl

from nfl.yahoo_fantasy.queries import (
    build_player_weekly_points,
    enrich_weekly_team_points,
    league_average_by_position,
    player_points_health,
    position_usage_counts,
    scoring_quality_by_week,
    standings_summary,
    weekly_team_points,
    weekly_team_points_resolved,
)
from nfl.yahoo_fantasy.warehouse import (
    CatalogPaths,
    YahooWarehouseClient,
    find_project_root,
    register_tables_from_warehouse,
)


class _FakeArrowTable:
    def __init__(self, frame: pl.DataFrame) -> None:
        self._frame = frame

    def to_arrow(self):
        return self._frame.to_arrow()


class _FakeTable:
    def __init__(self, frame: pl.DataFrame) -> None:
        self._frame = frame

    def scan(self) -> _FakeArrowTable:
        return _FakeArrowTable(self._frame)


class _FakeCatalog:
    def __init__(self, tables: dict[str, pl.DataFrame]) -> None:
        self._tables = tables
        self.registered: list[tuple[str, str]] = []

    def list_namespaces(self):
        namespaces = sorted({name.split(".")[0] for name in self._tables})
        return [(ns,) for ns in namespaces]

    def list_tables(self, namespace: str):
        names = [name for name in self._tables if name.startswith(f"{namespace}.")]
        return [(namespace, name.split(".", 1)[1]) for name in names]

    def load_table(self, table_identifier: str):
        if table_identifier not in self._tables:
            raise ValueError("missing table")
        return _FakeTable(self._tables[table_identifier])

    def create_namespace(self, namespace: str):
        _ = namespace

    def register_table(self, table_identifier: str, metadata_rel: str):
        self.registered.append((table_identifier, metadata_rel))
        self._tables[table_identifier] = pl.DataFrame({"ok": [1]})


def test_find_project_root_resolves_from_nested_folder(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    nested = root / "examples" / "deep"
    nested.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    resolved = find_project_root(nested)

    assert resolved == root


def test_client_list_and_load_table() -> None:
    frame = pl.DataFrame({"league_key": ["x"], "season": [2025]})
    catalog = _FakeCatalog({"yahoo_common.league": frame})
    paths = CatalogPaths(
        project_root=Path.cwd(),
        catalog_db_path=Path("iceberg_catalog.db"),
        warehouse_path=Path("warehouse"),
        catalog_uri="sqlite:///iceberg_catalog.db",
        warehouse_uri=Path("warehouse").resolve().as_uri(),
    )
    client = YahooWarehouseClient(catalog=catalog, paths=paths)

    assert client.list_tables("yahoo_common") == ["yahoo_common.league"]
    loaded = client.load_table("yahoo_common.league")
    assert loaded.shape == (1, 2)
    assert client.maybe_load("yahoo_common.missing") is None


def test_register_tables_from_warehouse_registers_latest_metadata(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    warehouse = project_root / "warehouse"
    metadata_dir = warehouse / "yhnfl" / "matchups" / "metadata"
    metadata_dir.mkdir(parents=True)

    old_file = metadata_dir / "00001-aaa.metadata.json"
    new_file = metadata_dir / "00002-bbb.metadata.json"
    old_file.write_text("{}", encoding="utf-8")
    new_file.write_text("{}", encoding="utf-8")

    catalog = _FakeCatalog({})
    count = register_tables_from_warehouse(
        catalog=catalog,
        warehouse=warehouse,
        project_root=project_root,
        namespaces=["yhnfl"],
    )

    assert count == 1
    assert catalog.registered[0][0] == "yhnfl.matchups"
    assert catalog.registered[0][1].endswith("00002-bbb.metadata.json")


def test_weekly_points_uses_matchups_fallback_when_player_points_missing() -> None:
    stats_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "season": [2025],
            "week": [1],
            "player_key": ["p1"],
            "fantasy_points": [0.0],
            "stats": [[]],
        }
    )
    roster_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "season": [2025],
            "week": [1],
            "team_key": ["t1"],
            "player_key": ["p1"],
            "selected_position": ["WR"],
            "is_starting": [True],
            "points": [0.0],
        }
    )
    matchups_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "season": [2025],
            "week": [1],
            "team_key": ["t1"],
            "points": [101.7],
        }
    )

    weekly, source = weekly_team_points(stats_df=stats_df, roster_df=roster_df, matchups_df=matchups_df)

    assert source == "matchups"
    assert weekly.select(pl.col("team_points")).item() == 101.7


def test_weekly_points_resolved_falls_back_when_player_stats_branch_is_all_zero() -> None:
    stats_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "season": [2025],
            "week": [1],
            "player_key": ["p1"],
            "fantasy_points": [0.0],
            "stats": [[]],
        }
    )
    roster_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "season": [2025],
            "week": [1],
            "team_key": ["t1"],
            "player_key": ["p1"],
            "selected_position": ["WR"],
            "is_starting": [True],
            "points": [24.5],
        }
    )
    matchups_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "season": [2025],
            "week": [1],
            "team_key": ["t1"],
            "points": [101.7],
        }
    )

    weekly, source = weekly_team_points_resolved(stats_df=stats_df, roster_df=roster_df, matchups_df=matchups_df)

    assert source == "matchups"
    assert weekly.columns == ["league_key", "season", "week", "team_key", "team_points"]
    assert weekly.select(pl.col("team_points")).item() == 101.7


def test_enrich_weekly_team_points_adds_friendly_names_and_keeps_shape() -> None:
    weekly = pl.DataFrame(
        {
            "league_key": ["l"],
            "season": [2025],
            "week": [1],
            "team_key": ["t1"],
            "team_points": [99.5],
        }
    )
    league_df = pl.DataFrame({"league_key": ["l"], "season": [2025], "league_name": ["League One"]})
    team_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "team_key": ["t1"],
            "team_name": ["Team One"],
            "owner_name": ["Owner One"],
        }
    )

    out = enrich_weekly_team_points(weekly_points=weekly, league_df=league_df, team_df=team_df)

    assert out.columns == [
        "season",
        "week",
        "league_name",
        "team_name",
        "owner_name",
        "team_points",
        "league_key",
        "team_key",
    ]
    assert out.select("league_name").item() == "League One"
    assert out.select("team_name").item() == "Team One"


def test_league_average_by_position_orders_positions() -> None:
    avg = pl.DataFrame(
        {
            "season": [2025, 2025, 2025],
            "position": ["WR", "QB", "RB"],
            "avg_points_per_week": [10.0, 20.0, 15.0],
            "avg_pct_of_team_points": [20.0, 35.0, 25.0],
        }
    )

    out = league_average_by_position(avg)

    assert out.columns == [
        "season",
        "position",
        "league_avg_points_per_week",
        "league_avg_pct_of_team_points",
    ]
    assert out.select("position").to_series().to_list() == ["QB", "RB", "WR"]


def test_player_points_health_returns_expected_counters() -> None:
    stats_df = pl.DataFrame(
        {
            "league_key": ["l", "l"],
            "season": [2025, 2025],
            "week": [1, 1],
            "player_key": ["p1", "p2"],
            "fantasy_points": [5.0, 0.0],
            "stats": [[{"stat_id": "1", "value": 10}], []],
        }
    )
    roster_df = pl.DataFrame(
        {
            "league_key": ["l", "l"],
            "season": [2025, 2025],
            "week": [1, 1],
            "team_key": ["t1", "t1"],
            "player_key": ["p1", "p2"],
            "selected_position": ["WR", "RB"],
            "is_starting": [True, True],
            "points": [7.0, 0.0],
        }
    )

    health = player_points_health(stats_df=stats_df, roster_df=roster_df)

    assert health["non_zero_fantasy_points"] == 1
    assert health["stats_payload_entries"] == 1
    assert health["non_zero_roster_points"] == 1


def test_scoring_quality_and_position_usage() -> None:
    roster_df = pl.DataFrame(
        {
            "league_key": ["l", "l"],
            "season": [2025, 2025],
            "week": [1, 1],
            "team_key": ["t1", "t1"],
            "player_key": ["p1", "p2"],
            "selected_position": ["WR", "RB"],
            "is_starting": [True, True],
            "points": [10.0, None],
        }
    )
    stats_df = pl.DataFrame(
        {
            "league_key": ["l", "l"],
            "season": [2025, 2025],
            "week": [1, 1],
            "player_key": ["p1", "p2"],
            "fantasy_points": [10.0, 0.0],
            "stats": [[{"stat_id": "5", "value": 100}], []],
        }
    )

    player_points = build_player_weekly_points(roster_df=roster_df, stats_df=stats_df)
    assert "player_points" in player_points.columns

    usage = position_usage_counts(roster_df)
    assert usage.height == 2

    quality = scoring_quality_by_week(stats_df=stats_df, roster_df=roster_df)
    assert quality.height == 1
    assert "missing_stats_payload_week" in quality.columns


def test_standings_summary_includes_friendly_names_and_omits_ties() -> None:
    standings_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "season": [2025],
            "team_key": ["t1"],
            "rank": [1],
            "wins": [10],
            "losses": [3],
            "ties": [0],
            "points_for": [1400.0],
            "points_against": [1200.0],
        }
    )
    league_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "season": [2025],
            "league_name": ["League One"],
        }
    )
    team_df = pl.DataFrame(
        {
            "league_key": ["l"],
            "team_key": ["t1"],
            "team_name": ["Team One"],
            "owner_name": ["Owner One"],
        }
    )

    result = standings_summary(standings_df=standings_df, league_df=league_df, team_df=team_df)

    assert result.columns == [
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
    assert "ties" not in result.columns
    assert result.select("league_name").item() == "League One"
    assert result.select("team_name").item() == "Team One"
    assert result.select("owner_name").item() == "Owner One"
