# -*- coding: utf-8 -*-
# tests/test_player_mflxref.py

import logging
import random
import sys
import unittest

from nfl.player.mflxref import *
from nfl.utility import getdb


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class Player_mflxref_test(unittest.TestCase):

    def setUp(self):
        self.db = getdb('nfl')
        self.season_year = 2018
        self.logger = logging.getLogger()

    def rand_dictitem(self, d):
        '''
        Gets random item from dict

        Args:
            d(dict):

        Returns:
            tuple: dict key and value

        '''
        k = random.choice(list(d.keys()))
        return (k, d[k])

    @unittest.skip
    def test_mfl_players_db(self):
        p = mfl_players_db(self.db)
        self.logger.info(p[0])
        self.assertIsNotNone(p)

    @unittest.skip
    def test_mfl_playersd_db(self):
        d = mfl_playersd_db(self.db)
        item = self.rand_dictitem(d)
        self.logger.info(item)
        self.assertIsInstance(d, dict)
        self.assertIsInstance(item, tuple)

    @unittest.skip
    def test_mfl_playerids_db(self):
        p = mfl_playerids_db(self.db)
        self.logger.info(p[0])
        self.assertIsNotNone(p)

    @unittest.skip
    def test_mfl_players_web(self):
        p = mfl_players_web(self.season_year)
        self.logger.info(p[0])
        self.assertIsInstance(p, list)

    @unittest.skip
    def test_mfl_playersd_web(self):
        d = mfl_playersd_web(self.season_year)
        item = self.rand_dictitem(d)
        self.logger.info(item)
        self.assertIsInstance(d, dict)
        self.assertIsInstance(item, tuple)

    @unittest.skip
    def test_mfl_playerids_web(self):
        p = mfl_playerids_web(self.season_year)
        self.logger.info(p[0])
        self.assertIsNotNone(p)

    def test_mfl_not_in_db(self):
        l1 = [1, 2, 3]
        l2 = [1, 2, 5, 6, 7]
        s1 = set((5,6,7))
        diff = mfl_not_in_db(l1, l2)
        self.assertIsInstance(diff, set)
        self.assertTrue(s1 == diff)

if __name__=='__main__':
    unittest.main()