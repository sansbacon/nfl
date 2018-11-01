# -*- coding: utf-8 -*-

import logging
import random
import sys
import unittest

import nfl.espn as ne
from nfl.teams import espn_teams

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


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
        return random.choice(['qb', 'rb', 'wr', 'te'])

    @property
    def season(self):
        return random.choice([2018])

    @property
    def team(self):
        return random.choice(espn_teams())

    def setUp(self):
        self.s = ne.Scraper(cache_name='test-espn-scraper')
        self.p = ne.Parser()

    def test_adp(self):
        pos = self.pos
        content = self.s.adp(pos)
        self.assertIn('Live Draft Results', content)
        players = self.p.adp(content)
        self.assertIsNotNone(players)
        self.assertGreaterEqual(len(players), 10)

    def test_players_position(self):
        pos = self.pos
        content = self.s.players_position(pos)
        self.assertIn('NFL Players By Position', content)
        players = self.p.players_position(content, pos)
        self.assertIsNotNone(players)
        self.assertIsInstance(players, list)

    def test_projections(self):
        content = self.s.projections(self.pos, self.season)
        self.assertIn('PLAYERS', content)
        pos = self.pos
        content = self.s.projections(pos, season_year=self.season, offset=self.offset(pos))
        self.assertIn('PLAYERS', content)
        players = self.p.projections(content, pos)
        self.assertIsNotNone(players)
        self.assertIsInstance(players, list)

    def test_team_roster(self):
        content = self.s.team_roster(self.team)
        self.assertIn('Roster', content)
        players = self.p.team_roster(content)
        self.assertIsNotNone(players)
        self.assertIsInstance(players, list)

    def test_fantasy_players_team(self):
        tm = self.team
        content = self.s.fantasy_players_team(random.randint(1, 32))
        self.assertIsNotNone(content)
        self.assertIsNotNone(self.p.fantasy_players_team(content))

    def test_watson(self):
        pid = 14012
        content = self.s.watson(pid)
        self.assertIsInstance(self.p.watson(content), dict)

    def test_watson_players(self):
        content = self.s.watson_players()
        self.assertGreater(len(self.p.watson_players(content)), 0)

    def test_weekly_scoring(self):
        content = self.s.weekly_scoring(self.season, 1, self.pos)
        self.assertIsInstance(self.p.weekly_scoring(content), list)

    def test_weekly_scoring_dst(self):
        content = self.s.weekly_scoring(self.season, 1, 'dst')
        self.assertIsInstance(self.p.weekly_scoring_dst(content), list)

    def test_weekly_scoring_k(self):
        content = self.s.weekly_scoring(self.season, 1, 'k')
        self.assertIsInstance(self.p.weekly_scoring_k(content), list)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    unittest.main()
