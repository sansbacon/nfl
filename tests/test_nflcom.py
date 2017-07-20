# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.agents.nflcom import NFLComAgent
from nfl.scrapers.nflcom import NFLComScraper
from nfl.parsers.nflcom import NFLComParser
from nfl.pipelines.nflcom import gamesmeta_table


class Nfldotcom_test(unittest.TestCase):
    '''
    Tests nfldotcom scraper and parser
    '''

    def setUp(self):
        self.s = NFLComScraper(cache_name='test-nfldotcom-scraper')
        self.p = NFLComParser()
        self.a = NFLComAgent(scraper=self.s, parser=self.p)
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.all_games = []

    def test_gamebook(self):
        self.assertIsNotNone(self.s.gamebook(2016, 1, 56905))

    #def test_week_page(self):
    #    season = random.choice(range(2002, 2009))
    #    week = random.choice(range(1, 17))
    #    dc = gamesmeta_table(self.p.week_page(self.s.week_page(season, week)))
    #    logging.info(dc)

    #def test_week_pages(self):
    #    season = random.choice(range(2002, 2009))
    #    for week in random.sample(range(1, 17), 3):
    #        logging.info(gamesmeta_table(self.p.week_page(self.s.week_page(season, week))))


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
