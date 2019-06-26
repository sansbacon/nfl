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

"""

import json
import logging

from sportscraper.scraper import RequestScraper

ID_TEAM_DICT = {
 22: 'ARI',
 1: 'ATL',
 33: 'BAL',
 2: 'BUF',
 29: 'CAR',
 3: 'CHI',
 4: 'CIN',
 5: 'CLE',
 6: 'DAL',
 7: 'DEN',
 8: 'DET',
 9: 'GB',
 34: 'HOU',
 11: 'IND',
 30: 'JAX',
 12: 'KC',
 24: 'LAC',
 14: 'LA',
 15: 'MIA',
 16: 'MIN',
 17: 'NE',
 18: 'NO',
 19: 'NYG',
 20: 'NYJ',
 13: 'OAK',
 21: 'PHI',
 23: 'PIT',
 26: 'SEA',
 25: 'SF',
 27: 'TB',
 10: 'TEN',
 28: 'WAS',
 0: 'FA'
}

TEAM_ID_DICT = {
 'ARI': 22,
 'ATL': 1,
 'BAL': 33,
 'BUF': 2,
 'CAR': 29,
 'CHI': 3,
 'CIN': 4,
 'CLE': 5,
 'DAL': 6,
 'DEN': 7,
 'DET': 8,
 'GB': 9,
 'HOU': 34,
 'IND': 11,
 'JAC': 30,
 'JAX': 30,
 'KC': 12,
 'LAC': 24,
 'LA': 14,
 'LAR': 14,
 'MIA': 15,
 'MIN': 16,
 'NE': 17,
 'NO': 18,
 'NYG': 19,
 'NYJ': 20,
 'OAK': 13,
 'PHI': 21,
 'PIT': 23,
 'SEA': 26,
 'SF': 25,
 'TB': 27,
 'TEN': 10,
 'WAS': 28,
 'WSH': 28,
 'FA': 0
}


STAT_IDS = {
    '0': 'pass_att',
    '1': 'pass_cmp',
    '3': 'pass_yds',
    '4': 'pass_td',
    '20': 'pass_int',
    '23': 'rush_att',
    '24': 'rush_yds',
    '25': 'rush_td',
    '53': 'rec_rec',
    '42': 'rec_yds',
    '43': 'rec_td',
    '58': 'rec_tar'
}


class Scraper(RequestScraper):
    """
    Scrape ESPN API for football stats

    """

    def projections(self,
                    position='ALL',
                    team_id=-1,
                    team_code=None,
                    limit=50,
                    offset=0):
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
        if position == 'ALL':
            filter_slot_ids = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,23,24]
        elif position in ['QB', 'qb']:
            filter_slot_ids = [0]
        elif position in ['RB', 'rb']:
            filter_slot_ids = [2]
        elif position in ['WR', 'wr']:
            filter_slot_ids = [4]
        elif position in ['TE', 'te']:
            filter_slot_ids = [6]
        elif position in ['FLEX', 'flex']:
            filter_slot_ids = [23]
        elif position in ['DST', 'D/ST', 'D', 'Defense', 'DEF']:
            filter_slot_ids = [16]
        elif position in ['K', 'k', 'Kicker']:
            filter_slot_ids = [17]
        else:
            filter_slot_ids = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 23, 24]

        url = 'http://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/segments/0/leaguedefaults/1'
        x_fantasy_filter = {"players":{
                              "filterSlotIds":{"value":filter_slot_ids},
                              "filterStatsForSplitTypeIds":{"value":[0]},
                              "filterStatsForSourceIds":{"value":[1]},
                              "filterStatsForExternalIds":{"value":[2019]},
                              "sortDraftRanks":{"sortPriority":2, "sortAsc":True,"value":"PPR"},
                              "sortPercOwned":{"sortPriority":3,"sortAsc":False},
                              "limit":limit,"offset":offset,
                              "filterStatsForTopScoringPeriodIds":{"value":2,"additionalValue":["002019","102019","002018"]}
                            }
                           }

        # add team filter (if applicable)
        if team_id >= 0:
            x_fantasy_filter["players"]["filterProTeamIds"] = {"value": [team_id]}
        elif team_code:
            x_fantasy_filter["players"]["filterProTeamIds"] = {"value": [TEAM_ID_DICT.get(team_code, '')]}

        # construct request
        headers = {
            'X-Fantasy-Filter': json.dumps(x_fantasy_filter),
            'X-Fantasy-Source': 'kona',
            'Accept': 'application/json',
            'Referer': 'http://fantasy.espn.com/football/players/projections',
            'DNT': '1',
            'Connection': 'keep-alive',
            'X-Fantasy-Platform': 'kona-PROD-669a217c5628b670cf386bd4cebe972bf88022eb',
        }
        logging.debug(headers)
        return self.get_json(url, headers=headers, params={'view': 'kona_player_info'})


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
        top_level_keys = {'id': 'source_player_id',
                          'fullName': 'full_name',
                          'proTeamId': 'source_team_id'}
        proj = []
        for item in content['players']:
            player = item['player']
            p = {top_level_keys.get(k):v for k,v in player.items() if k in top_level_keys}
            # ESPN has entries for players with no projections
            # will throw IndexError in these instances, can safely ignore
            try:
                stats = player['stats'][0]['stats']
                for stat_id, stat_name in STAT_IDS.items():
                    p[stat_name] = stats.get(stat_id)
                p['source_team_code'] = ID_TEAM_DICT.get(int(p.get('source_team_id', 0)))
                proj.append(p)
            except IndexError:
                pass
        return proj


if __name__ == "__main__":
    pass