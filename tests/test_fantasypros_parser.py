# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.parsers.fantasypros import FantasyProsNFLParser


class Fantasypros_parser_test(unittest.TestCase):

    def setUp(self):
        self._p = FantasyProsNFLParser()

    def test_adp(self):
        with open('data/fantasypros-adp.html') as infile:
            content = infile.read()
        players = self._p.adp(content)
        self.assertIsNotNone(players)
        self.assertTrue(random.choice(players).has_key('source_player_id'))

    def test_depth_chart(self):
        with open ('data/fantasypros-dc.html') as infile:
            self.dc = infile.read()
        dc = self._p.depth_charts(self.dc, '20170221')
        self.assertGreaterEqual(len(dc), 0)
        logging.info(dc)

    def test_draft_rankings_overall(self):
        with open('data/fantasypros-consensus-cheatsheets.html') as infile:
            content = infile.read()
        players = self._p.draft_rankings_overall(content)
        self.assertIsNotNone(players)
        self.assertTrue(random.choice(players).has_key('source_player_id'))
        logging.info(random.choice(players))

    def test_draft_rankings_position(self):
        with open('data/fantasypros-cheatsheets.html') as infile:
            content = infile.read()
        players = self._p.draft_rankings_position(content)
        self.assertIsNotNone(players)
        self.assertTrue(random.choice(players).has_key('source_player_id'))
        logging.info(random.choice(players))

    def test_projections(self):
        with open('data/fantasypros-projections.html') as infile:
            content = infile.read()
        players = self._p.projections(content, 'qb')
        self.assertIsNotNone(players)
        self.assertTrue(random.choice(players).has_key('source_player_id'))
        logging.info(random.choice(players))

    def test_weekly_rankings(self):
        with open('data/fantasypros-weekly.html') as infile:
            content = infile.read()
        players = self._p.weekly_rankings(content)
        self.assertIsNotNone(players)
        self.assertTrue(random.choice(players).has_key('source_player_id'))
        logging.info(random.choice(players))

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()