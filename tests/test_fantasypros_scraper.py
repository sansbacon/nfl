# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import unittest

from nfl.scrapers.fantasypros import FantasyProsNFLScraper


class TestFantasyProsScraper(unittest.TestCase):

    def setUp(self):
        self.s = FantasyProsNFLScraper()

    def test_adp(self):
        self.assertIsNotNone(self.s.adp(fmt='std'))
        self.assertIsNotNone(self.s.adp(fmt='ppr'))

    def test_draft_rankings(self):
        std_positions = ['qb', 'k', 'dst']
        ppr_positions = ['rb', 'wr', 'te', 'flex', 'qb-flex']
        self.assertIsNotNone(self.s.draft_rankings(pos=random.choice(std_positions), fmt='std'))
        self.assertIsNotNone(self.s.draft_rankings(pos=random.choice(ppr_positions), fmt='ppr'))
        self.assertIsNotNone(self.s.draft_rankings(pos=random.choice(ppr_positions), fmt='hppr'))

    def test_projections(self):
        std_positions = ['qb', 'k', 'dst']
        ppr_positions = ['rb', 'wr', 'te', 'flex', 'qb-flex']
        self.assertIsNotNone(self.s.projections(pos=random.choice(std_positions), fmt='std', week='draft'))
        self.assertIsNotNone(self.s.projections(pos=random.choice(ppr_positions), fmt='ppr', week='draft'))
        self.assertIsNotNone(self.s.projections(pos=random.choice(ppr_positions), fmt='hppr', week='draft'))

    def test_ros_rankings(self):
        std_positions = ['qb', 'k', 'dst']
        ppr_positions = ['rb', 'wr', 'te', 'flex', 'qb-flex']
        self.assertIsNotNone(self.s.ros_rankings(pos=random.choice(std_positions), fmt='std'))
        self.assertIsNotNone(self.s.ros_rankings(pos=random.choice(ppr_positions), fmt='ppr'))
        self.assertIsNotNone(self.s.ros_rankings(pos=random.choice(ppr_positions), fmt='hppr'))

    def test_weekly_rankings(self):
        std_positions = ['qb', 'k', 'dst']
        ppr_positions = ['rb', 'wr', 'te', 'flex', 'qb-flex']
        self.assertIsNotNone(self.s.weekly_rankings(pos=random.choice(std_positions), fmt='std', week=random.choice(range(1,18))))
        self.assertIsNotNone(self.s.weekly_rankings(pos=random.choice(ppr_positions), fmt='ppr', week=random.choice(range(1,18))))
        self.assertIsNotNone(self.s.weekly_rankings(pos=random.choice(ppr_positions), fmt='hppr', week=random.choice(range(1,18))))

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()