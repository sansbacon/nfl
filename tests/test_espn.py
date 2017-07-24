# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.scrapers.espn import ESPNNFLScraper
from nfl.parsers.espn import ESPNNFLParser


class ESPN_test(unittest.TestCase):
    '''
    Tests nfldotcom scraper and parser
    '''
    @property
    def offset(self):
        return random.choice([40, 80, 120, 160, 200, 240])

    def setUp(self):
        self.s = ESPNNFLScraper(cache_name='test-espn-scraper')
        self.p = ESPNNFLParser()

    def test_league_roster(self):
        content = self.s.league_roster(2016, 302946, 12)
        self.assertIsNotNone(content)
        self.assertIn('STARTERS', content)

    def test_projections(self):
        content = self.s.projections()
        self.assertIsNotNone(content)
        self.assertIn('PLAYERS', content)
        content = self.s.projections(offset=self.offset)
        self.assertIsNotNone(content)
        self.assertIn('PLAYERS', content)

    def test_waiver_wire(self):
        content = self.s.waiver_wire(302946, 12)
        self.assertIsNotNone(content)
        self.assertIn('PLAYERS', content)


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
