# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.scrapers.footballoutsiders import FootballOutsidersNFLScraper
from nfl.parsers.footballoutsiders import FootballOutsidersNFLParser


class FO_test(unittest.TestCase):

    @property
    def season(self):
        return random.choice(range(2010, 2017))

    def setUp(self):
        self.s = FootballOutsidersNFLScraper(cache_name='fo-test')
        self.p = FootballOutsidersNFLParser()

    def test_dl(self):
        seas = self.season
        content = self.s.dl()
        self.assertIsNotNone(content)
        content = self.s.dl(seas)
        self.assertIsNotNone(self.p.dl(content, seas))

    def test_drive(self):
        content = self.s.drive(season=self.season, offdef='off')
        self.assertIsNotNone(self.p.drive(content=content, offdef='off'))

    def test_ol(self):
        seas = self.season
        content = self.s.ol()
        self.assertIsNotNone(content)
        content = self.s.ol(seas)
        self.assertIsNotNone(self.p.ol(content, seas))

    def test_qb(self):
        content = self.s.qb()
        self.assertIsNotNone(content)
        content = self.s.qb(season=self.season)
        self.assertIsNotNone(content)

    '''
    def test_rb(self):
        content = self.s.rb()
        self.assertIsNotNone(content)
        content = self.s.rb(season=self.season)
        self.assertIsNotNone(content)

    def test_te(self):
        content = self.s.te()
        self.assertIsNotNone(content)
        content = self.s.te(season=self.season)
        self.assertIsNotNone(content)

    def test_wr(self):
        content = self.s.wr()
        self.assertIsNotNone(content)
        content = self.s.wr(season=self.season)
        self.assertIsNotNone(content)

    def test_snap_counts(self):
        content = self.s.snap_counts(self.season, 1)
        self.assertIsNotNone(content)
        self.assertIn('snap counts', content)

    def test_team_defense(self):
        content = self.s.team_defense()
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)
        content = self.s.team_defense(season=self.season)
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)

    def test_team_efficiency(self):
        content = self.s.team_efficiency()
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)
        content = self.s.team_efficiency(season=self.season)
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)

    def test_team_offense(self):
        content = self.s.team_offense()
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)
        content = self.s.team_offense(season=self.season)
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)

            #def test_dvoa_table(self):
        #    content = self.s.dvoa_table('')
        #    self.assertIsNotNone(content)
        #    self.assertRegexpMatches(content, r'html')
        #    logging.info('test')
    '''

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()