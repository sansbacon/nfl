# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import json
import logging


class DraftNFLParser(object):

    def __init__(self):
        '''
        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def player_pool(self, pp):
        '''
        Parses draft JSON player_pool
        
        Args:
            pp: parsed JSON

        Returns:
            list of player dict
        '''
        positions = {i['id']: i['name'] for i in pp['player_pool']['positions']}
        teams = {str(i['id']): i['abbr'] for i in pp['player_pool']['teams']}

        # get player basics
        draft_players = {}
        for pl in pp['player_pool']['players']:
            fn = pl['first_name'] + ' ' + pl['last_name']
            pid = pl.get('id')
            tid = str(pl.get('team_id', 'UNK'))
            tc = teams.get(tid, 'UNK')
            draft_players[pl['id']] = {
                'source': 'draft', 'source_player_name': fn,
                'source_player_id': pid, 'source_team_code': tc,
                'season_year': 2017, 'week': 1, 'projection_type': 'hppr'
            }

        # now get the projections
        for pl in pp['player_pool']['bookings']:
            dpl = draft_players.get(pl['player_id'])
            if dpl:
                proj = pl.get('projected_points', 0)
                draft_players[pl['player_id']]['projection'] = float(proj)
                pos = pl.get('position_id', 'UNK')
                draft_players[pl['player_id']]['source_player_position'] = positions.get(str(pos), 'UNK')
        
        return draft_players