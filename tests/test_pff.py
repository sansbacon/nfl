# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.scrapers.pff import PFFScraper
from nfl.parsers.pff import PFFParser


class Pff_test(unittest.TestCase):

    @property
    def team_id(self):
        return random.choice(range(1,33))

    @property
    def player(self):
        return random.choice([11853, 1317, 6326, 6332, 1384])

    def setUp(self):
        self.s = PFFScraper()
        self.p = PFFParser()

    def test_depth_charts(self):
        pass
        #content = self.s.depth_charts(self.team_id)
        #self.assertIsNotNone(content)
        #self.assertIsInstance(content, dict)

    def test_position_grades(self):
        # pos
        pass

    def test_player_grades_career(self):
        # player_id
        pass

    def test_player_grades_week(self):
        # player_id
        pass

    def test_player_snaps_season(self):
        # player_id
        pass

    def test_players(self):
        # team_id
        pass

    def test_teams(self):
        pass

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()