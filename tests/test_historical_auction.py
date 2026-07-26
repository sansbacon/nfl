from __future__ import annotations

import sys
import types

import polars as pl

from nfl.yahoo_fantasy.historical_auction import (
    HistoricalAuctionImportResult,
    load_historical_auction_values,
    persist_historical_auction_tables,
    resolve_historical_players,
)
from nfl.yahoo_fantasy.queries import unified_draft_price_analysis


def test_load_historical_auction_values(tmp_path) -> None:
    csv_path = tmp_path / "historical_auction_values.csv"
    csv_path.write_text(
        "histi,Pick,Salary,Team,Player,Position,Dollar_Rank,Pos_Dollar_Rank\n"
        "2023,2,70,Min,Justin Jefferson,WR,1,1\n",
        encoding="utf-8",
    )

    df = load_historical_auction_values(csv_path)

    assert df.height == 1
    assert "source_row_hash" in df.columns
    assert df["season"][0] == 2023
    assert df["player_name_normalized"][0] == "JUSTIN JEFFERSON"
    assert df["position_normalized"][0] == "WR"


def test_resolve_historical_players_exact_match() -> None:
    raw_df = pl.DataFrame(
        {
            "season": [2023],
            "pick_number": [2],
            "auction_price": [70.0],
            "team_raw": ["Min"],
            "player_name_raw": ["Justin Jefferson"],
            "position_raw": ["WR"],
            "dollar_rank": [1],
            "position_dollar_rank": [1],
            "team_normalized": ["MIN"],
            "player_name_normalized": ["JUSTIN JEFFERSON"],
            "position_normalized": ["WR"],
            "source_row_hash": ["abc"],
        }
    )
    player_df = pl.DataFrame(
        {
            "player_key": ["449.p.12345"],
            "player_id": [12345],
            "full_name": ["Justin Jefferson"],
            "display_position": ["WR"],
            "editorial_team_abbr": ["MIN"],
        }
    )

    result = resolve_historical_players(raw_df=raw_df, yahoo_player_df=player_df)

    assert result.resolved.height == 1
    assert result.resolved["resolution_status"][0] == "resolved"
    assert result.resolved["yahoo_player_key"][0] == "449.p.12345"
    assert result.match_queue.height == 0


def test_unified_draft_price_analysis_combines_sources() -> None:
    draft_pick_df = pl.DataFrame(
        {
            "league_key": ["449.l.1"],
            "season": [2024],
            "team_key": ["449.l.1.t.1"],
            "player_key": ["449.p.12345"],
            "pick_number": [1],
            "round_number": [1],
            "cost": [65.0],
        }
    )
    player_df = pl.DataFrame(
        {
            "player_key": ["449.p.12345"],
            "player_id": [12345],
            "full_name": ["Justin Jefferson"],
            "display_position": ["WR"],
        }
    )
    historical_df = pl.DataFrame(
        {
            "season": [2023],
            "pick_number": [2],
            "auction_price": [70.0],
            "player_name_raw": ["Justin Jefferson"],
            "position_raw": ["WR"],
            "resolved_player_name": ["Justin Jefferson"],
            "resolved_position": ["WR"],
            "yahoo_player_key": ["449.p.12345"],
            "yahoo_player_id": [12345],
            "resolution_status": ["resolved"],
            "resolution_confidence": [1.0],
            "resolution_method": ["exact"],
        }
    )

    out = unified_draft_price_analysis(
        draft_pick_df=draft_pick_df,
        player_df=player_df,
        historical_resolved_df=historical_df,
    )

    assert out.height == 2
    assert set(out["source_type"].to_list()) == {"api_draft_pick", "historical_web_ui"}


def test_resolve_historical_players_matches_punctuation_variants() -> None:
    raw_df = pl.DataFrame(
        {
            "season": [2023],
            "pick_number": [4],
            "auction_price": [62.0],
            "team_raw": ["Cin"],
            "player_name_raw": ["Ja'Marr Chase"],
            "position_raw": ["WR"],
            "dollar_rank": [3],
            "position_dollar_rank": [2],
            "team_normalized": ["CIN"],
            "player_name_normalized": ["JA MARR CHASE"],
            "position_normalized": ["WR"],
            "source_row_hash": ["row-ja-marr"],
        }
    )
    player_df = pl.DataFrame(
        {
            "player_key": ["449.p.54321"],
            "player_id": [54321],
            "full_name": ["JaMarr Chase"],
            "display_position": ["WR"],
            "editorial_team_abbr": ["CIN"],
        }
    )

    result = resolve_historical_players(raw_df=raw_df, yahoo_player_df=player_df)

    assert result.resolved.height == 1
    assert result.resolved["resolution_status"][0] == "resolved"
    assert result.resolved["yahoo_player_key"][0] == "449.p.54321"


def test_resolve_historical_players_matches_nickname_variants() -> None:
    raw_df = pl.DataFrame(
        {
            "season": [2023],
            "pick_number": [11],
            "auction_price": [14.0],
            "team_raw": ["Phi"],
            "player_name_raw": ["Kenny Gainwell"],
            "position_raw": ["RB"],
            "dollar_rank": [75],
            "position_dollar_rank": [28],
            "team_normalized": ["PHI"],
            "player_name_normalized": ["KENNY GAINWELL"],
            "position_normalized": ["RB"],
            "source_row_hash": ["row-kenny-gainwell"],
        }
    )
    player_df = pl.DataFrame(
        {
            "player_key": ["449.p.32752"],
            "player_id": [32752],
            "full_name": ["Kenneth Gainwell"],
            "display_position": ["RB"],
            "editorial_team_abbr": ["PHI"],
        }
    )

    result = resolve_historical_players(raw_df=raw_df, yahoo_player_df=player_df)

    assert result.resolved.height == 1
    assert result.resolved["resolution_status"][0] == "resolved"
    assert result.resolved["resolution_method"][0] == "nickname_heuristic"
    assert result.resolved["yahoo_player_key"][0] == "449.p.32752"
    assert result.match_queue.height == 0


def test_resolve_historical_players_matches_dst_team_name_when_unique() -> None:
    raw_df = pl.DataFrame(
        {
            "season": [2023],
            "pick_number": [15],
            "auction_price": [2.0],
            "team_raw": ["Any"],
            "player_name_raw": ["New England"],
            "position_raw": ["DEF"],
            "dollar_rank": [200],
            "position_dollar_rank": [20],
            "team_normalized": ["ANY"],
            "player_name_normalized": ["NEW ENGLAND"],
            "position_normalized": ["DST"],
            "source_row_hash": ["row-ne-def"],
        }
    )
    player_df = pl.DataFrame(
        {
            "player_key": ["449.p.def1", "449.p.rb1"],
            "player_id": [9001, 1001],
            "full_name": ["New England Patriots", "New England Runner"],
            "display_position": ["DEF", "RB"],
            "editorial_team_abbr": ["NE", "NE"],
        }
    )

    result = resolve_historical_players(raw_df=raw_df, yahoo_player_df=player_df)

    assert result.resolved.height == 1
    assert result.resolved["resolution_status"][0] == "resolved"
    assert result.resolved["resolution_method"][0] == "dst_team_name"
    assert result.resolved["yahoo_player_key"][0] == "449.p.def1"


def test_resolve_historical_players_keeps_dst_ambiguous_for_shared_city() -> None:
    raw_df = pl.DataFrame(
        {
            "season": [2023],
            "pick_number": [16],
            "auction_price": [1.0],
            "team_raw": ["Any"],
            "player_name_raw": ["Los Angeles"],
            "position_raw": ["DEF"],
            "dollar_rank": [210],
            "position_dollar_rank": [25],
            "team_normalized": ["ANY"],
            "player_name_normalized": ["LOS ANGELES"],
            "position_normalized": ["DST"],
            "source_row_hash": ["row-la-def"],
        }
    )
    player_df = pl.DataFrame(
        {
            "player_key": ["449.p.deflar", "449.p.deflac"],
            "player_id": [9101, 9102],
            "full_name": ["Los Angeles Rams", "Los Angeles Chargers"],
            "display_position": ["DEF", "DEF"],
            "editorial_team_abbr": ["LAR", "LAC"],
        }
    )

    result = resolve_historical_players(raw_df=raw_df, yahoo_player_df=player_df)

    assert result.resolved.height == 1
    assert result.resolved["resolution_status"][0] == "unresolved"
    assert result.match_queue.height == 1


def test_resolve_historical_players_resolves_shared_city_dst_with_team_code() -> None:
    raw_df = pl.DataFrame(
        {
            "season": [2023],
            "pick_number": [17],
            "auction_price": [1.0],
            "team_raw": ["LAR"],
            "player_name_raw": ["Los Angeles"],
            "position_raw": ["DEF"],
            "dollar_rank": [220],
            "position_dollar_rank": [27],
            "team_normalized": ["LAR"],
            "player_name_normalized": ["LOS ANGELES"],
            "position_normalized": ["DST"],
            "source_row_hash": ["row-la-def-lar"],
        }
    )
    player_df = pl.DataFrame(
        {
            "player_key": ["449.p.deflar", "449.p.deflac"],
            "player_id": [9101, 9102],
            "full_name": ["Los Angeles Rams", "Los Angeles Chargers"],
            "display_position": ["DEF", "DEF"],
            "editorial_team_abbr": ["LAR", "LAC"],
        }
    )

    result = resolve_historical_players(raw_df=raw_df, yahoo_player_df=player_df)

    assert result.resolved.height == 1
    assert result.resolved["resolution_status"][0] == "resolved"
    assert result.resolved["resolution_method"][0] == "dst_team_code"
    assert result.resolved["yahoo_player_key"][0] == "449.p.deflar"


def test_resolve_historical_players_resolves_dst_with_team_code_across_multiple_seasons() -> None:
    raw_df = pl.DataFrame(
        {
            "season": [2023],
            "pick_number": [18],
            "auction_price": [1.0],
            "team_raw": ["NE"],
            "player_name_raw": ["New England"],
            "position_raw": ["DEF"],
            "dollar_rank": [225],
            "position_dollar_rank": [29],
            "team_normalized": ["NE"],
            "player_name_normalized": ["NEW ENGLAND"],
            "position_normalized": ["DST"],
            "source_row_hash": ["row-ne-def-multi"],
        }
    )
    player_df = pl.DataFrame(
        {
            "player_key": ["399.p.defne", "406.p.defne"],
            "player_id": [8001, 8001],
            "game_id": [399, 406],
            "full_name": ["Patriots", "Patriots"],
            "display_position": ["DEF", "DEF"],
            "editorial_team_abbr": ["NE", "NE"],
        }
    )

    result = resolve_historical_players(raw_df=raw_df, yahoo_player_df=player_df)

    assert result.resolved.height == 1
    assert result.resolved["resolution_status"][0] == "resolved"
    assert result.resolved["resolution_method"][0] == "dst_team_code"
    assert result.resolved["yahoo_player_key"][0] == "406.p.defne"


def test_persist_historical_auction_tables_replaces_existing_tables(monkeypatch) -> None:
    class _NoSuchTableError(Exception):
        pass

    class _NamespaceAlreadyExistsError(Exception):
        pass

    class _FakeTable:
        def __init__(self, identifier: str) -> None:
            self.identifier = identifier
            self.append_calls = 0

        def append(self, _arrow_table) -> None:
            self.append_calls += 1

    class _FakeCatalog:
        def __init__(self) -> None:
            self.namespaces: set[str] = set()
            self.tables: dict[str, _FakeTable] = {}
            self.drop_calls: list[str] = []
            self.create_calls: list[str] = []

        def create_namespace(self, namespace: str) -> None:
            if namespace in self.namespaces:
                raise _NamespaceAlreadyExistsError()
            self.namespaces.add(namespace)

        def drop_table(self, identifier: str) -> None:
            self.drop_calls.append(identifier)
            if identifier in self.tables:
                del self.tables[identifier]
            else:
                raise _NoSuchTableError()

        def create_table(self, identifier: str, schema) -> _FakeTable:
            _ = schema
            table = _FakeTable(identifier)
            self.tables[identifier] = table
            self.create_calls.append(identifier)
            return table

        def load_table(self, identifier: str) -> _FakeTable:
            if identifier not in self.tables:
                raise _NoSuchTableError()
            return self.tables[identifier]

    fake_catalog = _FakeCatalog()

    catalog_module = types.ModuleType("pyiceberg.catalog")
    catalog_module.load_catalog = lambda *args, **kwargs: fake_catalog

    exceptions_module = types.ModuleType("pyiceberg.exceptions")
    exceptions_module.NamespaceAlreadyExistsError = _NamespaceAlreadyExistsError
    exceptions_module.NoSuchTableError = _NoSuchTableError

    monkeypatch.setitem(sys.modules, "pyiceberg.catalog", catalog_module)
    monkeypatch.setitem(sys.modules, "pyiceberg.exceptions", exceptions_module)

    import_result = HistoricalAuctionImportResult(
        raw=pl.DataFrame({"source_row_hash": ["r1"], "season": [2023]}),
        resolved=pl.DataFrame({"source_row_hash": ["r1"], "resolution_status": ["resolved"]}),
        match_queue=pl.DataFrame(
            {
                "source_row_hash": [],
                "season": [],
                "player_name_raw": [],
                "position_raw": [],
                "team_raw": [],
                "resolution_status": [],
                "resolution_confidence": [],
                "candidate_player_key": [],
                "candidate_player_name": [],
                "candidate_position": [],
            }
        ),
    )

    results = persist_historical_auction_tables(import_result, dry_run=False, namespace="yhnfl_manual")

    expected_tables = {
        "yhnfl_manual.historical_auction_values_raw",
        "yhnfl_manual.historical_auction_values_resolved",
        "yhnfl_manual.historical_auction_values_match_queue",
    }
    assert {r.table_identifier for r in results} == expected_tables
    assert expected_tables.issubset(set(fake_catalog.drop_calls))
    assert expected_tables.issubset(set(fake_catalog.create_calls))
    assert fake_catalog.tables["yhnfl_manual.historical_auction_values_raw"].append_calls == 1
    assert fake_catalog.tables["yhnfl_manual.historical_auction_values_resolved"].append_calls == 1
    assert fake_catalog.tables["yhnfl_manual.historical_auction_values_match_queue"].append_calls == 0
