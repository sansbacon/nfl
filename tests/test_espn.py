# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.scrapers.espn import ESPNNFLScraper
from nfl.parsers.espn import ESPNNFLParser
from nfl.teams import espn_teams


class ESPN_test(unittest.TestCase):
    '''
    Tests nfldotcom scraper and parser
    '''
    def offset(self, pos):
        if pos == 'k':
            return 0
        elif pos in ['qb', 'te']:
            return random.choice([0, 40])
        else:
            return random.choice([0, 40, 80])

    @property
    def pos(self):
        return random.choice(['qb', 'rb', 'wr', 'k', 'te'])

    @property
    def team(self):
        return random.choice(espn_teams())

    def setUp(self):
        self.s = ESPNNFLScraper(cache_name='test-espn-scraper')
        self.p = ESPNNFLParser()

    def test_adp(self):
        pos = self.pos
        content = self.s.adp(pos)
        self.assertIn('Live Draft Results', content)
        players = self.p.adp(content)
        self.assertIsNotNone(players)
        self.assertGreaterEqual(len(players), 10)

    '''
    def test_players_position(self):
        pos = self.pos
        content = self.s.players_position(pos)
        self.assertIn('NFL Players By Position', content)
        players = self.p.players_position(content, pos)
        self.assertIsNotNone(players)
        self.assertIsInstance(players, list)

    def test_projections(self):
        content = self.s.projections(self.pos)
        self.assertIn('PLAYERS', content)
        pos = self.pos
        content = self.s.projections(pos, offset=self.offset(pos))
        self.assertIn('PLAYERS', content)
        self.assertRaises(ValueError, lambda: self.s.projections('nyk', 40))
        self.assertRaises(ValueError, lambda: self.s.projections(pos, 500))
        players = self.p.projections(content, pos)
        self.assertIsNotNone(players)
        self.assertIsInstance(players, list)

    def test_team_roster(self):
        content = self.s.team_roster(self.team)
        self.assertIn('Roster', content)
        players = self.p.team_roster(content)
        self.assertIsNotNone(players)
        self.assertIsInstance(players, list)
    '''

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
