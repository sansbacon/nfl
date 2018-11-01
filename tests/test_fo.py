# -*- coding: utf-8 -*-

import logging
import random
import sys
import unittest

import nfl.fo as nf

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class Fo_test(unittest.TestCase):
    '''
    Tests football outsiders scraper and parser
    '''

    @property
    def season(self):
        return random.choice(range(2009, 2017))

    @property
    def week(self):
        return random.choice(range(1, 18))

    def setUp(self):
        self.s = nf.Scraper(cache_name='test-fo-scraper')
        self.p = nf.Parser()
        self.all_games = []

    """
    def test_dl(self):
        content = self.s.dl()
        self.assertIsNotNone(content)
        self.p.dl(content)
    
    
    def test_drive(self):
        content = self.s.drive()
        self.assertIsNotNone(content)
        self.p.drive(content)
    
    
    def test_ol(self):
        content = self.s.ol()
        self.assertIsNotNone(content)
        self.p.ol(content)
    
    
    def test_qb(self):
        content = self.s.qb()
        self.assertIsNotNone(content)
        self.p.qb(content)
    
    
    def test_rb(self):
        content = self.s.rb()
        self.assertIsNotNone(content)
        self.p.rb(content)
    
    
    def test_snap_counts(self):
        content = self.s.snap_counts()
        self.assertIsNotNone(content)
        self.p.snap_counts(content)
    
    
    def test_te(self):
        content = self.s.te()
        self.assertIsNotNone(content)
        self.p.te(content)
    
    
    def test_team_defense(self):
        content = self.s.team_defense()
        self.assertIsNotNone(content)
        self.p.team_defense(content)
    
    
    def test_team_efficiency(self):
        content = self.s.team_efficiency()
        self.assertIsNotNone(content)
        self.p.team_efficiency(content)
    
    
    def test_team_offense(self):
        content = self.s.team_offense()
        self.assertIsNotNone(content)
        self.p.team_offense(content)
    
    
    def test_wr(self):
        content = self.s.wr()
        self.assertIsNotNone(content)
        self.p.wr(content)
    """


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    unittest.main()
