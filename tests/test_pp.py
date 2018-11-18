# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import unittest

from nfl.pp import Scraper, Parser


class TestPlayerProfiler(unittest.TestCase):

    def setUp(self):
        self.s = Scraper()
        self.p = Parser()

    def test_player_page(self):
        content = self.s.player_page('TT-0500')
        self.assertIsNotNone(content)
        data = content['data']['Player']
        self.assertIsInstance(data, dict)
        mh = self.p.player_medical_history(data)
        self.assertIsInstance(mh, list)
        gl = self.p.player_game_logs(data)
        self.assertIsInstance(gl, list)

    def test_players(self):
        data = self.s.players()
        self.assertIsNotNone(data)
        self.assertIsInstance(data, dict)

    def test_rankings(self):
        data = self.s.rankings()
        self.assertIsNotNone(data)
        self.assertIsInstance(data, dict)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
