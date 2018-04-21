'''
pipelines/pfr.py
functions to transform pfr data for insertion into database, etc.
'''

# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
from nfl.names import first_last

logging.getLogger(__name__).addHandler(logging.NullHandler())


def draft_table(players):
    '''
    Converts data from pfr draft page for insertion into draft table

    Arguments:
        players: list of dict

    Returns:
        list of dict
    '''
    fixed = []
    for p in players:
        f = p.copy()
        f['draft_overall_pick'] = p['draft_pick']
        f.pop('draft_pick', None)
        f['source_team_code'] = p['team']
        f.pop('team', None)
        f['source_player_name'] = first_last(p['player'])
        f.pop('player', None)
        fixed.append(f)
    return fixed


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


if __name__ == '__main__':
    pass