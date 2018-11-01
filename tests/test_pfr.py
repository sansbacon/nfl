# -*- coding: utf-8 -*-

import logging
import random
import sys
import unittest
from string import ascii_uppercase

import nfl.pfr as pfr


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
        self.s = pfr.Scraper(cache_name='pfr-plays-query')
        self.p = pfr.Parser()

    def test_team_plays_query(self):
        content = self.s.team_plays_query(season_start=2016, season_end=2016, offset=0)
        self.assertNotIn('404 error', content)
        self.assertRegexpMatches(content, r'html')

    def test_draft(self):
        content = self.s.draft(self.seas)
        self.assertNotIn('404 error', content)
        players = self.p.draft(content, self.seas)
        self.assertIsNotNone(players)
        player = random.choice(players)
        self.assertIn('draft_year', player.keys())

    def test_players(self):
        content = self.s.players(self.last_initial)
        self.assertGreater(len(self.p.players(content)), 0)
        self.assertNotIn('404 error', content)

    def test_player_fantasy_season(self):
        content = self.s.player_fantasy_season(self.seas, self.player)
        self.assertIsNotNone(self.p.player_fantasy_season(content))
        self.assertNotIn('404 error', content)

    def test_playerstats_fantasy_weekly(self):
        content = self.s.playerstats_fantasy_weekly(self.seas, self.week, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_playerstats_fantasy_yearly(self):
        content = self.s.playerstats_fantasy_yearly(self.seas, self.offset)
        self.assertIsNotNone(content)
        self.assertNotIn('404 error', content)

    def test_player_fantasy_year(self):
        content = self.s.player_fantasy_season(self.seas, self.player)
        self.assertIsNotNone(self.p.player_fantasy_season(content))
        self.assertNotIn('404 error', content)

    def test_playerstats_offense_weekly(self):
        content = self.s.playerstats_offense_weekly(self.seas, self.week, self.offset)
        self.assertGreater(len(self.p.playerstats_offense_weekly(content)), 0)
        self.assertNotIn('404 error', content)

    def test_playerstats_offense_yearly(self):
        content = self.s.playerstats_offense_yearly(self.seas, self.offset)
        self.assertGreater(len(self.p.playerstats_offense_yearly(content)), 0)
        self.assertNotIn('404 error', content)

    def test_playerstats_passing_weekly(self):
        content = self.s.playerstats_passing_weekly(self.seas, self.week, self.offset)
        self.assertGreater(len(self.p.playerstats_offense_weekly(content)), 0)
        self.assertNotIn('404 error', content)

    @unittest.skip
    def test_playerstats_passing_yearly(self):
        # TODO: this test is not passing
        content = self.s.playerstats_passing_yearly(self.seas, self.offset)
        self.assertGreater(len(self.p.playerstats_offense_yearly(content)), 0)
        self.assertNotIn('404 error', content)

    def test_playerstats_receiving_weekly(self):
        content = self.s.playerstats_receiving_weekly(self.seas, self.week, self.offset)
        self.assertGreater(len(self.p.playerstats_offense_weekly(content)), 0)
        self.assertNotIn('404 error', content)

    @unittest.skip
    def test_playerstats_receiving_yearly(self):
        # TODO: this test is not passing
        content = self.s.playerstats_receiving_yearly(self.seas, self.offset)
        self.assertGreater(len(self.p.playerstats_offense_yearly(content)), 0)
        self.assertNotIn('404 error', content)

    @unittest.skip
    def test_playerstats_rushing_weekly(self):
        # TODO: this test is not passing
        content = self.s.playerstats_rushing_weekly(self.seas, self.week, self.offset)
        self.assertGreater(len(self.p.playerstats_offense_weekly(content)), 0)
        self.assertNotIn('404 error', content)

    @unittest.skip
    def test_playerstats_rushing_yearly(self):
        # TODO: this test is not passing
        content = self.s.playerstats_rushing_yearly(self.seas, self.offset)
        self.assertGreater(content)
        self.assertNotIn('404 error', content)

    def test_team_plays_query(self):
        season = self.seas
        content = self.s.team_plays_query(season, season, self.offset)
        self.assertGreater(len(self.p.team_plays(content)), 0)
        self.assertNotIn('404 error', content)

    @unittest.skip
    def test_team_passing_weekly(self):
        # TODO: this test is not passing
        season = self.seas
        content = self.s.team_passing_weekly(season, season, self.week)
        self.assertGreater(len(self.p.team_offense_weekly(content)), 0)
        self.assertNotIn('404 error', content)

    def test_team_defense_yearly(self):
        sy = self.seas
        content = self.s.team_defense_yearly(sy)
        self.assertGreater(len(self.p.team_defense_yearly(content, sy)), 0)
        self.assertNotIn('404 error', content)

    def test_team_defense_weekly(self):
        season = self.seas
        content = self.s.team_defense_weekly(season, season, self.week)
        self.assertGreater(len(self.p.team_defense_weekly(content)), 0)
        self.assertNotIn('404 error', content)

    def test_team_offense_weekly(self):
        season = self.seas
        content = self.s.team_offense_weekly(season, season, self.week)
        self.assertGreater(len(self.p.team_offense_weekly(content)), 0)
        self.assertNotIn('404 error', content)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
