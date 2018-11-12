#!/usr/bin/env python3
# nfl/pgf.py
# interactive search of player_game_finder

from cmd import Cmd
import itertools
import json
import logging
import os
import inspect
from pathlib import Path

import pandas as pd

from nfl.pfr import Scraper, Parser
from nfl.utility import flatten_list


class PlayerGameFinder(Cmd):

    prompt = 'player_game_finder> '
    intro = 'Welcome to Player Game Finder! Type ? to list commands'

    def __init__(self):
        super(PlayerGameFinder, self).__init__()
        self._s = Scraper('pgf')
        self._p = Parser()
        self.opp = None
        self.pos = None
        self.sort_key = None
        self.thresh = 0
        self.data = None

    @property
    def positions(self):
        return ['QB', 'RB', 'TE', 'WR']

    @property
    def team_codes(self):
        return ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den',
                 'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'mia',
                 'min', 'nwe', 'nor', 'nyg', 'nyj',
                 'rai', 'phi', 'pit', 'sfo', 'sea', 'tam', 'oti', 'was']

    def valid_pos(self, pos):
        return pos in self.positions

    def valid_tc(self, tc):
        return tc in self.team_codes

    def do_load(self, inp):
        '''

        Args:
            inp:

        Returns:

        '''
        pth = Path(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
        with open (str(pth / 'data' / 'pgf.json'), 'r') as f:
            self.data = json.load(f)

    def help_load(self):
        msg = '\nLoads data from json file\n'
        print(msg)
        return msg

    def do_sort(self, inp):
        self.sort_key = inp

    def help_sort(self):
        msg = '\nSets sort key for dataframe\n'
        print(msg)
        return msg

    def do_exit(self, inp):
        print('Bye')
        return True

    def help_exit(self):
        print('exit the application. Shorthand: x q Ctrl-D.')

    def _conv_col(self, v):
        '''
        Converts value to float or zero

        Args:
            v:

        Returns:
            float

        '''
        try:
            v = float(v)
        except:
            v = 0.0
        return v

    def _dump_search(self, df, pos):
        '''
        Pretty-prints results

        '''
        if pos == 'QB':
            cols = []
            for col in ['player', 'pos', 'week_num', 'team', 'pass_att', 'pass_cmp',
                        'pass_yds', 'pass_td', 'rush_att', 'rush_yds', 'rush_td', 'draftkings_points']:
                if col in df.columns:
                    cols.append(col)
        elif pos in ['RB', 'WR', 'TE']:
            cols = []
            for col in ['player', 'pos', 'week_num', 'team', 'targets', 'rec', 'rec_yds', 'rec_td',
                        'rush_att', 'rush_yds', 'rush_td', 'draftkings_points']:
                if col in df.columns:
                    cols.append(col)
        else:
            cols = df.columns

        df.dropna(axis=0, how='all', inplace=True)
        df.drop_duplicates(subset=['player', 'week_num', 'team'], keep='first', inplace=True)

        try:
            dfr = df[cols].copy()
            dfr.rename(columns={'week_num': 'week', 'draftkings_points': 'dkpts'},
                       inplace=True)
            dfr['dkpts'] = dfr['dkpts'].apply(lambda x: self._conv_col(x))
            dfr = dfr.query('dkpts >= 1')
            if self.sort_key in ['dkpts', 'draftkings_points', 'points', 'pts']:
                print(dfr.sort_values('dkpts', ascending=False))
            else:
                print(dfr)
        except Exception as e:
            print(e)
        return df

    def do_search(self, inp):
        if '|' in inp:
            params = dict(itertools.zip_longest(*[iter(inp.split('|'))] * 2, fillvalue=''))
        else:
            params = {'opp_id': self.opp, 'pos[]': self.pos.upper(), 'c2val': str(self.thresh)}
        if self.data:
            key = params['opp_id'] + '_' + params['pos{}']
            vals = flatten_list([v for k,v in self.data.items if key in k])
        else:
            try:
                content = self._s.player_game_finder(params)
                vals = self._p.player_game_finder(content)
            except Exception as e:
                print(e)
                print(self._s.urls[-1])
        try:
            df = pd.DataFrame(vals)
            self._dump_search(df, self.pos)
        except:
            pass
        finally:
            return None

    def help_search(self):
        msg = ('Searches pfr for positional results vs. team',
               'Can use opp, pos, and thresh and pass no parameters',
               'Or can pass parameters as pipe-delimited string, e.g. opp|car|pos[]|QB')
        print('\n', '\n'.join(msg), '\n')
        return msg

    def do_merge(self, inp):
        params = dict(itertools.zip_longest(*[iter(inp.split('|'))] * 2, fillvalue=''))
        print(self._s._merge_pgl_params(params))

    def help_merge(self):
        msg = ('Shows dict output of pipe-delimited string, e.g. opp|car|pos[]|QB')
        print('\n', msg, '\n')
        return msg

    def do_opp(self, inp):
        tc = inp.lower()
        if self.valid_tc(tc):
            self.opp = tc
            print('Set opp to {}'.format(self.opp))
        else:
            print('Invalid team code: {}'.format(inp))
            print('Valid codes are: \n{}'.format(self.team_codes))

    def help_opp(self):
        msg = ('Sets opponent or shows valid opponents, e.g. car')
        print('\n', msg, '\n')
        return msg

    def do_pos(self, inp):
        pos = inp.upper()
        if self.valid_pos(pos):
            self.pos = pos
            print('Set pos to {}'.format(self.pos))
        else:
            print('Invalid position: {}'.format(pos))
            print('Valid positions are: \n{}'.format(self.positions))

    def help_pos(self):
        msg = ('Sets position or shows valid positions, e.g. QB')
        print('\n', msg, '\n')
        return msg

    def do_thresh(self, inp):
        try:
            self.thresh = int(inp)
            print('Set thresh to {}'.format(self.thresh))
        except:
            print('invalid threshold {}'.format(inp))

    def help_thresh(self):
        msg = ('Sets threshold fantasy points to display player, e.g. 5')
        print('\n', msg, '\n')
        return msg

    def do_settings(self, inp):
        print(self.__dict__)

    def help_settings(self):
        msg =  'Shows current settings, such as opp, pos, and thresh'
        print('\n', msg, '\n')
        return msg

    do_EOF = do_exit
    help_EOF = help_exit


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler('/tmp/pgf.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.ERROR)
    PlayerGameFinder().cmdloop()
