# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import json
import logging
import random
import sys
import unittest

from nfl.scrapers.footballoutsiders import FootballOutsidersNFLScraper
from nfl.parsers.footballoutsiders import FootballOutsidersNFLParser
from nfl.player.fboxref import *
from nfl.player.playerxref import nfl_gsis_players
from nfl.utility import getdb, flatten_list

class FO_test(unittest.TestCase):

    @property
    def season(self):
        return random.choice(range(2010, 2017))

    def setUp(self):
        self.s = FootballOutsidersNFLScraper(cache_name='fo-test')
        self.p = FootballOutsidersNFLParser()
        self.db = getdb()

    @unittest.skip("skip")
    def test_fbo_gsis_players(self):
        self.assertIsNotNone(fbo_gsis_players(self.db))

    def test_fbo_gsis_xref(self):
        with open('/home/sansbacon/snapcounts.json', 'r') as f:
            sc = json.load(f)
        sc = flatten_list(sc)
        self.assertIsNotNone(sc)
        source_players = [p['player'] for p in sc]
        logging.info(source_players)
        self.assertIsNotNone(source_players)
        xref = fbo_gsis_xref(nfl_gsis_players(self.db), source_players)
        self.assertIsNotNone(xref)

    @unittest.skip("skip")
    def test_dl(self):
        seas = self.season
        content = self.s.dl()
        self.assertIsNotNone(content)
        content = self.s.dl(seas)
        self.assertIsNotNone(self.p.dl(content, seas))

    @unittest.skip("skip")
    def test_drive(self):
        content = self.s.drive(season=self.season, offdef='off')
        self.assertIsNotNone(self.p.drive(content=content, offdef='off'))

    @unittest.skip("skip")
    def test_ol(self):
        seas = self.season
        content = self.s.ol()
        self.assertIsNotNone(content)
        content = self.s.ol(seas)
        self.assertIsNotNone(self.p.ol(content, seas))

    @unittest.skip("skip")
    def test_qb(self):
        content = self.s.qb()
        self.assertIsNotNone(content)
        content = self.s.qb(season=self.season)
        self.assertIsNotNone(content)

    @unittest.skip("skip")
    def test_rb(self):
        content = self.s.rb()
        self.assertIsNotNone(content)
        content = self.s.rb(season=self.season)
        self.assertIsNotNone(content)

    @unittest.skip("skip")
    def test_te(self):
        content = self.s.te()
        self.assertIsNotNone(content)
        content = self.s.te(season=self.season)
        self.assertIsNotNone(content)

    @unittest.skip("skip")
    def test_wr(self):
        content = self.s.wr()
        self.assertIsNotNone(content)
        content = self.s.wr(season=self.season)
        self.assertIsNotNone(content)

    @unittest.skip("skip")
    def test_snap_counts(self):
        content = self.s.snap_counts(self.season, 1)
        self.assertIsNotNone(content)
        self.assertIn('snap counts', content)

    @unittest.skip("skip")
    def test_team_defense(self):
        content = self.s.team_defense()
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)
        content = self.s.team_defense(season=self.season)
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)

    @unittest.skip("skip")
    def test_team_efficiency(self):
        content = self.s.team_efficiency()
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)
        content = self.s.team_efficiency(season=self.season)
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)

    @unittest.skip("skip")
    def test_team_offense(self):
        content = self.s.team_offense()
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)
        content = self.s.team_offense(season=self.season)
        self.assertIsNotNone(content)
        self.assertIn('DVOA', content)

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()