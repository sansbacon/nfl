from __future__ import annotations

from pathlib import Path

import polars as pl

from nfl.yahoo_fantasy.storage.iceberg import (
    IcebergNamespaceConfig,
    persist_to_iceberg,
    resolve_table_identifier,
)


def test_resolve_table_identifier_uses_sport_namespaces() -> None:
    namespaces = IcebergNamespaceConfig(nfl="yhnfl", nba="ynbna")

    nfl_identifier, nfl_entity, nfl_sport = resolve_table_identifier("nfl_standings", namespaces)
    nba_identifier, nba_entity, nba_sport = resolve_table_identifier("nba_standings", namespaces)

    assert nfl_identifier == "yhnfl.standings"
    assert nfl_entity == "standings"
    assert nfl_sport == "nfl"

    assert nba_identifier == "ynbna.standings"
    assert nba_entity == "standings"
    assert nba_sport == "nba"


def test_persist_to_iceberg_dry_run_upsert_and_idempotency(tmp_path: Path) -> None:
    frames = {
        "nfl_standings": pl.DataFrame(
            {
                "league_key": ["461.l.1", "461.l.1"],
                "season": [2025, 2025],
                "team_key": ["461.l.1.t.1", "461.l.1.t.1"],
                "rank": [1, 1],
                "wins": [10, 10],
                "losses": [3, 3],
                "ties": [0, 0],
                "points_for": [1450.2, 1450.2],
                "points_against": [1320.1, 1320.1],
            }
        )
    }

    store_path = tmp_path / "write_log.json"

    first = persist_to_iceberg(
        frames=frames,
        namespace_config=IcebergNamespaceConfig(nfl="yhnfl", nba="ynbna"),
        idempotency_store_path=store_path,
        dry_run=True,
    )

    assert len(first) == 1
    assert first[0].table_identifier == "yhnfl.standings"
    assert first[0].written_rows == 1
    assert first[0].skipped_by_idempotency is False

    second = persist_to_iceberg(
        frames=frames,
        namespace_config=IcebergNamespaceConfig(nfl="yhnfl", nba="ynbna"),
        idempotency_store_path=store_path,
        dry_run=True,
    )

    assert len(second) == 1
    assert second[0].written_rows == 0
    assert second[0].skipped_by_idempotency is True
