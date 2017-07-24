# pipelines.py
# functions to transform nflcom data
# for insertion into database, use in optimizer, etc.

from __future__ import print_function
from copy import deepcopy
import logging

from nfl.teams import nickname_to_code


logging.getLogger(__name__).addHandler(logging.NullHandler())


def gamesmeta_table(games):
    '''
    Converts data from NFL.com week_page for insertion into gamesmeta table

    Arguments:
        games: list of dict

    Returns:
        list of dict
    '''
    fixed = []
    for g in games:
        # {'week': '1', 'gsis_id': '2008090711', 'away': 'cardinals', 'season_year': '2008', 'home': '49ers', 'matchup': 'cardinals@49ers'}
        # start with home team
        f = {}
        f['gsis_id'] = g['gsis_id']
        f['season_year'] = int(g['season_year'])
        f['week'] = int(g['week'])
        f['game_date'] = g['game_date']
        f['team_code'] = nickname_to_code(g['home'], f['season_year'])
        f['opp'] = nickname_to_code(g['away'], f['season_year'])
        f['is_home'] = True
        fixed.append(f)

        # make some changes for away team
        f2 = deepcopy(f)
        f2['is_home'] = False
        f2['team_code'] = f['opp']
        f2['opp'] = f['team_code']
        fixed.append(f2)

    return fixed


if __name__ == '__main__':
    pass