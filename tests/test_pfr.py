# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import sys
import unittest

from nfl.scrapers.pfr import PfrNFLScraper
from nfl.parsers.pfr import PfrNFLParser


class Pfr_test(unittest.TestCase):

    def setUp(self):
        self.s = PfrNFLScraper(cache_name='pfr-plays-query')
        self.p = PfrNFLParser()

    def test_team_plays_query(self):
        content = self.s.team_plays_query(season_start=2016, season_end=2016, offset=0)
        self.assertIsNotNone(content)
        self.assertRegexpMatches(content, r'html')

    def test_draft(self):
        content = self.s.draft(2016)
        self.assertIsNotNone(content)
        self.assertIn('Myles', content)

    def test_fantasy_season(self):
        content = self.s.fantasy_season(2016)
        self.assertIsNotNone(content)
        self.assertIn('Bell', content)

    def test_fantasy_week(self):
        content = self.s.fantasy_week(2016, 9)
        self.assertIsNotNone(content)
        self.assertIn('Bell', content)

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()