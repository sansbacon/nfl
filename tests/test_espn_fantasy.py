# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import json
import logging
import os
import sys
import unittest

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

from nfl.scrapers.espn_fantasy import ESPNFantasyScraper
from nfl.parsers.espn_fantasy import ESPNFantasyParser


class ESPN_fantasy_test(unittest.TestCase):
    '''
    Tests espn_fantasy scraper and parser
    '''

    def setUp(self):
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(os.path.expanduser('~'), '.fantasy'))
        self.s = ESPNFantasyScraper(config=self.config, visible=True, profile='/home/sansbacon/.mozilla/firefox/6h98gbaj.default')
        self.p = ESPNFantasyParser()
        self.leagueId = 483232
        self.teamId = 7
        self.seasonId = 2017

    def test_waiver_wire(self):
        content = self.s.fantasy_waiver_wire(self.leagueId, self.teamId, self.seasonId)
        self.assertIsNotNone(content)
        self.assertIn('/ffl/freeagency?', content)
        players = self.p.fantasy_waiver_wire(content)
        self.assertIsNotNone(players)

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
