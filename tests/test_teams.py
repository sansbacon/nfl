# -*- coding: utf-8 -*-
# tests/test_teams.py
# tests for nfl.teams module

import logging
import random
import sys
import unittest

import nfl.teams as nt


class Teams_test(unittest.TestCase):

    @property
    def city(self):
        return random.choice(('Chicago', 'Arizona'))

    @property
    def code(self):
        return random.choice(('CHI', 'WAS'))

    @property
    def long(self):
        return random.choice(('Chicago Bears', 'Tennessee Titans'))

    @property
    def nickname(self):
        return random.choice(('Bears', 'Titans'))

    def test_city_to_code(self):
        self.assertIsNotNone(nt.city_to_code(self.city))
        self.assertIsNone(nt.city_to_code('ZAM'))

    def test_long_to_code(self):
        self.assertIsNotNone(nt.long_to_code(self.long))
        self.assertIsNone(nt.long_to_code('ZAM'))

    def test_nickname_to_code(self):
        self.assertIsNotNone(nt.nickname_to_code(self.nickname))
        self.assertIsNone(nt.nickname_to_code('ZAM'))

    def test_from_nfl(self):
        self.assertIsNotNone(nt.from_nfl('CHI', 'rg'))

    def test_to_nfl(self):
        self.assertIsNotNone(nt.to_nfl('CHI', 'rg'))

    def test_espn_teams(self):
        self.assertIn('chi', nt.espn_teams())


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
