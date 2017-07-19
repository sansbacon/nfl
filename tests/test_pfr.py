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
        content = self.s.team_plays_query(season_start=2009, season_end=2016, offset=0)
        self.assertIsNotNone(content)
        self.assertRegexpMatches(content, r'html')
        teams = self.p.team_plays(content)
        self.assertIsNotNone(teams)
        logging.info(teams)


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()