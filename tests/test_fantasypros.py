# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.parsers.fantasypros import FantasyProsNFLParser
from nfl.scrapers.fantasypros import FantasyProsNFLScraper


class TestFantasyProsScraper(unittest.TestCase):

    @property
    def std_positions(self):
        return random.choice(['qb', 'k', 'dst'])

    @property
    def ppr_positions(self):
        return random.choice(['rb', 'wr', 'te', 'flex', 'qb-flex'])

    def setUp(self):
        self.s = FantasyProsNFLScraper()
        self.p = FantasyProsNFLParser()

    def test_adp(self):
        content = self.s.adp(fmt='std')
        players = self.p.adp(content)
        self.assertIsNotNone(players)
        content = self.s.adp(fmt='ppr')
        players = self.p.adp(content)
        self.assertIsNotNone(players)

    def test_draft_rankings(self):
        content = self.s.draft_rankings(pos=self.std_positions, fmt='std')
        self.assertIsNotNone(self.p.draft_rankings_overall(content))
        content = self.s.draft_rankings(pos=self.ppr_positions, fmt='ppr')
        self.assertIsNotNone(self.p.draft_rankings_overall(content))
        content = self.s.draft_rankings(pos=self.ppr_positions, fmt='hppr')
        self.assertIsNotNone(self.p.draft_rankings_overall(content))

    def test_projections(self):
        pos = self.std_positions
        self.assertIsNotNone(self.p.projections(self.s.projections(pos, fmt='std', week='draft'), pos))
        pos = self.ppr_positions
        self.assertIsNotNone(self.p.projections(self.s.projections(pos, fmt='ppr', week='draft'), pos))
        self.assertIsNotNone(self.p.projections(self.s.projections(pos, fmt='hppr', week='draft'), pos))

    def test_ros_rankings(self):
        pass

        '''
        pos = self.std_positions
        self.assertIsNotNone(self.p.ros_rankings(self.s.ros_rankings(pos, fmt='std', week='draft'), pos))
        pos = self.ppr_positions
        self.assertIsNotNone(self.p.ros_rankings(self.s.ros_rankings(pos, fmt='ppr', week='draft'), pos))
        self.assertIsNotNone(self.p.ros_rankings(self.s.ros_rankings(pos, fmt='hppr', week='draft'), pos))
        '''

    def test_weekly_rankings(self):
        pos = self.std_positions
        self.assertIsNotNone(self.p.weekly_rankings(self.s.weekly_rankings(pos, fmt='std', week=1)))
        pos = self.ppr_positions
        self.assertIsNotNone(self.p.weekly_rankings(self.s.weekly_rankings(pos, fmt='ppr', week=1)))
        self.assertIsNotNone(self.p.weekly_rankings(self.s.weekly_rankings(pos, fmt='hppr', week=1)))

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()