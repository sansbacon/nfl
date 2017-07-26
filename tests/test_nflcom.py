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
    TODO: these are not fully implemented
    '''

    @property
    def gsis_id(self):
        vals = ["2015090365", "2009101809", "2013120103", "2016100904", "2015092712",
                "2009100410", "2014080705", "2012092311", "2011112800", "2012120906",
                "2011103009", "2010091906", "2013112407", "2013082404", "2014110902",
                "2012101100", "2016010307", "2009101111", "2014091402", "2016090151"]
        return random.choice(vals)

    @property
    def season(self):
        return random.choice(range(2009, 2017))

    @property
    def week(self):
        return random.choice(range(1, 18))

    def setUp(self):
        self.s = NFLComScraper(cache_name='test-nfldotcom-scraper')
        self.p = NFLComParser()
        self.a = NFLComAgent(scraper=self.s, parser=self.p)
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.all_games = []

    def test_game(self):
        self.assertIsNotNone(self.s.game(self.gsis_id))

    def test_gamebook(self):
        self.assertIsNotNone(self.s.gamebook(2016, 1, 56905))

    def test_injuries(self):
        self.assertIsNotNone(self.s.injuries(self.week))

    def test_ol(self):
        self.assertIsNotNone(self.s.ol(self.season))

    def test_schedule_week(self):
        # season, week):
        self.assertIsNotNone(self.s.schedule_week(self.season, self.week))

    def test_score_week(self):
        self.assertIsNotNone(self.s.score_week(self.season, self.week))


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
