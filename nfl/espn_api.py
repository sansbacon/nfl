"""
espn_api.py
classes for scraping, parsing espn football api
this includes fantasy and real nfl data

Usage:

    from nfl.espn_api import Scraper, Parser

    season = 2020
    week = 1
    s = Scraper(season=season)
    p = Parser(season=season)
    content = s.players(season)
    print(p.weekly_projections(content, week))
"""

import json
import logging
from pathlib import Path
import sys
import time
from PLOD import PLOD

sys.path.append(str(Path.home() / "sportscraper"))
sys.path.append(str(Path.home() / "nfl"))
from sportscraper.scraper import RequestScraper
from nfl.teams import get_team_code


class Scraper(RequestScraper):
    """
    Scrape ESPN API for football stats

    """

    def __init__(self, season, **kwargs):
        super().__init__(**kwargs)
        self.season = season

    @property
    def api_url(self):
        return f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{self.season}/segments/0/leaguedefaults/3"

    @property
    def default_headers(self):
        return {
            "authority": "fantasy.espn.com",
            "accept": "application/json",
            "x-fantasy-source": "kona",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
            "x-fantasy-platform": "kona-PROD-a9859dd5e813fa08e6946514bbb0c3f795a4ea23",
            "dnt": "1",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://fantasy.espn.com/football/players/projections",
            "accept-language": "en-US,en;q=0.9,ar;q=0.8",
            "if-none-match": "W/^\\^008956866aeb5b199ec8612a9e7576ed7^\\^",
        }

    @property
    def default_params(self):
        return {"view": "kona_player_info"}

    @property
    def default_x_fantasy_filter(self):
        return {
            "players": {
                "filterStatsForSplitTypeIds": {"value": [1]},
                "filterSlotIds": {"value": self._filter_slots("ALL")},
                "filterStatsForSourceIds": {"value": [1]},
                "sortAppliedStatTotal": {
                    "sortAsc": False,
                    "sortPriority": 2,
                    "value": "1120203",
                },
                "sortDraftRanks": {"sortPriority": 3, "sortAsc": True, "value": "PPR"},
                "sortPercOwned": {"sortPriority": 4, "sortAsc": False},
                "filterRanksForRankTypes": {"value": ["PPR"]},
                "filterRanksForSlotIds": {"value": [0, 2, 4, 6, 17, 16]},
                "filterStatsForTopScoringPeriodIds": {
                    "value": 2,
                    "additionalValue": [
                        "002020",
                        "102020",
                        "002019",
                        "1120203",
                        "022020",
                    ],
                },
            }
        }

    def _filter_slots(self, pos):
        """Gets filter slots parameter"""
        default = list(range(20)) + [23, 24]
        mapping = {
            "QB": 0,
            "RB": 2,
            "WR": 4,
            "TE": 6,
            "FLEX": 23,
            "DST": 16,
            "K": 17,
            "ALL": default,
        }
        if pos.upper() in mapping:
            return mapping.get(pos.upper)
        raise ValueError(f"Invalid position: {pos}")

    def projections(self):
        """Gets projections for all players"""
        xff = {
            "players": {
                "limit": 1500,
                "sortDraftRanks": {
                    "sortPriority": 100,
                    "sortAsc": True,
                    "value": "PPR",
                },
            }
        }

        headers = self.default_headers
        headers["x-fantasy-filter"] = json.dumps(xff)
        return self.get_json(self.api_url, headers=headers, params=self.default_params)

    def weekly_projections_by_team(self, week, team_id, limit=50, offset=0):
        """Gets player projections by team

        Args:
            week (int): e.g. 1-17
            team_id (int): e.g. 1-32

        Returns:
            dict
        """
        # x_fantasy_filter is where most of the API action is
        # will stringify when create headers dict
        # simplest to get projections by team, because don't need to
        # make more than 1 request per team (50 records max)
        x_fantasy_filter = self.default_x_fantasy_filter.copy()
        x_fantasy_filter["filterProTeamIds"] = {"value": [team_id]}
        x_fantasy_filter["filterRanksForScoringPeriodIds"] = {"value": [week]}
        headers = self.default_headers.copy()
        headers["x_fantasy_filter"] = json.dumps(x_fantasy_filter)
        return self.get_json(self.api_url, headers=headers, payload=self.default_params)


class Parser:
    """
    Parse ESPN API for football stats

    """

    POSITION_MAP = {
        0: "QB",
        1: "TQB",
        2: "RB",
        3: "RB/WR",
        4: "WR",
        5: "WR/TE",
        6: "TE",
        7: "OP",
        8: "DT",
        9: "DE",
        10: "LB",
        11: "DL",
        12: "CB",
        13: "S",
        14: "DB",
        15: "DP",
        16: "D/ST",
        17: "K",
        18: "P",
        19: "HC",
        20: "BE",
        21: "IR",
        22: "",
        23: "RB/WR/TE",
        24: "ER",
        25: "Rookie",
        "QB": 0,
        "RB": 2,
        "WR": 4,
        "TE": 6,
        "D/ST": 16,
        "K": 17,
        "FLEX": 23,
    }

    STAT_MAP = {
        "0": "pass_att",
        "1": "pass_cmp",
        "3": "pass_yds",
        "4": "pass_td",
        "19": "pass_tpc",
        "20": "pass_int",
        "23": "rush_att",
        "24": "rush_yds",
        "25": "rush_td",
        "26": "rush_tpc",
        "53": "rec_rec",
        "42": "rec_yds",
        "43": "rec_td",
        "44": "rec_tpc",
        "58": "rec_tar",
        "72": "fum_lost",
        "74": "madeFieldGoalsFrom50Plus",
        "77": "madeFieldGoalsFrom40To49",
        "80": "madeFieldGoalsFromUnder40",
        "85": "missedFieldGoals",
        "86": "madeExtraPoints",
        "88": "missedExtraPoints",
        "89": "defensive0PointsAllowed",
        "90": "defensive1To6PointsAllowed",
        "91": "defensive7To13PointsAllowed",
        "92": "defensive14To17PointsAllowed",
        "93": "defensiveBlockedKickForTouchdowns",
        "95": "defensiveInterceptions",
        "96": "defensiveFumbles",
        "97": "defensiveBlockedKicks",
        "98": "defensiveSafeties",
        "99": "defensiveSacks",
        "101": "kickoffReturnTouchdown",
        "102": "puntReturnTouchdown",
        "103": "fumbleReturnTouchdown",
        "104": "interceptionReturnTouchdown",
        "123": "defensive28To34PointsAllowed",
        "124": "defensive35To45PointsAllowed",
        "129": "defensive100To199YardsAllowed",
        "130": "defensive200To299YardsAllowed",
        "132": "defensive350To399YardsAllowed",
        "133": "defensive400To449YardsAllowed",
        "134": "defensive450To499YardsAllowed",
        "135": "defensive500To549YardsAllowed",
        "136": "defensiveOver550YardsAllowed",
    }

    TEAM_MAP = {
        "ARI": 22,
        "ATL": 1,
        "BAL": 33,
        "BUF": 2,
        "CAR": 29,
        "CHI": 3,
        "CIN": 4,
        "CLE": 5,
        "DAL": 6,
        "DEN": 7,
        "DET": 8,
        "GB": 9,
        "HOU": 34,
        "IND": 11,
        "JAC": 30,
        "JAX": 30,
        "KC": 12,
        "LAC": 24,
        "LA": 14,
        "LAR": 14,
        "MIA": 15,
        "MIN": 16,
        "NE": 17,
        "NO": 18,
        "NYG": 19,
        "NYJ": 20,
        "OAK": 13,
        "PHI": 21,
        "PIT": 23,
        "SEA": 26,
        "SF": 25,
        "TB": 27,
        "TEN": 10,
        "WAS": 28,
        "WSH": 28,
        "FA": 0,
    }

    def __init__(self, season):
        """
            """
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        self.season = season

    def _parse_stats(self, stat):
        """Parses stats dict"""
        return {
            self.STAT_IDS.get(str(k)): float(v)
            for k, v in stat.items()
            if str(k) in self.STAT_IDS
        }

    def _find_projection(self, stats, week=None):
        """Simplified way to find projection or result"""
        mapping = {
            "seasonId": self.season,
            "scoringPeriodId": 0 if not week else week,
            "statSourceId": 1 if not week else 0,
            "statSplitTypeId": 0 if not week else 1,
        }

        for item in stats:
            if {k: item[k] for k in mapping} == mapping:
                return item

    def _find_season_projection(self, stats):
        """Takes statslist and gets season projection"""
        currproj = [
            item
            for item in stats
            if item["seasonId"] == self.season
            and item["scoringPeriodId"] == 0
            and item["statSourceId"] == 1
            and item["statSplitTypeId"] == 0
        ]
        try:
            return currproj[0]
        except IndexError:
            logging.error("no matching week")
            return None

    def _find_weekly_projection(self, stats, week):
        """Takes statslist and gets weekly projection"""
        currproj = [
            item
            for item in stats
            if item["seasonId"] == self.season
            and item["scoringPeriodId"] == week
            and item["statSourceId"] == 0
            and item["statSplitTypeId"] == 1
        ]
        try:
            return currproj[0]
        except IndexError:
            logging.error("no matching week")
            return None

    def espn_team(self, team_code=None, team_id=None):
        """Returns team_id given code or team_code given team_id"""
        if team_code:
            tid = self.TEAM_MAP.get(team_code)
            return tid if tid else self.TEAM_MAP.get(get_team_code(team_code))
        elif team_id:
            return {v: k for k, v in self.TEAM_MAP.items()}.get(int(team_id))

    def season_projections(self, content):
        """Parses the seasonal projections
        
        Args:
            content(dict): parsed JSON
            week(int): 1-17

        Returns:
            list: of dict
        """
        proj = []

        top_level_keys = {
            "id": "source_player_id",
            "fullName": "source_player_name",
            "proTeamId": "source_team_id",
        }

        for player in [item["player"] for item in content["players"]]:
            p = {
                top_level_keys.get(k): v
                for k, v in player.items()
                if k in top_level_keys
            }

            p["source_team_code"] = self.espn_team(team_id=p.get("source_team_id", 0))

            # loop through player stats to find weekly projections
            stat = self._find_season_projection(player["stats"])
            if stat:
                p["source_player_projection"] = stat["appliedTotal"]
                proj.append(dict(**p, **self._parse_stats(stat["stats"])))
            else:
                p["source_player_projection"] = None
                proj.append(p)
        return proj

    def weekly_projections(self, content, week):
        """Parses the weekly projections

        Args:
            content(dict): parsed JSON
            week(int): 1-17

        Returns:
            list: of dict
        """
        proj = []

        top_level_keys = {
            "id": "source_player_id",
            "fullName": "source_player_name",
            "proTeamId": "source_team_id",
        }

        for player in [item["player"] for item in content["players"]]:
            p = {
                top_level_keys.get(k): v
                for k, v in player.items()
                if k in top_level_keys
            }

            p["source_team_code"] = self.espn_team(team_id=p.get("source_team_id", 0))

            # loop through player stats to find weekly projections
            stat = self._find_weekly_projection(player["stats"], week)
            if stat:
                p["source_player_projection"] = stat["appliedTotal"]
                proj.append(dict(**p, **self._parse_stats(stat["stats"])))
            else:
                p["source_player_projection"] = None
                proj.append(p)
        return proj


class Agent:
    """
    Combines common scraping/parsing tasks

    """

    def __init__(self, scraper=None, parser=None, season=None, cache_name="espn-agent"):
        """
        Creates Agent object

        Args:
            scraper (espn.Scraper): default None
            parser (espn.Parser): default None
            season (int): default None
            cache_name(str): default 'espn-agent'

        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        if not parser and not scraper and not season:
            raise ValueError("Must provide season if no scraper and parser")
        if scraper:
            self._s = scraper
        else:
            self._s = Scraper(season=season, cache_name=cache_name)
        if parser:
            self._p = parser
        else:
            self._p = Parser(season=season)

    def weekly_projections_by_team(self, week):
        """Gets weekly projections for all teams

        Args:
            week(int): 1-17

        Returns:
            list: of dict
        """
        projections = []
        for team_code, team_id in TEAM_MAP.items():
            logging.info("starting projections for %s", team_code)
            content = self._s.weekly_projections_by_team(week=week, team_id=team_id)
            projections += self._p.weekly_projections_by_team(content, week)
            time.sleep(1)
        return projections


# %%
a = Agent(season=2020, cache_name="week3")

# %%
logging.basicConfig(level=logging.INFO)

# %%
proj = a.weekly_projections_by_team(week=3)

# %%
import pandas as pd

df = pd.DataFrame(proj)
df.head()

# %%
if __name__ == "__main__":
    pass

