# -*- coding: utf-8 -*-

import logging
import random
import sys
import unittest

from nfl.pgf import PlayerGameFinder


class Pgf_test(unittest.TestCase):

    def setUp(self):
        self.pgf = PlayerGameFinder()

    def test_valid_pos(self):
        self.assertTrue(self.pgf.valid_pos('QB'))
        self.assertFalse(self.pgf.valid_pos('XXX'))

    def test_valid_tc(self):
        self.assertTrue(self.pgf.valid_tc('car'))
        self.assertFalse(self.pgf.valid_tc('lar'))

    def test_do_load(self):
        self.pgf.do_load('')
        self.assertIsNotNone(self.pgf.data)

    def test_help_load(self):
        msg = self.pgf.help_load()
        self.assertIsNotNone(msg)

    def test_do_sort(self):
        inp = 'pts'
        self.pgf.do_sort(inp)
        self.assertEqual(inp, self.pgf.sort_key)

    def test_help_sort(self):
        msg = self.pgf.help_sort()
        self.assertIsNotNone(msg)

    def test_conv_col(self):
        self.assertIsInstance(self.pgf._conv_col(1.0), float)
        self.assertEqual(self.pgf._conv_col('x'), 0.0)

    @unittest.skip
    def test_dump_search(self):
        self.pgf._dump_search(df, pos)


    """


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


    """

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
