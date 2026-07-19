from __future__ import annotations

from datetime import date

from nfl.fantasypros_fantasy.api import FantasyProsApiClient


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _FakeSession:
    def __init__(self, html: str):
        self._html = html

    def get(self, url: str, headers: dict, timeout: int):
        _ = (url, headers, timeout)
        return _FakeResponse(self._html)


def test_parse_adp_page_multi_platform_layout() -> None:
    html = """
    <html><body>
      <table id='data'>
        <tbody>
          <tr>
            <td>1</td>
            <td>
              <a class='player-name fp-id-12345' href='/nfl/players/justin-jefferson.php'>Justin Jefferson</a>
              <small>MIN</small>
              <small>(6)</small>
            </td>
            <td>WR1</td>
            <td>1.2</td><td>1.4</td><td>1.1</td><td>1.3</td><td>1.5</td><td>1.6</td><td>1.4</td><td>1.3</td>
          </tr>
        </tbody>
      </table>
    </body></html>
    """

    client = FantasyProsApiClient(session=_FakeSession(html), validate_contracts=True)
    parsed = client.parse_adp_page(html=html, season=2025, effective_date=date(2026, 7, 18))

    assert len(parsed.players) == 1
    assert parsed.players[0]["fp_player_id"] == "justin-jefferson"
    assert parsed.players[0]["position"] == "WR"

    assert len(parsed.adp_rows) == 1
    assert parsed.adp_rows[0]["season"] == 2025
    assert parsed.adp_rows[0]["adp"] == 1.4
    assert parsed.adp_rows[0]["adp_formatted"] == "1.01"
    assert parsed.adp_rows[0]["bye_week"] == 6


def test_get_players_and_adp_snapshots_current_layout() -> None:
    html = """
    <html><body>
      <table id='data'>
        <tbody>
          <tr>
            <td>5</td>
            <td>
              <a class='player-name' href='/nfl/players/bijan-robinson.php'>Bijan Robinson</a>
              <small>ATL</small>
              <small>(5)</small>
            </td>
            <td>RB2</td>
            <td>8.4</td>
          </tr>
        </tbody>
      </table>
    </body></html>
    """

    client = FantasyProsApiClient(session=_FakeSession(html), validate_contracts=True)
    players = client.get_players(2025)
    adp_rows = client.get_adp_snapshots(2025, effective_date=date(2026, 7, 18))

    assert players[0]["fp_player_id"] == "bijan-robinson"
    assert players[0]["team"] == "ATL"

    assert adp_rows[0]["rank"] == 5
    assert adp_rows[0]["adp"] == 8.4
    assert adp_rows[0]["adp_formatted"] == "1.08"
