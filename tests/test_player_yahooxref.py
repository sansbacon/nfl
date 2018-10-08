# -*- coding: utf-8 -*-
# tests/test_player_yahooxref.py

import logging
import random
import sys
import unittest

from nfl.player.yahooxref import *
from nfl.utility import getdb


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class Player_yahooxref_test(unittest.TestCase):

    def setUp(self):
        self.db = getdb('nfl')
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

    def test_mfl_players_db(self):
        p = yahoo_playerids_db(self.db)
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


if __name__=='__main__':
    unittest.main()