# -*- coding: utf-8 -*-
# tests/test_pff.py

import logging
import os
import random
import sys
import unittest

import psutil
from nfl.pff import Parser
from nfl.pff import Scraper


class Pff_test(unittest.TestCase):

    @property
    def player(self):
        return random.choice([11853, 1317, 6326, 6332, 1384])

    @property
    def pos(self):
        return random.choice(['QB', 'HB', 'WR', 'TE'])

    @property
    def team_id(self):
        return random.choice(range(1, 33))

    def setUp(self):
        self.s = Scraper(profile=os.getenv('mozilla_profile'))
        self.p = Parser()

    def tearDown(self):
        self.s.browser.close()
        self.s.browser.quit()
        procnames = ["Xvfb", "geckodriver"]
        for proc in psutil.process_iter():
            # check whether the process name matches
            if proc.name() in procnames:
                proc.kill()

    @unittest.skip
    def test_position_grades(self):
        content = self.s.position_grades(self.pos)
        logging.info(content)
        self.assertIsInstance(content, dict)
        self.assertGreater(len(self.p.position_grades(content)), 0)

    @unittest.skip
    def test_depth_charts(self):
        content = self.s.depth_charts(self.team_id)
        self.assertIsInstance(content, dict)
        self.assertGreater(len(self.p.depth_charts(content)), 0)
        excl = ('rt', 'rg', 'lt', 'lg', 'c')
        self.assertGreater(len(self.p.depth_charts(content, excl)), 0)

    @unittest.skip
    def test_player_grades_career(self):
        content = self.s.player_grades_career(self.player)
        self.assertIsInstance(content, list)
        self.assertGreater(len(self.p.player_grades_career(content)), 0)

    @unittest.skip
    def test_player_grades_week(self):
        content = self.s.player_grades_week(self.player)
        self.assertIsInstance(content, list)
        self.assertGreater(len(self.p.player_grades_week(content)), 0)

    @unittest.skip
    def test_player_snaps_season(self):
        content = self.s.player_snaps_season(self.player)
        self.assertIsInstance(content, list)
        self.assertGreater(len(self.p.player_snaps_season(content)), 0)

    @unittest.skip
    def test_players(self):
        content = self.s.players(self.team_id)
        self.assertIsInstance(content, dict)
        self.assertGreater(len(self.p.players(content)), 0)

    @unittest.skip
    def test_teams(self):
        content = self.s.teams()
        self.assertIsInstance(content, dict)
        self.assertGreater(len(self.p.teams(content)), 0)

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
    unittest.main()
