'''
pipelines/pfr.py
functions to transform pfr data for insertion into database, etc.
'''

import logging
import re

from nfl.dates import strtodate
from nfl.player.playerxref import *
from nfl.seasons import season_week


logging.getLogger(__name__).addHandler(logging.NullHandler())


def draft_table(players, pfrd, db):
    '''
    Prepares dict for insertion in draft table

    Args:
        players(list): of dict
        pfrd(dict): pfr_id: player_id
        db(NFLPostgres): instance

    Returns:
        list

    '''
    pconv = {
        'college_id': 'college',
        'source_player_id': 'pfr_player_id',
        'pos': 'pos'
    }

    dconv = {
        'draft_pick': 'draft_overall_pick',
        'draft_round': 'draft_round',
        'draft_year': 'draft_year',
        'player': 'source_player_name',
        'team': 'source_team_id',
        'pos': 'source_player_position',
        'source_player_id': 'source_player_id'
    }

    dtoins = []

    for p in players:
        logging.info('starting {}'.format(p.get('player')))
        pfr_id = p.get('source_player_id')
        player_id = pfrd.get(pfr_id)
        if not player_id:
            try:
                ln, fn = re.split(r',\s*', p.get('player'))[0:2]
                d = {pconv.get(k): v for k, v in p.items() if k in pconv}
                d['first_name'] = fn
                d['last_name'] = ln
                player_id = db._insert_dict(d, 'base.player')
            except:
                logging.exception('could not insert {}'.format(p))
        d2 = {dconv.get(k): v for k, v in p.items() if k in dconv}
        d2['source'] = 'pfr'
        d2['player_id'] = player_id
        dtoins.append(d2)

    return dtoins


def playerstats_fantasy_weekly_table(players):
    '''
    Prepares player dict for insertion into playerstats_fantasy_weekly table
    
    Args:
        players: list of dict

    Returns:
        list of dict
    '''
    convert = {
        'team': 'source_team_code',
        'year_id': 'season_year',
        'source': 'source',
        'source_player_id': 'source_player_id',
        'player': 'source_player_name',
        'source_team_code': 'source_team_code',
        'season_year': 'season_year',
        'week_num': 'week',
        'draftkings_points': 'draftkings_points',
        'fanduel_points': 'fanduel_points',
        'fantasy_points': 'fantasy_points_std'
    }

    fixed = []
    for p in players:
        player = {convert[k]: valornone(v) for k,v in p.items() if k in convert.keys()}
        player['source'] = 'pfr'
        fixed.append(player)

    return fixed


def playerstats_fantasy_yearly_table(players):
    '''
    Prepares player dict for insertion into playerstats_fantasy_yearly table

    Args:
        players: list of dict

    Returns:
        list of dict
    '''
    convert = {
        'team': 'source_team_code',
        'source': 'source',
        'fantasy_pos': 'source_player_position',
        'source_player_id': 'source_player_id',
        'source_player_name': 'source_player_name',
        'source_player_position': 'source_player_position',
        'source_team_code': 'source_team_code',
        'season_year': 'season_year',
        'draftkings_points': 'draftkings_points',
        'fanduel_points': 'fanduel_points',
        'fantasy_points': 'fantasy_points_std',
        'g': 'g',
        'gs': 'gs'
    }
    fixed = []
    for p in players:
        player = {convert[k]: valornone(v) for k, v in p.items() if k in convert.keys()}
        player['source'] = 'pfr'
        fixed.append(player)
    return fixed


def playerstats_offense_weekly_table(players):
    '''
    Converts offense playerstats for single week

    Args:
        players: 

    Returns:
        list of dict
    '''
    convert = {
        'team': 'source_team_code',
        'pass_att': 'pass_att',
        'pass_cmp': 'pass_cmp',
        'pass_int': 'pass_int',
        'pass_sacked': 'pass_sacked',
        'pass_sacked_yds': 'pass_sacked_yds',
        'pass_td': 'pass_td',
        'pass_yds': 'pass_yds',
        'player': 'source_player_name',
        'rec': 'rec',
        'rec_yds': 'rec_yds',
        'rec_td': 'rec_td',
        'rush_att': 'rush_att',
        'rush_td': 'rush_td',
        'rush_yds': 'rush_yds',
        'week_num': 'week',
        'season_year': 'season_year',
        'year_id': 'season_year',
        'source_player_id': 'source_player_id',
    }

    fixed = []
    for player in players:
        p = {convert[k]: valornone(v) for k, v in player.items() if k in convert.keys()}
        p['source'] = 'pfr'
        fixed.append(p)

    return fixed

def playerstats_offense_yearly_table(players):
    '''
    Converts offense playerstats for single season

    Args:
        players: 

    Returns:
        list of dict
    '''
    convert = {
        'team': 'source_team_code',
        'pass_att': 'pass_att',
        'pass_cmp': 'pass_cmp',
        'pass_int': 'pass_int',
        'pass_sacked': 'pass_sacked',
        'pass_sacked_yds': 'pass_sacked_yds',
        'pass_td': 'pass_td',
        'pass_yds': 'pass_yds',
        'player': 'source_player_name',
        'source_player_name': 'source_player_name',
        'rec': 'rec',
        'targets': 'rec_target',
        'rec_yds': 'rec_yds',
        'rec_td': 'rec_td',
        'rush_att': 'rush_att',
        'rush_td': 'rush_td',
        'rush_yds': 'rush_yds',
        'season_year': 'season_year',
        'year_id': 'season_year',
        'source_player_id': 'source_player_id',
        'g': 'g'
    }

    fixed = []
    for player in players:
        p = {convert[k]: valornone(v) for k, v in player.items() if k in convert.keys()}
        p['source'] = 'pfr'
        fixed.append(p)
    return fixed


def teamstats_defense_weekly_table(teams):
    '''

    Args:
        teams: 

    Returns:

    '''
    convert = {
        'team': 'source_team_code',
        'plays_defense': 'plays_defense',
        'pass_att_opp': 'pass_att_opp',
        'pass_cmp_opp': 'pass_cmp_opp',
        'pass_int_opp': 'pass_int_opp',
        'pass_sacked_opp': 'pass_sacked_opp',
        'pass_sacked_yds_opp': 'pass_sacked_yds_opp',
        'pass_td_opp': 'pass_td_opp',
        'pass_yds_opp': 'pass_yds_opp',
        'rush_att_opp': 'rush_att_opp',
        'rush_td_opp': 'rush_td_opp',
        'rush_yds_opp': 'rush_yds_opp',
        'week_num': 'week',
        'year_id': 'season_year'
    }

    fixed = []
    for t in teams:
        team = {convert[k]: valornone(v) for k,v in t.items() if k in convert.keys()}
        team['source'] = 'pfr'
        fixed.append(team)

    return fixed

def teamstats_defense_yearly_table(teams):
    '''

    Args:
        teams: 

    Returns:

    '''
    convert = {
        'team': 'source_team_code',
        'source': 'source',
        'source_team_code': 'source_team_code',
        'plays_offense': 'plays_defense',
        'pass_cmp': 'pass_cmp_opp',
        'pass_att': 'pass_att_opp',
        'pass_yds': 'pass_yds_opp',
        'pass_int': 'pass_int_opp',
        'pass_td': 'pass_td_opp',
        'pass_sacked': 'pass_sacked_opp',
        'pass_sacked_yds': 'pass_sacked_yds_opp',
        'rush_att': 'rush_att_opp',
        'rush_yds': 'rush_yds_opp',
        'rush_td': 'rush_td_opp',
        'season_year': 'season_year',
        'year_id': 'season_year'
    }

    fixed = []
    for t in teams:
        team = {convert[k]: valornone(v) for k,v in t.items() if k in convert.keys()}
        team['source'] = 'pfr'
        fixed.append(team)

    return fixed

def teamstats_offense_weekly_table(teams):
    '''
    
    Args:
        teams: 

    Returns:

    '''
    convert = {
       'team': 'source_team_code',
       'pass_att': 'pass_att',
       'pass_cmp': 'pass_cmp',
       'pass_int': 'pass_int',
       'pass_sacked': 'pass_sacked',
       'pass_sacked_yds': 'pass_sacked_yds',
       'pass_td': 'pass_td',
       'pass_yds': 'pass_yds',
       'rush_att': 'rush_att',
       'rush_td': 'rush_td',
       'rush_yds': 'rush_yds',
       'week_num': 'week',
       'year_id': 'season_year'
    }

    fixed = []
    for t in teams:
        team = {convert[k]: valornone(v) for k,v in t.items() if k in convert.keys()}
        team['source'] = 'pfr'
        fixed.append(team)

    return fixed

def valornone(val):
    if val == '':
        return None
    else:
        return val


def team_fantasy_week_pipeline(players, year=None, week=None):
    '''

    '''
    db = getdb()
    q = """SELECT * FROM extra_misc.player_xref WHERE source='pfr'"""
    posd = {p['source_player_id']: p['source_player_position']
            for p in db.select_dict(q)}
    results = []
    tofix = []

    while (type(players[0]) == list):
        players = flatten_list(players)

    for p in players:
        if not year:
            year = season_week(strtodate(p['game_date']))['season']
        if not week:
            week = p['week_num']
        pos = posd.get(p['source_player_id'])
        d = {'source': 'pfr',
             'source_player_id': p['source_player_id'],
             'source_player_name': p['player'],
             'source_player_position': pos,
             'source_team_id': p['team'],
             'week': week,
             'season_year': year,
             'fantasy_points_std': p['fantasy_points'],
             'fantasy_points_ppr': p['fantasy_points_ppr'],
             'draftkings_points': p['draftkings_points'],
             'fanduel_points': p['fanduel_points']}
        d = {k: val_or_none(v) for k, v in d.items()}
        if pos:
            results.append(d)
        else:
            tofix.append(d)
    return results, tofix


if __name__ == '__main__':
    pass