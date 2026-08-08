"""Tests for FantasyProsApiClient.parse_adp_volume_csv."""

from __future__ import annotations

import textwrap
from datetime import date
from pathlib import Path

import pytest

from nfl.fantasypros_fantasy.api import FantasyProsApiClient

_SAMPLE_CSV_PLAYER_BYE = textwrap.dedent("""\
    Rank,Player (Bye),POS,ESPN,Sleeper,AVG
    1,Christian McCaffrey   SF (9),RB1,1.0,1.0,1.0
    2,Justin Jefferson   MIN (7),WR1,2.0,2.0,2.0
    3,Tyreek Hill   MIA (12),WR2,3.0,3.0,3.0
""")

_SAMPLE_CSV_PLAYER_NO_BYE = textwrap.dedent("""\
    Rank,Player,POS,ESPN,Sleeper,AVG
    1,Christian McCaffrey SF,RB1,1.0,1.0,1.0
    2,Justin Jefferson MIN,WR1,2.0,2.0,2.0
""")


def _write_csv(tmp_path: Path, content: str, filename: str = "fp_adp.csv") -> Path:
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture
def client() -> FantasyProsApiClient:
    return FantasyProsApiClient(validate_contracts=False)


def test_parse_adp_volume_csv_returns_adp_page_data(
    client: FantasyProsApiClient, tmp_path: Path
) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    result = client.parse_adp_volume_csv(csv_path, season=2024)

    assert result.players
    assert result.adp_rows


def test_parse_adp_volume_csv_player_count(client: FantasyProsApiClient, tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    result = client.parse_adp_volume_csv(csv_path, season=2024)

    assert len(result.players) == 3
    assert len(result.adp_rows) == 3


def test_parse_adp_volume_csv_player_name_extracted(
    client: FantasyProsApiClient, tmp_path: Path
) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    result = client.parse_adp_volume_csv(csv_path, season=2024)

    names = {p["full_name"] for p in result.players}
    assert "Christian McCaffrey" in names
    assert "Justin Jefferson" in names
    assert "Tyreek Hill" in names


def test_parse_adp_volume_csv_team_extracted(client: FantasyProsApiClient, tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    result = client.parse_adp_volume_csv(csv_path, season=2024)

    teams = {p["full_name"]: p["team"] for p in result.players}
    assert teams["Christian McCaffrey"] == "SF"
    assert teams["Justin Jefferson"] == "MIN"
    assert teams["Tyreek Hill"] == "MIA"


def test_parse_adp_volume_csv_position_stripped_of_rank(
    client: FantasyProsApiClient, tmp_path: Path
) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    result = client.parse_adp_volume_csv(csv_path, season=2024)

    positions = {p["full_name"]: p["position"] for p in result.players}
    assert positions["Christian McCaffrey"] == "RB"
    assert positions["Justin Jefferson"] == "WR"


def test_parse_adp_volume_csv_adp_season_set(client: FantasyProsApiClient, tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    result = client.parse_adp_volume_csv(csv_path, season=2023)

    for row in result.adp_rows:
        assert row["season"] == 2023


def test_parse_adp_volume_csv_rank_assigned(client: FantasyProsApiClient, tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    result = client.parse_adp_volume_csv(csv_path, season=2024)

    ranks = [row["rank"] for row in result.adp_rows]
    assert ranks[0] == 1
    assert ranks[1] == 2
    assert ranks[2] == 3


def test_parse_adp_volume_csv_effective_date_override(
    client: FantasyProsApiClient, tmp_path: Path
) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    effective = date(2024, 8, 1)
    result = client.parse_adp_volume_csv(csv_path, season=2024, effective_date=effective)

    for row in result.adp_rows:
        assert row["effective_date"] == effective


def test_parse_adp_volume_csv_adp_formatted(client: FantasyProsApiClient, tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    result = client.parse_adp_volume_csv(csv_path, season=2024)

    # First pick should format as 1.01
    assert result.adp_rows[0]["adp_formatted"] == "1.01"


def test_parse_adp_volume_csv_fp_player_id_slugified(
    client: FantasyProsApiClient, tmp_path: Path
) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    result = client.parse_adp_volume_csv(csv_path, season=2024)

    ids = {p["full_name"]: p["fp_player_id"] for p in result.players}
    assert ids["Christian McCaffrey"] == "christian-mccaffrey_sf"
    assert ids["Justin Jefferson"] == "justin-jefferson_min"


def test_parse_adp_volume_csv_accepts_string_path(
    client: FantasyProsApiClient, tmp_path: Path
) -> None:
    csv_path = _write_csv(tmp_path, _SAMPLE_CSV_PLAYER_BYE)
    # Pass as str, not Path
    result = client.parse_adp_volume_csv(str(csv_path), season=2024)

    assert len(result.players) == 3
