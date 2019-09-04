"""

# espn_api.py
# classes for scraping, parsing espn football api
# this does include some basic fantasy data
# espn_fantasy is mostly about managing fantasy teams

Usage:

    import pprint
    from nfl.espn_api import Scraper, Parser

    s = Scraper()
    p = Parser()
    team_code = 'BAL'
    content = s.projections(team_code=team_code)
    pprint.pprint(p.projections(content))

    season = 2019
    week = 1
    team_code = 'BAL'
    content = s.weekly_projections(week=week, team_code=team_code)
    pprint.pprint(p.weekly_projections(content, season, week))

"""

import json
import logging

from sportscraper.scraper import RequestScraper


ESPN_TEAMS = [
 {'source_team_city': 'Indianapolis',
  'source_team_code': 'Ind',
  'source_team_id': 11,
  'source_team_name': 'Colts'},
 {'source_team_city': 'Kansas City',
  'source_team_code': 'KC',
  'source_team_id': 12,
  'source_team_name': 'Chiefs'},
 {'source_team_city': 'Oakland',
  'source_team_code': 'Oak',
  'source_team_id': 13,
  'source_team_name': 'Raiders'},
 {'source_team_city': 'Los Angeles',
  'source_team_code': 'LAR',
  'source_team_id': 14,
  'source_team_name': 'Rams'},
 {'source_team_city': 'Miami',
  'source_team_code': 'Mia',
  'source_team_id': 15,
  'source_team_name': 'Dolphins'},
 {'source_team_city': 'Minnesota',
  'source_team_code': 'Min',
  'source_team_id': 16,
  'source_team_name': 'Vikings'},
 {'source_team_city': 'New England',
  'source_team_code': 'NE',
  'source_team_id': 17,
  'source_team_name': 'Patriots'},
 {'source_team_city': 'New Orleans',
  'source_team_code': 'NO',
  'source_team_id': 18,
  'source_team_name': 'Saints'},
 {'source_team_city': 'New York',
  'source_team_code': 'NYG',
  'source_team_id': 19,
  'source_team_name': 'Giants'},
 {'source_team_city': 'New York',
  'source_team_code': 'NYJ',
  'source_team_id': 20,
  'source_team_name': 'Jets'},
 {'source_team_city': 'Philadelphia',
  'source_team_code': 'Phi',
  'source_team_id': 21,
  'source_team_name': 'Eagles'},
 {'source_team_city': 'Arizona',
  'source_team_code': 'Ari',
  'source_team_id': 22,
  'source_team_name': 'Cardinals'},
 {'source_team_city': 'Pittsburgh',
  'source_team_code': 'Pit',
  'source_team_id': 23,
  'source_team_name': 'Steelers'},
 {'source_team_city': 'Los Angeles',
  'source_team_code': 'LAC',
  'source_team_id': 24,
  'source_team_name': 'Chargers'},
 {'source_team_city': 'San Francisco',
  'source_team_code': 'SF',
  'source_team_id': 25,
  'source_team_name': '49ers'},
 {'source_team_city': 'Seattle',
  'source_team_code': 'Sea',
  'source_team_id': 26,
  'source_team_name': 'Seahawks'},
 {'source_team_city': 'Tampa Bay',
  'source_team_code': 'TB',
  'source_team_id': 27,
  'source_team_name': 'Buccaneers'},
 {'source_team_city': 'Washington',
  'source_team_code': 'Wsh',
  'source_team_id': 28,
  'source_team_name': 'Redskins'},
 {'source_team_city': 'Carolina',
  'source_team_code': 'Car',
  'source_team_id': 29,
  'source_team_name': 'Panthers'},
 {'source_team_city': 'Jacksonville',
  'source_team_code': 'Jax',
  'source_team_id': 30,
  'source_team_name': 'Jaguars'},
 {'source_team_city': 'Baltimore',
  'source_team_code': 'Bal',
  'source_team_id': 33,
  'source_team_name': 'Ravens'},
 {'source_team_city': 'Houston',
  'source_team_code': 'Hou',
  'source_team_id': 34,
  'source_team_name': 'Texans'},
 {'source_team_city': '',
  'source_team_code': 'FA',
  'source_team_id': 0,
  'source_team_name': 'FA'},
 {'source_team_city': 'Atlanta',
  'source_team_code': 'Atl',
  'source_team_id': 1,
  'source_team_name': 'Falcons'},
 {'source_team_city': 'Buffalo',
  'source_team_code': 'Buf',
  'source_team_id': 2,
  'source_team_name': 'Bills'},
 {'source_team_city': 'Chicago',
  'source_team_code': 'Chi',
  'source_team_id': 3,
  'source_team_name': 'Bears'},
 {'source_team_city': 'Cincinnati',
  'source_team_code': 'Cin',
  'source_team_id': 4,
  'source_team_name': 'Bengals'},
 {'source_team_city': 'Cleveland',
  'source_team_code': 'Cle',
  'source_team_id': 5,
  'source_team_name': 'Browns'},
 {'source_team_city': 'Dallas',
  'source_team_code': 'Dal',
  'source_team_id': 6,
  'source_team_name': 'Cowboys'},
 {'source_team_city': 'Denver',
  'source_team_code': 'Den',
  'source_team_id': 7,
  'source_team_name': 'Broncos'},
 {'source_team_city': 'Detroit',
  'source_team_code': 'Det',
  'source_team_id': 8,
  'source_team_name': 'Lions'},
 {'source_team_city': 'Green Bay',
  'source_team_code': 'GB',
  'source_team_id': 9,
  'source_team_name': 'Packers'},
 {'source_team_city': 'Tennessee',
  'source_team_code': 'Ten',
  'source_team_id': 10,
  'source_team_name': 'Titans'}
]

ID_TEAM_DICT = {
    22: "ARI",
    1: "ATL",
    33: "BAL",
    2: "BUF",
    29: "CAR",
    3: "CHI",
    4: "CIN",
    5: "CLE",
    6: "DAL",
    7: "DEN",
    8: "DET",
    9: "GB",
    34: "HOU",
    11: "IND",
    30: "JAX",
    12: "KC",
    24: "LAC",
    14: "LA",
    15: "MIA",
    16: "MIN",
    17: "NE",
    18: "NO",
    19: "NYG",
    20: "NYJ",
    13: "OAK",
    21: "PHI",
    23: "PIT",
    26: "SEA",
    25: "SF",
    27: "TB",
    10: "TEN",
    28: "WAS",
    0: "FA",
}

TEAM_ID_DICT = {
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

STAT_IDS = {
    "0": "pass_att",
    "1": "pass_cmp",
    "3": "pass_yds",
    "4": "pass_td",
    "20": "pass_int",
    "23": "rush_att",
    "24": "rush_yds",
    "25": "rush_td",
    "53": "rec_rec",
    "42": "rec_yds",
    "43": "rec_td",
    "58": "rec_tar",
}


class Scraper(RequestScraper):
    """
    Scrape ESPN API for football stats

    """

    def projections(
        self,
        position="ALL",
        team_id=-1,
        team_code=None,
        limit=50,
        offset=0
    ):
        """
        Gets player projections by position or team

        Args:
            position(str): default 'ALL'
            team_id(int): default -1
            team_code(str): default None
            limit(int): default 50
            offset(int): default 0

        Returns:
            dict

        """
        if position == "ALL":
            filter_slot_ids = [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                23,
                24,
            ]
        elif position in ["QB", "qb"]:
            filter_slot_ids = [0]
        elif position in ["RB", "rb"]:
            filter_slot_ids = [2]
        elif position in ["WR", "wr"]:
            filter_slot_ids = [4]
        elif position in ["TE", "te"]:
            filter_slot_ids = [6]
        elif position in ["FLEX", "flex"]:
            filter_slot_ids = [23]
        elif position in ["DST", "D/ST", "D", "Defense", "DEF"]:
            filter_slot_ids = [16]
        elif position in ["K", "k", "Kicker"]:
            filter_slot_ids = [17]
        else:
            filter_slot_ids = [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                23,
                24,
            ]

        url = "http://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/segments/0/leaguedefaults/1"
 
        # x_fantasy_filter is where most of the API action is
        # will stringify when create headers dict
        # simplest to get projections by team, because don't need to
        #   make more than 1 request (50 records max)
        x_fantasy_filter = {
            "players": {
                "filterSlotIds": {"value": filter_slot_ids},
                "filterStatsForSplitTypeIds": {"value": [0]},
                "filterStatsForSourceIds": {"value": [1]},
                "filterStatsForExternalIds": {"value": [2019]},
                "sortDraftRanks": {"sortPriority": 2, "sortAsc": True, "value": "PPR"},
                "sortPercOwned": {"sortPriority": 3, "sortAsc": False},
                "limit": limit,
                "offset": offset,
                "filterStatsForTopScoringPeriodIds": {
                    "value": 2,
                    "additionalValue": ["002019", "102019", "002018"],
                },
            }
        }

        # add team filter (if applicable)
        if team_id >= 0:
            x_fantasy_filter["players"]["filterProTeamIds"] = {"value": [team_id]}
        elif team_code:
            x_fantasy_filter["players"]["filterProTeamIds"] = {
                "value": [TEAM_ID_DICT.get(team_code, "")]
            }

        headers = {
            "X-Fantasy-Filter": json.dumps(x_fantasy_filter),
            "X-Fantasy-Source": "kona",
            "Accept": "application/json",
            "Referer": "http://fantasy.espn.com/football/players/projections",
            "DNT": "1",
            "Connection": "keep-alive",
            "X-Fantasy-Platform": "kona-PROD-669a217c5628b670cf386bd4cebe972bf88022eb",
        }
        return self.get_json(url, headers=headers, params={"view": "kona_player_info"})

    def teams(self):
        """

        Returns:
            dict

        """
        url = 'http://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/'
        headers = {
            'Accept': 'application/json',
            'Referer': 'http://fantasy.espn.com/football/players/projections',
            'X-Fantasy-Source': 'kona',
            'DNT': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36',
            'X-Fantasy-Platform': 'kona-PROD-669a217c5628b670cf386bd4cebe972bf88022eb',
        }
        return self.get_json(url, headers=headers, params={'view': 'proTeamSchedules'})

    def weekly_projections(
        self,
        week,
        league_id=302946,
        team_id=-1,
        team_code=None,
        limit=50,
        offset=0
    ):
        """
        Gets player projections by position or team

        Args:
            week(int):
            league_id(int):
            team_id(int): default -1
            team_code(str): default None

        Returns:
            dict

        """
        url = f'https://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/segments/0/leagues/{league_id}'
        filter_slot_ids = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                           14, 15, 16, 17, 18, 19, 23, 24]

        # x_fantasy_filter is where most of the API action is
        # will stringify when create headers dict
        # simplest to get projections by team, because don't need to
        #   make more than 1 request (50 records max)
        x_fantasy_filter = {
            "players": {
                "filterSlotIds": {"value": filter_slot_ids},
                'filterRanksForMostRelevant': {'value': True},
                "sortDraftRanks": {"sortPriority": 100, "sortAsc": True, "value": "STANDARD"},
                "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
                "limit": limit,
                "offset": offset,
                "filterStatsForTopScoringPeriodIds": {
                    "value": 2,
                    "additionalValue": ["002019", "102019", "002018", "1120191", "022019"],
                },
            }
        }

        # add team filter (if applicable)
        if team_id >= 0:
            x_fantasy_filter["players"]["filterProTeamIds"] = {"value": [team_id]}
        elif team_code:
            x_fantasy_filter["players"]["filterProTeamIds"] = {
                "value": [TEAM_ID_DICT.get(team_code, "")]
            }

        headers = {
            "X-Fantasy-Filter": json.dumps(x_fantasy_filter),
            "X-Fantasy-Source": "kona",
            "Accept": "application/json",
            "DNT": "1",
            "Connection": "keep-alive",
            "X-Fantasy-Platform": "kona-PROD-669a217c5628b670cf386bd4cebe972bf88022eb",
            'sec-fetch-mode': 'cors',
            'x-fantasy-source': 'kona',
            'referer': f'https://fantasy.espn.com/football/players/add?leagueId={league_id}',
            'authority': 'fantasy.espn.com',
            'if-none-match': '"02e6d6b144815cc538384cd73c9de990a"',
            'sec-fetch-site': 'same-origin',
        }

        params = {'scoringPeriodId': week, 'view': 'kona_player_info'}
        return self.get_json(url, headers=headers, params=params)


class Parser:
    """
    Parse ESPN API for football stats

    """

    def __init__(self):
        """
        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    @staticmethod
    def _val(val):
        """
        Converts non-numeric value to numeric 0

        Args:
            val:

        Returns:
            number
        """
        if "--" in val:
            return 0
        return val

    @staticmethod
    def projections(content):
        """

        Args:
            content(dict): parsed JSON

        Returns:
            list: of dict

        """
        top_level_keys = {
            "id": "source_player_id",
            "fullName": "full_name",
            "proTeamId": "source_team_id",
        }
        proj = []
        for item in content["players"]:
            player = item["player"]
            p = {
                top_level_keys.get(k): v
                for k, v in player.items()
                if k in top_level_keys
            }
            # ESPN has entries for players with no projections
            # will throw IndexError in these instances, can safely ignore
            try:
                stats = player["stats"][0]["stats"]
                for stat_id, stat_name in STAT_IDS.items():
                    p[stat_name] = stats.get(stat_id, 0)
                p["source_team_code"] = ID_TEAM_DICT.get(
                    int(p.get("source_team_id", 0))
                )
                proj.append(p)
            except IndexError:
                pass
        return proj

    @staticmethod
    def teams(content):
        """

        Args:
            content(dict): parsed JSON

        Returns:
            list: of dict

        """
        top_level_keys = {
            "abbrev": "source_team_code",
            "location": "source_team_city",
            "id": "source_team_id",
            "name": "source_team_name"
        }
        return [{top_level_keys.get(k):v for k,v in team.items() if k in top_level_keys}
                  for team in content['settings']['proTeams']]


    @staticmethod
    def weekly_projections(content, season, week):
        """

        Args:
            content(dict): parsed JSON
            season(int): 2018, 2019, etc.
            week(int): 1-17

        Returns:
            list: of dict

        """
        top_level_keys = {
            "id": "source_player_id",
            "fullName": "full_name",
            "proTeamId": "source_team_id",
        }
        proj = []
        for item in content["players"]:
            player = item["player"]
            p = {
                top_level_keys.get(k): v
                for k, v in player.items()
                if k in top_level_keys
            }

            # loop through player stats to find weekly projections
            for stat in player['stats']:
                if stat.get('seasonId') == season and stat.get('scoringPeriodId') == week:
                    p['projection'] = stat.get('appliedTotal', 0)
            p["source_team_code"] = ID_TEAM_DICT.get(int(p.get("source_team_id", 0)))
            proj.append(p)
        return proj


if __name__ == "__main__":
    pass

