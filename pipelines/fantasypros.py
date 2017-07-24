# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging

from nfl.teams import long_to_code


logging.getLogger(__name__).addHandler(logging.NullHandler())


def weekly_rankings_table(rankings, season_year):
    '''
    Converts data from fantasypros.com weekly rankings page for insertion into weekly_rankings table
    
    Args:
        results: list of dict

    Returns:
        list of dict
    '''
    for idx, player in enumerate(rankings):
        rankings[idx]['season_year'] = season_year
        rankings[idx]['source'] = 'fantasypros'
        rankings[idx]['position'] = player.get('pos', '').upper()
        rankings[idx].pop('pos', None)
        if player['position'] == 'DST':
            rankings[idx]['team_code'] = long_to_code(player['player'])
        rankings[idx]['source_player_name'] = player['player']
        rankings[idx].pop('player', None)
        rankings[idx].pop('bye', None)
        rankings[idx].pop('last_updated', None)
        if ' ' in player.get('opp', ''):
            rankings[idx]['opp'] = player['opp'].split()[-1]
    return rankings

if __name__ == '__main__':
    pass