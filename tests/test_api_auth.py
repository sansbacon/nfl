from __future__ import annotations

import json
from pathlib import Path

from nfl.yahoo_fantasy.api import YahooApiClient
from nfl.yahoo_fantasy.auth import build_oauth_session, extract_auth_code


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeOAuth:
    def __init__(self, payload_map: dict[str, dict]):
        self.payload_map = payload_map

    def get(self, url: str, params: dict, timeout: int):
        _ = (params, timeout)
        suffix = url.split("/fantasy/v2", 1)[1]
        return _FakeResponse(self.payload_map[suffix])


def test_extract_auth_code_from_url() -> None:
    code = extract_auth_code("http://localhost?code=abc123&state=xyz")
    assert code == "abc123"


def test_build_oauth_session_uses_cached_token(tmp_path: Path) -> None:
    token_path = tmp_path / ".yahoo_token.json"
    token_path.write_text(json.dumps({"access_token": "x", "token_type": "bearer"}), encoding="utf-8")

    session = build_oauth_session(
        client_id="client",
        client_secret="secret",
        redirect_uri="http://localhost",
        token_path=token_path,
        auth_code=None,
        open_browser=False,
    )

    assert session.token is not None
    assert session.token.get("access_token") == "x"


def test_api_client_normalizes_league_and_teams() -> None:
    payload_map = {
        "/league/461.l.717896/settings": {
            "fantasy_content": {
                "league": [
                    {"league_key": "461.l.717896"},
                    {
                        "name": "League X",
                        "season": "2025",
                        "game_code": "nfl",
                        "scoring_type": "head",
                        "league_type": "private",
                        "num_teams": "12",
                    },
                ]
            }
        },
        "/league/461.l.717896/teams": {
            "fantasy_content": {
                "league": [
                    {"league_key": "461.l.717896"},
                    {
                        "teams": {
                            "0": {
                                "team": [
                                    [
                                        {"team_key": "461.l.717896.t.1"},
                                        {"team_id": "1"},
                                        {"name": "Team One"},
                                        {
                                            "managers": [
                                                {"manager": {"nickname": "Owner One"}}
                                            ]
                                        },
                                        {"draft_position": "2"},
                                    ]
                                ]
                            }
                        }
                    },
                ]
            }
        },
    }

    client = YahooApiClient(oauth_session=_FakeOAuth(payload_map), use_cache=False)
    league = client.get_league_metadata("461.l.717896")
    teams = client.get_teams("461.l.717896")

    assert league["league_name"] == "League X"
    assert league["game_id"] == 461
    assert teams[0]["team_name"] == "Team One"
    assert teams[0]["owner_name"] == "Owner One"


def test_api_client_normalizes_nfl_standings() -> None:
    payload_map = {
        "/league/461.l.717896/settings": {
            "fantasy_content": {
                "league": [
                    {"league_key": "461.l.717896"},
                    {
                        "name": "League X",
                        "season": "2025",
                        "game_code": "nfl",
                        "scoring_type": "head",
                        "league_type": "private",
                    },
                ]
            }
        },
        "/league/461.l.717896/standings": {
            "fantasy_content": {
                "league": [
                    {"league_key": "461.l.717896"},
                    {
                        "standings": [
                            {
                                "teams": {
                                    "0": {
                                        "team": [
                                            [
                                                {"team_key": "461.l.717896.t.1"},
                                                {"name": "Team One"},
                                                {
                                                    "managers": [
                                                        {"manager": {"nickname": "Owner One"}}
                                                    ]
                                                },
                                            ],
                                            {
                                                "team_standings": {
                                                    "rank": "1",
                                                    "outcome_totals": {
                                                        "wins": "10",
                                                        "losses": "3",
                                                        "ties": "0",
                                                    },
                                                    "points_for": "1450.2",
                                                    "points_against": "1320.1",
                                                }
                                            },
                                        ]
                                    }
                                }
                            }
                        ]
                    },
                ]
            }
        },
    }

    client = YahooApiClient(oauth_session=_FakeOAuth(payload_map), use_cache=False)
    standings = client.get_standings("461.l.717896", sport="nfl")

    assert len(standings) == 1
    assert standings[0]["team_key"] == "461.l.717896.t.1"
    assert standings[0]["wins"] == 10
    assert standings[0]["points_for"] == 1450.2


def test_api_client_extracts_players_and_weekly_nfl_entities() -> None:
    payload_map = {
        "/league/461.l.717896/settings": {
            "fantasy_content": {
                "league": [
                    {"league_key": "461.l.717896"},
                    {
                        "name": "League X",
                        "season": "2025",
                        "game_code": "nfl",
                        "scoring_type": "head",
                        "league_type": "private",
                        "start_week": "1",
                        "end_week": "14",
                    },
                ]
            }
        },
        "/league/461.l.717896/players;start=0;count=25": {
            "fantasy_content": {
                "league": [
                    {"league_key": "461.l.717896"},
                    {
                        "players": {
                            "0": {
                                "player": [
                                    [
                                        {"player_key": "461.p.123"},
                                        {"player_id": "123"},
                                        {"name": {"full": "Player One"}},
                                        {"display_position": "WR"},
                                        {"editorial_team_abbr": "LAC"},
                                    ]
                                ]
                            }
                        }
                    },
                ]
            }
        },
        "/league/461.l.717896/scoreboard;week=1": {
            "fantasy_content": {
                "league": [
                    {"league_key": "461.l.717896"},
                    {
                        "scoreboard": [
                            {
                                "matchups": {
                                    "0": {
                                        "matchup": [
                                            {"week": "1", "is_playoffs": "0", "is_consolation": "0"},
                                            {
                                                "teams": {
                                                    "0": {
                                                        "team": [
                                                            [{"team_key": "461.l.717896.t.1"}],
                                                            {"team_points": {"total": "123.4"}},
                                                        ]
                                                    },
                                                    "1": {
                                                        "team": [
                                                            [{"team_key": "461.l.717896.t.2"}],
                                                            {"team_points": {"total": "117.2"}},
                                                        ]
                                                    },
                                                }
                                            },
                                        ]
                                    }
                                }
                            }
                        ]
                    },
                ]
            }
        },
        "/team/461.l.717896.t.1/roster;week=1;out=players": {
            "fantasy_content": {
                "team": [
                    {"team_key": "461.l.717896.t.1"},
                    {
                        "roster": [
                            {
                                "players": {
                                    "0": {
                                        "player": [
                                            [
                                                {"player_key": "461.p.123"},
                                                {"status": ""},
                                                {"bye_weeks": {"week": "7"}},
                                            ],
                                            {"selected_position": {"position": "WR"}},
                                            {"player_points": {"total": "18.3"}},
                                        ]
                                    }
                                }
                            }
                        ]
                    },
                ]
            }
        },
    }

    client = YahooApiClient(oauth_session=_FakeOAuth(payload_map), use_cache=False)

    players = client.get_players("461.l.717896")
    assert len(players) == 1
    assert players[0]["player_key"] == "461.p.123"

    matchups = client.get_matchups("461.l.717896", season=2025, weeks=[1])
    assert len(matchups) == 2
    assert matchups[0]["week"] == 1

    rosters = client.get_roster_entries(
        "461.l.717896",
        season=2025,
        weeks=[1],
        team_keys=["461.l.717896.t.1"],
    )
    assert len(rosters) == 1
    assert rosters[0]["selected_position"] == "WR"
    assert rosters[0]["is_starting"] is True

    stats_weekly = client.get_player_stats_weekly("461.l.717896", season=2025, roster_entries=rosters)
    assert len(stats_weekly) == 1
    assert stats_weekly[0]["fantasy_points"] == 18.3
    assert stats_weekly[0]["bye_week"] == 7


def test_api_client_extracts_scoring_rules_and_stat_categories() -> None:
    payload_map = {
        "/league/461.l.717896/settings": {
            "fantasy_content": {
                "league": [
                    {"league_key": "461.l.717896"},
                    {
                        "name": "League X",
                        "season": "2025",
                        "game_code": "nfl",
                        "scoring_type": "head",
                        "league_type": "private",
                        "scoring_rules": {
                            "0": {"scoring_rule": [{"stat_id": "5"}, {"value": "0.04"}]},
                            "1": {"scoring_rule": [{"stat_id": "6"}, {"value": "4"}]},
                        },
                    },
                ]
            }
        },
        "/game/461/stat_categories": {
            "fantasy_content": {
                "game": [
                    {"game_key": "461"},
                    {
                        "stat_categories": {
                            "stats": {
                                "0": {"stat": [{"stat_id": "5"}, {"name": "Passing Yards"}, {"display_name": "Pass Yds"}]},
                                "1": {"stat": [{"stat_id": "6"}, {"name": "Passing TD"}, {"display_name": "Pass TD"}]},
                            }
                        }
                    },
                ]
            }
        },
    }

    client = YahooApiClient(oauth_session=_FakeOAuth(payload_map), use_cache=False)

    rules = client.get_scoring_rules("461.l.717896", season=2025)
    categories = client.get_stat_categories("461.l.717896", game_id=461)

    assert len(rules) == 2
    assert {row["stat_id"] for row in rules} == {"5", "6"}
    assert any(row["stat_id"] == "5" and row["points_per_unit"] == 0.04 for row in rules)

    assert len(categories) == 2
    assert any(row["stat_id"] == "5" and row["display_name"] == "Pass Yds" for row in categories)
