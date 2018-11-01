# -*- coding: utf-8 -*-

import logging
import random
import sys
import unittest
from string import ascii_uppercase

import nfl.nflcom as nc

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class Nflcom_test(unittest.TestCase):
    '''
    Tests nfldotcom scraper and parser
    '''

    @property
    def gsis_id(self):
        vals = ["2015090365", "2009101809", "2013120103", "2016100904", "2015092712",
                "2009100410", "2014080705", "2012092311", "2011112800", "2012120906",
                "2011103009", "2010091906", "2013112407", "2013082404", "2014110902",
                "2012101100", "2016010307", "2009101111", "2014091402", "2016090151"]
        return random.choice(vals)

    @property
    def letter(self):
        x = None
        while not x:
            l = random.choice(ascii_uppercase)
            if l not in ['x', 'y', 'z', 'v']:
                x = l
        return x

    @property
    def profile_id(self):
        vals = ['2495143']
        return random.choice(vals)

    @property
    def season(self):
        return random.choice(range(2009, 2017))

    @property
    def week(self):
        return random.choice(range(1, 18))

    def setUp(self):
        self.s = nc.Scraper(cache_name='test-nfldotcom-scraper')
        self.p = nc.Parser()
        self.a = nc.Agent(scraper=self.s, parser=self.p)
        self.all_games = []

    def test_game(self):
        self.assertIsNotNone(self.s.game(self.gsis_id))

    def test_gamebook(self):
        self.assertIsNotNone(self.s.gamebook(2016, 1, 56905))

    def test_injuries(self):
        self.assertIsNotNone(self.s.injuries(self.week))

    def test_ol(self):
        self.assertIsNotNone(self.s.ol(self.season))

    def test_player_profile(self):
        profile_path = 'andydalton/2495143'
        content = self.s.player_profile(profile_path=profile_path)
        self.assertIsNotNone(content)

    def test_schedule_week(self):
        self.assertIsNotNone(self.s.schedule_week(self.season, self.week))

    def test_score_week(self):
        self.assertIsNotNone(self.s.score_week(self.season, self.week))

    @unittest.skip
    def test_players(self):
        content = self.s.players(self.letter)
        self.assertIsNotNone(self.p.players(content))

    def test_player_search_name(self):
        content = self.s.player_search_name('Andy Dalton', 'current')
        self.assertIsNotNone(self.p.player_search_name(content))


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    unittest.main()
