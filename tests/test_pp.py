"""

tests/test_pp.py

"""

import logging
import random
import sys
import unittest

from nflmisc.nflpg import getdb
from nfl.pp import Scraper, Parser, Agent, Xref
from playermatcher import Site


logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


class TestPlayerProfiler(unittest.TestCase):

    def setUp(self):
        self.s = Scraper()
        self.p = Parser()

    def test_player_page(self):
        content = self.s.player_page('TT-0500')
        self.assertIsNotNone(content)
        data = content['data']['Player']
        self.assertIsInstance(data, dict)
        mh = self.p.player_medical_history(data)
        self.assertIsInstance(mh, list)
        gl = self.p.player_game_logs(data)
        self.assertIsInstance(gl, list)

    def test_players(self):
        data = self.s.players()
        self.assertIsNotNone(data)
        self.assertIsInstance(data, dict)

    def test_rankings(self):
        data = self.s.rankings()
        self.assertIsNotNone(data)
        self.assertIsInstance(data, dict)

    def test_xref_init(self):
        xr = Xref(None)
        self.assertIsInstance(xr, Site)

    def test_agent_init(self):
        a = Agent()
        self.assertIsInstance(a, Agent)
        self.assertIsInstance(a._s, Scraper)
        self.assertIsInstance(a._p, Parser)
        self.assertIsInstance(a._x, Xref)

    def test_agent_player_xref(self):
        db = getdb('nfl')
        a = Agent(db=db)
        players = a.player_xref()
        self.assertIsNotNone(players)
        #self.assertIsInstance(players, list)
        #self.assertIsInstance(random.choice(players), dict)
        logging.info(random.choice(players))


if __name__ == '__main__':
    unittest.main()
