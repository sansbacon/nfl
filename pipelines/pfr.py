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


if __name__ == '__main__':
    pass