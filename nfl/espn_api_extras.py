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
