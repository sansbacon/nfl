# -*- coding: utf-8 -*-
# tests/test_dates.py
# tests for nfl.dates module

import datetime
import logging
import random
import sys
import unittest

import nfl.seasons as ns


class Seasons_test(unittest.TestCase):

    @property
    def seas(self):
        return random.choice(range(2009, 2017))

    @property
    def week(self):
        return random.choice(range(1, 18))

    def test_all_seasons(self):
        seas = ns.all_seasons()
        self.assertIsInstance(seas, dict)
        self.assertIn(self.seas, seas.keys())

    def test_current_season_year(self):
        y = ns.current_season_year()
        self.assertLessEqual(y, datetime.datetime.now().year)

    def test_fantasylabs_week(self):
        y = self.seas
        w = self.week
        self.assertIsNotNone(ns.fantasylabs_week(y, w))
        self.assertIn('-', ns.fantasylabs_week(y, w))

    def test_get_season(self):
        s = ns.get_season(self.seas)
        self.assertIsInstance(s, dict)

    def test_season_week(self):
        d = datetime.datetime.now().date()
        self.assertIsInstance(ns.season_week(d), dict)

        d = datetime.datetime(2018, 10, 13).date()
        sw = ns.season_week(d)
        self.assertEqual(sw['season'], 2018)
        self.assertEqual(sw['week'], 6)

        d = datetime.datetime(2018, 1, 1).date()
        sw = ns.season_week(d)
        self.assertEqual(sw['season'], 2017)
        self.assertEqual(sw['week'], 17)

    def test_week_end(self):
        y = self.seas
        w = self.week
        self.assertIsInstance(ns.week_end(y, w), datetime.date)

        y = 2018
        w = 5
        self.assertLess(ns.week_end(y, w), datetime.datetime.now().date())

    def test_week_start(self):
        y = self.seas
        w = self.week
        self.assertIsInstance(ns.week_start(y, w), datetime.date)

        y = 2018
        w = 5
        self.assertLess(ns.week_start(y, w), datetime.datetime.now().date())


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()