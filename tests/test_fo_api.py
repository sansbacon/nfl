# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.scrapers.footballoutsiders import FootballOutsidersAPIScraper


class FO_api_test(unittest.TestCase):

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
        self.s = FootballOutsidersAPIScraper(cache_name='fo-api-test')
        #self.p = FootballOutsidersNFLParser()

    def test_dvoa_week(self):
        content = self.s.dvoa_week(self.season, self.week)
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)

    def test_team_season(self):
        content = self.s.team_season(self.season, self.team)
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)

    def test_team_week(self):
        content = self.s.team_week(self.season, self.week)
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()