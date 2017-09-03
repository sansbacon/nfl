# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import datetime
import logging


class DraftKingsNFLParser(object):
    '''
    '''

    def __init__(self):
        '''
        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def weekly_players_games(self, content):
        '''
        
        Args:
            content: parsed JSON dict

        Returns:
            players, games
        '''
        players = []
        wanted = ['pid', 'pcode', 'fn', 'ln', 'pn', 'tid', 'htid', 'atid', 'htabbr', 'atabbr', 's',
                  'ppg', 'or', 'pp', 'i']
        players = [{k:v for k,v in p.items() if k in wanted} for p in content['playerList']]
        games = []
        for game_id, gamev in content['teamList'].items():
            game = {'source_game_id': game_id}
            d = gamev.get('tz').split('(')[-1].split(')')[0]
            game['game_date'] = datetime.datetime.utcfromtimestamp(int(d) / 1000)
            game['source_home_team_code'] = gamev['ht']
            game['source_away_team_code'] = gamev['at']
            games.append(game)

        return players, games

if __name__ == '__main__':
    pass
