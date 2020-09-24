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
import time

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


class Agent:
    """
    Combines common scraping/parsing tasks

    """

    def __init__(self, scraper=None, parser=None, cache_name="espn-agent"):
        """
        Creates Agent object

        Args:
            scraper(espn.Scraper): default None
            parser(espn.Parser): default None
            cache_name(str): default 'espn-agent'

        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        if scraper:
            self._s = scraper
        else:
            self._s = Scraper(cache_name=cache_name)
        if parser:
            self._p = parser
        else:
            self._p = Parser()

    def weekly_projections(self, season_year, week):
        """

        Args:
            season_year(int): e.g. 2019
            week(int): 1-17

        Returns:
            list: of dict

        """
        projections = []
        logging.info('getting projections for %s Week %s', season_year, week)
        for team in TEAM_ID_DICT:
            logging.info('starting projections for %s', team)
            content = self._s.weekly_projections(week=week, team_code=team)
            projections.append(self._p.weekly_projections(content, season_year, week))
            time.sleep(2)
        return [item for sublist in projections
                for item in sublist]


"""


# espn_fantasy_scraper.py

#%%
import json
import requests

# %%
POSITION_MAP = {
    0: 'QB',
    1: 'TQB',
    2: 'RB',
    3: 'RB/WR',
    4: 'WR',
    5: 'WR/TE',
    6: 'TE',
    7: 'OP',
    8: 'DT',
    9: 'DE',
    10: 'LB',
    11: 'DL',
    12: 'CB',
    13: 'S',
    14: 'DB',
    15: 'DP',
    16: 'D/ST',
    17: 'K',
    18: 'P',
    19: 'HC',
    20: 'BE',
    21: 'IR',
    22: '',
    23: 'RB/WR/TE',
    24: 'ER',
    25: 'Rookie',
    'QB': 0,
    'RB': 2,
    'WR': 4,
    'TE': 6,
    'D/ST': 16,
    'K': 17,
    'FLEX': 23
}

PLAYER_STATS_MAP = {
    3: "passingYards",
    4: "passingTouchdowns",
    19: "passing2PtConversions",
    20: "passingInterceptions",
    23: "rushingAttempts",
    24: "rushingYards",
    25: "rushingTouchdowns",
    26: "rushing2PtConversions",
    42: "receivingYards",
    43: "receivingTouchdowns",
    44: "receiving2PtConversions",
    53: "receivingReceptions",
    58: "receivingTargets",
    72: "lostFumbles",
    74: "madeFieldGoalsFrom50Plus",
    77: "madeFieldGoalsFrom40To49",
    80: "madeFieldGoalsFromUnder40",
    85: "missedFieldGoals",
    86: "madeExtraPoints",
    88: "missedExtraPoints",
    89: "defensive0PointsAllowed",
    90: "defensive1To6PointsAllowed",
    91: "defensive7To13PointsAllowed",
    92: "defensive14To17PointsAllowed",
    93: "defensiveBlockedKickForTouchdowns",
    95: "defensiveInterceptions",
    96: "defensiveFumbles",
    97: "defensiveBlockedKicks",
    98: "defensiveSafeties",
    99: "defensiveSacks",
    101: "kickoffReturnTouchdown",
    102: "puntReturnTouchdown",
    103: "fumbleReturnTouchdown",
    104: "interceptionReturnTouchdown",
    123: "defensive28To34PointsAllowed",
    124: "defensive35To45PointsAllowed",
    129: "defensive100To199YardsAllowed",
    130: "defensive200To299YardsAllowed",
    132: "defensive350To399YardsAllowed",
    133: "defensive400To449YardsAllowed",
    134: "defensive450To499YardsAllowed",
    135: "defensive500To549YardsAllowed",
    136: "defensiveOver550YardsAllowed",
    140: "puntsInsideThe10", # PT10
    141: "puntsInsideThe20", # PT20
    148: "puntAverage44.0+", # PTA44
    149: "puntAverage42.0-43.9", #PTA42
    150: "puntAverage40.0-41.9", #PTA40
    161: "25+pointsWinMargin", #WM25
    162: "20-24pointWinMargin", #WM20
    163: "15-19pointWinMargin", #WM15
    164: "10-14pointWinMargin", #WM10
    165: "5-9pointWinMargin", # WM5
    166: "1-4pointWinMargin", # WM1
    155: "TeamWin", # TW
    171: "20-24pointLossMargin", # LM20
    172: "25+pointLossMargin", # LM25
}


BASE_X_FANTASY_FILTER =  {'players': 
  {
    'filterRanksForRankTypes': {'value': ['PPR']},
    'filterRanksForScoringPeriodIds': {'value': [3]},
    'filterRanksForSlotIds': {'value': [0, 2, 4, 6, 17, 16]},
    'filterSlotIds': {'value': [0]},
    'filterStatsForSourceIds': {'value': [1]},
    'filterStatsForSplitTypeIds': {'value': [1]},
    'filterStatsForTopScoringPeriodIds': {'value': 2, 'additionalValue': ['002020','102020','002019', '1120203', '022020']},
    'limit': 50,
    'offset': 0,
    'sortAppliedStatTotal': {'sortAsc': False,
    'sortPriority': 2,
    'value': '1120203'},
    'sortDraftRanks': {'sortAsc': True, 'sortPriority': 3, 'value': 'PPR'},
    'sortPercOwned': {'sortAsc': False, 'sortPriority': 4}
  }
}

# %%
# So change filterRanksForScoringPeriodIds
def x_fantasy_filter(week, pos, limit=50, offset=0):
    """Creates x-fantasy-filter header, which is akin to query string

    Args:
        week (int): e.g. 1
        pos (str): "QB", "WR", etc.
        limit (int): default 50
        offset (int): default 0, for paginated results
    Returns:
        dict
    """
    d = {'filterRanksForScoringPeriodIds': {'value': [week]},
        'filterSlotIds': {'value': [POSITION_MAP.get(pos)]},
        'limit': limit,
        'offset': offset}
    return dict(**BASE_X_FANTASY_FILTER, **d)


# %%
url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/2020/segments/0/leaguedefaults/3?view=kona_player_info'
week = 3
pos = "QB"
limit = 50
offset = 0

headers = {
    'authority': 'fantasy.espn.com',
    'accept': 'application/json',
    'x-fantasy-source': 'kona',
    'x-fantasy-filter': json.dumps(x_fantasy_filter(week, pos, limit, offset)),
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
    'x-fantasy-platform': 'kona-PROD-a9859dd5e813fa08e6946514bbb0c3f795a4ea23',
    'dnt': '1',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://fantasy.espn.com/football/players/projections',
    'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
    'if-none-match': 'W/"0ed6f681a29de93c9e006f93068af8ad6"',
}

params = (
    ('view', 'kona_player_info'),
)

r = requests.get(url, headers=headers, params=params)

# %%r = requests.get(url)
data = r.json()
# %%
players = data['players']
# %%
len(players)
# %%
player = players[0]['player']
#wanted = ['id', 'fullName', 'ownership_averageDraftPosition', 'ownership_auctionValueAverage']
topkeys = ['id', 'fullName']
subkeys = {'ownership': ['averageDraftPosition', 'auctionValueAverage'],
           'stats': ['appliedTotal', 'scoringPeriodId', 'id', 'external_id', 'seasonId'],
           "stats['stats']": {PLAYER_STATS_MAP(k): v for k, v in stats['stats'].items()}}


# %%
def process_player(player):
    """Turns nested player dict into flat dict"""
    p = {
      'source': 'espn_fantasy',
      'source_player_id': player['id'],
      'source_player_name': player['fullName']
    }

    # ownership subresource
    o = player['ownership']
    p['adp'] = o['averageDraftPosition']
    p['av'] = o['auctionValueAverage']

    # stats subresource
    s = player['stats'][0]
    p['proj'] = s['appliedTotal']
    p['week'] = s['scoringPeriodId']

    # stats sub-subresource
    for k, v in s['stats'].items():
        p[PLAYER_STATS_MAP.get(int(k))] = v

    return p
# %%
projs = [process_player(p['player']) for p in players]
# %%
projs[0]
# %%
players[0]
# %%

"""

"""
import requests

headers = {
    'authority': 'fantasy.espn.com',
    'accept': 'application/json',
    'x-fantasy-source': 'kona',
    'x-fantasy-filter': '{"players":{"filterStatsForExternalIds":{"value":[2020]},"filterSlotIds":{"value":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,23,24]},"filterStatsForSourceIds":{"value":[1]},"sortAppliedStatTotal":{"sortAsc":false,"sortPriority":2,"value":"102020"},"sortDraftRanks":{"sortPriority":3,"sortAsc":true,"value":"PPR"},"sortPercOwned":{"sortPriority":4,"sortAsc":false},"limit":50,"offset":0,"filterRanksForScoringPeriodIds":{"value":[1]},"filterRanksForRankTypes":{"value":["PPR"]},"filterStatsForTopScoringPeriodIds":{"value":2,"additionalValue":["002020","102020","002019","022020"]}}}',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    'x-fantasy-platform': 'kona-PROD-aa9589f081988f2d8ea670484512c40400965f3f',
    'dnt': '1',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://fantasy.espn.com/football/players/projections',
    'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
}

params = (
    ('view', 'kona_player_info'),
)

response = requests.get('https://fantasy.espn.com/apis/v3/games/ffl/seasons/2020/segments/0/leaguedefaults/3', headers=headers, params=params)

projections = response.json()['players']

# single player dict - Lamar Jackson
[p for p in projections if p['player']['fullName'] == 'Lamar Jackson'][0]
{'draftAuctionValue': 0,
 'id': 3916387,
 'keeperValue': 0,
 'keeperValueFuture': 0,
 'lineupLocked': False,
 'onTeamId': 0,
 'player': {'active': True,
            'defaultPositionId': 1,
            'draftRanksByRankType': {'PPR': {'auctionValue': 27,
                                             'published': False,
                                             'rank': 31,
                                             'rankSourceId': 0,
                                             'rankType': 'PPR',
                                             'slotId': 0},
                                     'STANDARD': {'auctionValue': 27,
                                                  'published': False,
                                                  'rank': 31,
                                                  'rankSourceId': 0,
                                                  'rankType': 'STANDARD',
                                                  'slotId': 0}},
            'droppable': True,
            'eligibleSlots': [0, 7, 20, 21],
            'firstName': 'Lamar',
            'fullName': 'Lamar Jackson',
            'id': 3916387,
            'injured': False,
            'injuryStatus': 'ACTIVE',
            'jersey': '8',
            'lastName': 'Jackson',
            'lastNewsDate': 1587576110000,
            'lastVideoDate': 1588863199000,
            'ownership': {'activityLevel': None,
                          'auctionValueAverage': 33.97047970479705,
                          'auctionValueAverageChange': 0.7189645532819,
                          'averageDraftPosition': 15.66908272931767,
                          'averageDraftPositionPercentChange': -0.03951665920244629,
                          'date': 1594299607419,
                          'leagueType': 0,
                          'percentChange': 0.013894294979692745,
                          'percentOwned': 99.8333267971293,
                          'percentStarted': 97.20577277540295},
            'proTeamId': 33,
            'rankings': {'1': [{'auctionValue': 0,
                                'published': False,
                                'rank': 1,
                                'rankSourceId': 6,
                                'rankType': 'PPR',
                                'slotId': 0}]},
            'seasonOutlook': 'The 2019 NFL MVP is fresh off a breakout season '
                             'in which he outscored the next-closest '
                             'quarterback by 78 fantasy points despite resting '
                             'in Week 17. The dual-threat weapon threw 36 '
                             'touchdowns to only six interceptions while '
                             'adding a record-setting 176-1,206-7 rushing line '
                             "-- that rushing production alone would've ranked "
                             '28th among running backs. The question is: Can '
                             'he do it again? History says no, as his 9.0% TD '
                             'rate (highest the NFL has seen over the past '
                             'decade) is unsustainable, and the last '
                             'quarterback to repeat as the top-scoring fantasy '
                             'QB was Daunte Culpepper in 2004. On the other '
                             "hand, Jackson's rushing volume and prowess give "
                             'him an extremely high floor, as shown by his 11 '
                             'top-six fantasy weeks in 15 outings last season. '
                             "Jackson's unique style makes him an elite "
                             'fantasy weapon and worth a look early in Round '
                             '3.',
            'stats': [{'appliedAverage': 22.548479216533334,
                       'appliedTotal': 338.227188248,
                       'externalId': '2020',
                       'id': '102020',
                       'proTeamId': 0,
                       'scoringPeriodId': 0,
                       'seasonId': 2020,
                       'statSourceId': 1,
                       'statSplitTypeId': 0,
                       'stats': {'0': 465.4031168,
                                 '1': 296.2309822,
                                 '10': 34.0,
                                 '11': 59.0,
                                 '12': 29.0,
                                 '15': 2.533153581,
                                 '16': 1.655415865,
                                 '17': 2.064622388,
                                 '18': 0.27887635,
                                 '19': 1.415918497,
                                 '2': 169.1721346,
                                 '20': 9.77814499,
                                 '21': 0.636504079,
                                 '210': 15.25,
                                 '22': 224.573392,
                                 '23': 155.6736176,
                                 '24': 902.3012034,
                                 '25': 5.959214533,
                                 '26': 0.189304559,
                                 '27': 180.0,
                                 '28': 90.0,
                                 '29': 45.0,
                                 '3': 3424.744227,
                                 '30': 36.0,
                                 '31': 18.0,
                                 '33': 31.0,
                                 '34': 15.0,
                                 '35': 0.311196102,
                                 '36': 0.217837271,
                                 '37': 2.227505185,
                                 '38': 0.076016206,
                                 '39': 5.796108664,
                                 '4': 25.47076617,
                                 '40': 59.16729203,
                                 '5': 684.0,
                                 '6': 342.0,
                                 '62': 1.605223057,
                                 '63': 0.049,
                                 '64': 34.61021859,
                                 '65': 8.487595581,
                                 '66': 2.642518939,
                                 '68': 11.13011452,
                                 '69': 4.074045879,
                                 '7': 171.0,
                                 '70': 1.215558712,
                                 '72': 5.289604591,
                                 '73': 15.06774958,
                                 '8': 136.0,
                                 '9': 68.0}}]},
 'ratings': {'0': {'positionalRanking': 1,
                   'totalRanking': 2,
                   'totalRating': 415.68}},
 'rosterLocked': False,
 'status': 'WAIVERS',
 'tradeLocked': False,
 'waiverProcessDate': 1594450800000}

# stat categories
stat_map = {
'0': 'pass_att',
'1': 'pass_cmp',
'3': 'pass_yds',
'4': 'pass_td',
'19': 'passing_tpc',
'20': 'pass_int',
'23': 'rush_att',
'24': 'rush_yds',
'25': 'rush_td',
'26': 'rush_tpc',
'42': 'rec_yds',
'43': 'rec_td',
'44': 'rec_tpc',
'53': 'rec_rec',
'58': 'rec_tgt',
'72': 'fumb',
'74': 'fgm_50+',
'77': 'fgm_40_49',
'80': 'fgm_1_39',
'85': 'fg_missed',
'86': 'fgm_xp',
'88': 'xp_missed',
'89': 'def_0_pts_allowed',
'90': 'def_1to6_pts_allowed',
'91': 'def_7to13_pts_allowed',
'92': 'def_14to17_pts_allowed',
'93': 'def_blk_kick_td',
'95': 'def_int',
'96': 'def_fumb_rec',
'97': 'def_blk_kick',
'98': 'def_safety',
'99': 'def_sack',
'101': 'def_kr_td',
'102': 'def_pr_td',
'103': 'def_fr_td',
'104': 'def_int_td',
'105': 'def_td',
'120': 'def_pts_allowed',
'123': 'def_28to34_pts_allowed',
'124': 'def_35to45_pts_allowed',
'127': 'def_yds_allowed'
'129': 'def_100to199_ya',
'130': 'def_200to299_ya',
'132': 'def_350to399_ya',
'133': 'def_400to449_ya',
'134': 'def_450to499_ya',
'135': 'def_500to549_ya',
'136': 'def_550+_ya',
}

 '10': 34.0,
 '11': 59.0,
 '12': 29.0,
 '15': 2.533153581,
 '16': 1.655415865,
 '17': 2.064622388,
 '18': 0.27887635,
 '19': 1.415918497,
 '2': 169.1721346,
 '20': 9.77814499,
 '21': 0.636504079,
 '210': 15.25,
 '22': 224.573392,
 '23': 155.6736176,
 '24': 902.3012034,
 '25': 5.959214533,
 '26': 0.189304559,
 '27': 180.0,
 '28': 90.0,
 '29': 45.0,
 '30': 36.0,
 '31': 18.0,
 '33': 31.0,
 '34': 15.0,
 '35': 0.311196102,
 '36': 0.217837271,
 '37': 2.227505185,
 '38': 0.076016206,
 '39': 5.796108664,
 '4': 25.47076617,
 '40': 59.16729203,
 '5': 684.0,
 '6': 342.0,
 '62': 1.605223057,
 '63': 0.049,
 '64': 34.61021859,
 '65': 8.487595581,
 '66': 2.642518939,
 '68': 11.13011452,
 '69': 4.074045879,
 '7': 171.0,
 '70': 1.215558712,
 '72': 5.289604591,
 '73': 15.06774958,
 '8': 136.0,
 '9': 68.0
}


POSITION_MAP = {
    0: 'QB',
    1: 'TQB',
    2: 'RB',
    3: 'RB/WR',
    4: 'WR',
    5: 'WR/TE',
    6: 'TE',
    7: 'OP',
    8: 'DT',
    9: 'DE',
    10: 'LB',
    11: 'DL',
    12: 'CB',
    13: 'S',
    14: 'DB',
    15: 'DP',
    16: 'D/ST',
    17: 'K',
    18: 'P',
    19: 'HC',
    20: 'BE',
    21: 'IR',
    22: '',
    23: 'RB/WR/TE',
    24: 'ER',
    25: 'Rookie',
    'QB': 0,
    'RB': 2,
    'WR': 4,
    'TE': 6,
    'D/ST': 16,
    'K': 17,
    'FLEX': 23
}

PRO_TEAM_MAP = {
    0 : 'None',
    1 : 'ATL',
    2 : 'BUF',
    3 : 'CHI',
    4 : 'CIN',
    5 : 'CLE',
    6 : 'DAL',
    7 : 'DEN',
    8 : 'DET',
    9 : 'GB',
    10: 'TEN',
    11: 'IND',
    12: 'KC',
    13: 'OAK',
    14: 'LAR',
    15: 'MIA',
    16: 'MIN',
    17: 'NE',
    18: 'NO',
    19: 'NYG',
    20: 'NYJ',
    21: 'PHI',
    22: 'ARI',
    23: 'PIT',
    24: 'LAC',
    25: 'SF',
    26: 'SEA',
    27: 'TB',
    28: 'WSH',
    29: 'CAR',
    30: 'JAX',
    33: 'BAL',
    34: 'HOU'
}

ACTIVITY_MAP = {
    178: 'FA ADDED',
    180: 'WAVIER ADDED',
    179: 'DROPPED',
    181: 'DROPPED',
    239: 'DROPPED',
    244: 'TRADED',
    'FA': 178,
    'WAVIER': 180,
    'TRADED': 244
}
"""

if __name__ == "__main__":
    pass

