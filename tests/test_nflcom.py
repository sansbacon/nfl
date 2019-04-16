# -*- coding: utf-8 -*-

import logging
import random
import sys
import unittest
from string import ascii_uppercase

from requests import Response

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
        content = self.s.game(self.gsis_id)
        self.assertIsNotNone(content)
        game = self.p.game_page(content)
        self.assertIsNotNone(game)

    def test_gamebook(self):
        content = self.s.gamebook(2016, 1, 56905)
        self.assertIsNotNone(content)
        self.assertIn('Gamebook', content)

    def test_injuries(self):
        season = self.season
        week = self.week
        content = self.s.injuries(week)
        self.assertIsNotNone(content)
        injuries = self.p.injuries(content, season, week)
        self.assertIsNotNone(injuries)

    def test_ol(self):
        content = self.s.ol(self.season)
        self.assertIsNotNone(content)
        ol = self.p.ol(content)
        self.assertIsInstance(ol, list)

    def test_player_profile(self):
        profile_path = 'andydalton/2495143'
        player_id, profile_id = profile_path.split('/')
        content = self.s.player_profile(profile_path=profile_path)
        self.assertIn(profile_path, content)
        player = self.p.player_page(content, profile_id)
        self.assertIsInstance(player, dict)

    def test_player_search_name(self):
        pname = 'Dalton, Andy'
        profile_path = 'andydalton/2495143'
        pid, prid = profile_path.split('/')
        search_result = self.s.player_search_name(pname)
        name, player_id, profile_id = self.p.player_search_name(search_result)[0]
        self.assertEqual(name, pname)
        self.assertEqual(pid, player_id)
        self.assertEqual(prid, profile_id)

    def test_player_search_web(self):
        name = 'Andy Dalton'
        profile_path = 'andydalton/2495143'
        player_id, profile_id = profile_path.split('/')
        search_result = self.s.player_search_web(name)
        self.assertIn(profile_path, search_result)
        content = self.s.get(search_result)
        player = self.p.player_page(content, profile_id)
        self.assertIsInstance(player, dict)

    def test_players(self):
        response = self.s.players(self.letter)
        self.assertIsInstance(response, Response)
        players = self.p.players(response)
        self.assertIsInstance(players, list)

    def test_schedule_week(self):
        self.assertIsNotNone(self.s.schedule_week(self.season, self.week))

    def test_score_week(self):
        self.assertIsNotNone(self.s.score_week(self.season, self.week))


if __name__ == '__main__':
    #logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    unittest.main()
