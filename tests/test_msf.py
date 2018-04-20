# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.scrapers.msf import MySportsFeedsNFLScraper

class TestMSFScraper(unittest.TestCase):


    @property
    def game(self):
        return random.choice(['20160911-NE-ARI', '20160911-GB-JAX'])

    @property
    def position(self):
        return random.choice(['QB', 'RB', 'WR', 'TE'])

    @property
    def season(self):
        return 2016 #random.choice(range(2014, 2017))

    @property
    def team(self):
        return random.choice(['WAS', 'ARI', 'CHI', 'DET'])

    @property
    def week(self):
        return random.choice(range(1, 18))

    def setUp(self):
        self.s = MySportsFeedsNFLScraper(username='XXX', password='XXX', cache_name='test-msf-scraper')

    def test_boxscore(self):
        # NOTE: this doesn't work with noncommercial account
        #    content = self.s.boxscore(self.game, 2016)
        #    self.assertIsInstance(content, dict)
        pass

    def test_season_stats(self):
        content = self.s.season_stats()
        self.assertIsInstance(content, dict)
        content = self.s.season_stats(self.season)
        self.assertIsInstance(content, dict)

    def test_schedule(self):
        content = self.s.schedule()
        self.assertIsInstance(content, dict)
        content = self.s.schedule(self.season)
        self.assertIsInstance(content, dict)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
