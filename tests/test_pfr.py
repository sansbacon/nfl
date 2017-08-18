# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
from string import ascii_uppercase
import random
import sys
import unittest

from nfl.scrapers.pfr import PfrNFLScraper
from nfl.parsers.pfr import PfrNFLParser


class Pfr_test(unittest.TestCase):

    @property
    def last_initial(self):
        return random.choice(ascii_uppercase)

    @property
    def offset(self):
        return random.choice(range(0, 100, 200))

    @property
    def player(self):
        ids = ['PalmCa00', 'BreeDr00', 'RodgAa00', 'CousKi00', 'StafMa00', 'RivePh00',
               'TaylTy00', 'CarrDe02', 'SmitAl03', 'BrowAn04', 'DaltAn00', 'FreeDe00',
               'JoneJu02', 'RyanMa00', 'RoetBe00', 'PeteAd01', 'MarsBr00']
        return random.choice(ids)

    @property
    def seas(self):
        return random.choice(range(2002, 2017))

    @property
    def week(self):
        return random.choice(range(1, 18))

    def setUp(self):
        self.s = PfrNFLScraper(cache_name='pfr-plays-query')
        self.p = PfrNFLParser()

    def test_team_plays_query(self):
        content = self.s.team_plays_query(season_start=2016, season_end=2016, offset=0)
        self.assertIsNotNone(content)
        self.assertRegexpMatches(content, r'html')

    def test_draft(self):
        content = self.s.draft(self.seas)
        self.assertIsNotNone(content)
        players = self.p.draft(content, self.seas)
        self.assertIsNotNone(players)
        player = random.choice(players)
        self.assertIn('draft_year', player.keys())

    def test_fantasy_season(self):
        content = self.s.fantasy_season(self.seas)
        self.assertIsNotNone(content)
        self.assertIn('Bell', content)

    def test_fantasy_week(self):
        content = self.s.fantasy_week(self.seas, 9)
        self.assertIsNotNone(content)
        self.assertIn('Bell', content)

    def test_players(self):
        content = self.s.players(self.last_initial)
        self.assertIsNotNone(content)

    def test_playerstats_fantasy_weekly(self):
        content = self.s.playerstats_fantasy_weekly(self.seas, self.week, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_fantasy_yearly(self):
        content = self.s.playerstats_fantasy_yearly(self.seas, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_player_fantasy_year(self):
        content = self.s.player_fantasy_year(self.seas, self.player)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_offense_weekly(self):
        content = self.s.playerstats_offense_weekly(self.seas, self.week, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_offense_yearly(self):
        content = self.s.playerstats_offense_yearly(self.seas, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_passing_weekly(self):
        content = self.s.playerstats_offense_weekly(self.seas, self.week, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_passing_yearly(self):
        content = self.s.playerstats_passing_yearly(self.seas, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_receiving_weekly(self):
        content = self.s.playerstats_receiving_weekly(self.seas, self.week, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_receiving_yearly(self):
        content = self.s.playerstats_receiving_yearly(self.seas, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_rushing_weekly(self):
        content = self.s.playerstats_rushing_weekly(self.seas, self.week, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_rushing_yearly(self):
        content = self.s.playerstats_rushing_yearly(self.seas, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_players(self):
        content = self.s.players(self.last_initial)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_team_plays_query(self):
        ## (self, season_start, season_end, offset):
        season = self.seas
        content = self.s.team_plays_query(season, season, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_team_passing_weekly(self):
        season = self.seas
        content = self.s.team_passing_weekly(season, season, self.week)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_team_defense_yearly(self):
        content = self.s.team_passing_weekly(self.season)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_team_defense_weekly(self):
        season = self.seas
        content = self.s.team_defense_weekly(season, season, self.week)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_team_offense_weekly(self):
        season = self.seas
        content = self.s.team_offense_weekly(season, season, self.week)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()