# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
from string import ascii_uppercase
import random
import sys
import unittest

from nfl.scrapers.pfr import PfrNFLScraper
from nfl.parsers.pfr import PfrNFLParser


class Pfr_test(unittest.TestCase):

    @property
    def last_initial(self):
        return random.choice(ascii_uppercase)

    @property
    def seas(self):
        return random.choice(range(2002, 2017))

    def setUp(self):
        self.s = PfrNFLScraper(cache_name='pfr-plays-query')
        self.p = PfrNFLParser()

    def test_team_plays_query(self):
        content = self.s.team_plays_query(season_start=2016, season_end=2016, offset=0)
        self.assertIsNotNone(content)
        self.assertRegexpMatches(content, r'html')

    def test_draft(self):
        content = self.s.draft(self.seas)
        self.assertIsNotNone(content)
        players = self.p.draft(content, self.seas)
        self.assertIsNotNone(players)
        player = random.choice(players)
        self.assertIn('draft_year', player.keys())

    def test_fantasy_season(self):
        content = self.s.fantasy_season(self.seas)
        self.assertIsNotNone(content)
        self.assertIn('Bell', content)

    def test_fantasy_week(self):
        content = self.s.fantasy_week(self.seas, 9)
        self.assertIsNotNone(content)
        self.assertIn('Bell', content)

    def test_players(self):
        content = self.s.players(self.last_initial)
        self.assertIsNotNone(content)

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()