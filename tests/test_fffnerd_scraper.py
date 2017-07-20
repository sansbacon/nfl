# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import os
import random
import sys
import unittest

from nfl.scrapers.ffnerd import FFNerdNFLScraper


class TestFFNerdScraper(unittest.TestCase):

    @property
    def position(self):
        return random.choice(['QB', 'RB', 'WR', 'TE'])

    @property
    def season(self):
        return random.choice(range(2010, 2017))

    @property
    def team(self):
        return random.choice(['WAS', 'ARI', 'CHI', 'DET'])

    @property
    def week(self):
        return random.choice(range(1, 18))

    def setUp(self):
        self.s = FFNerdNFLScraper(api_key=os.getenv('FFNERD_API_KEY'),
                                  cache_name='test-ffnerd-scraper')

    def test_depth_charts(self):
        self.assertIsNotNone(self.s.depth_charts())

    def test_draft_projections(self):
        self.assertIsNotNone(self.s.draft_projections(self.position))

    def test_draft_rankings(self):
        self.assertIsNotNone(self.s.draft_rankings())

    def test_draft_tiers(self):
        self.assertIsNotNone(self.s.draft_tiers())

    def test_injuries(self):
        self.assertIsNotNone(self.s.injuries(self.week))

    def test_players(self):
        self.assertIsNotNone(self.s.players())
        self.assertIsNotNone(self.s.players(self.position))

    def test_schedule(self):
        self.assertIsNotNone(self.s.schedule())

    def test_weekly_projections(self):
        self.assertIsNotNone(self.s.weekly_projections(self.week, self.position))

    def test_weekly_rankings(self):
        self.assertIsNotNone(self.s.weekly_rankings(self.week, self.position))

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()