# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import os
import random
import sys
import unittest

from nfl.msf import Scraper, Parser


class TestMSFScraper(unittest.TestCase):

    @property
    def game(self):
        return random.choice(['20160911-NE-ARI', '20160911-GB-JAX'])

    @property
    def position(self):
        return random.choice(['QB', 'RB', 'WR', 'TE'])

    @property
    def season(self):
        # random.choice(range(2016, 2019))
        return 2016

    @property
    def team(self):
        return random.choice(['WAS', 'ARI', 'CHI', 'DET'])

    @property
    def week(self):
        return random.choice(range(1, 18))

    def setUp(self):
        self.s = Scraper(username=os.getenv('msf_user'),
                         password=os.getenv('msf_password'),
                         cache_name='test-msf-scraper')
        self.p = Parser()

    def test_credentials(self):
        self.assertIsNotNone(os.getenv('msf_user'))
        self.assertIsNotNone(os.getenv('msf_password'))

    @unittest.skip
    def test_boxscore(self):
        # NOTE: this doesn't work with noncommercial account
        content = self.s.boxscore(self.game, 2016)
        self.assertIsInstance(content, dict)

    def test_season_stats(self):
        content = self.s.season_stats()
        self.assertIsInstance(content, dict)
        content = self.s.season_stats(self.season)
        self.assertIsInstance(content, dict)

    @unittest.skip
    def test_schedule(self):
        content = self.s.schedule()
        self.assertIsInstance(content, dict)
        content = self.s.schedule(self.season)
        self.assertIsInstance(content, dict)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
    unittest.main()
