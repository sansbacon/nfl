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


def test_parse_adp_page_report_config_json_layout() -> None:
    html = """
    <html><body>
      <script>
        window.FP = window.FP || {};
        window.FP.reportConfig = {
          "table": {
            "fields": [
              {"key": "rank", "label": "Rank"},
              {"key": "player", "label": "Player (Bye)"},
              {"key": "pos", "label": "POS"},
              {"key": "src_79", "label": "ESPN"},
              {"key": "src_4350", "label": "Sleeper"},
              {"key": "src_80", "label": "CBS"},
              {"key": "src_291", "label": "NFL"},
              {"key": "src_439", "label": "RTSports"},
              {"key": "src_624", "label": "Fantrax"},
              {"key": "avg", "label": "AVG"},
              {"key": "realtime", "label": "Real-Time"}
            ],
            "rows": [
              {
                "id": 23133,
                "rank": 2,
                "player": {
                  "id": 23133,
                  "name": "Bijan Robinson",
                  "team": "ATL (11)",
                  "url": "/nfl/players/bijan-robinson.php"
                },
                "pos": "RB2",
                "src_79": 2,
                "src_4350": 1,
                "src_80": null,
                "src_291": null,
                "src_439": null,
                "src_624": null,
                "avg": 1.5,
                "realtime": 2
              }
            ]
          }
        };
      </script>
    </body></html>
    """

    client = FantasyProsApiClient(session=_FakeSession(html), validate_contracts=True)
    parsed = client.parse_adp_page(html=html, season=2026, effective_date=date(2026, 7, 26))

    assert len(parsed.players) == 1
    assert parsed.players[0]["fp_player_id"] == "bijan-robinson"
    assert parsed.players[0]["team"] == "ATL"
    assert parsed.players[0]["position"] == "RB"

    assert len(parsed.adp_rows) == 1
    assert parsed.adp_rows[0]["season"] == 2026
    assert parsed.adp_rows[0]["rank"] == 2
    assert parsed.adp_rows[0]["adp"] == 1.5
    assert parsed.adp_rows[0]["adp_espn"] == 2.0
    assert parsed.adp_rows[0]["adp_sleeper"] == 1.0
    assert parsed.adp_rows[0]["adp_realtime"] == 2.0
    assert parsed.adp_rows[0]["bye_week"] == 11
