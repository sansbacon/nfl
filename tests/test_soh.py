"""

tests/test_pp.py

"""

import logging
import random
import sys
import unittest

from nfl.soh import Scraper, Parser

logger = logging.getLogger()
logger.level = logging.INFO
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)


class TestSoh(unittest.TestCase):

    def setUp(self):
        self.s = Scraper()
        self.p = Parser()

    @property
    def seasons(self):
        return random.choice(list(range(2013, 2019)))

    def test_win_totals(self):
        seas = self.seasons
        response = self.s.win_totals(seas)
        win_totals = self.p.win_totals(response)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(win_totals, list)
        win_total = random.choice(win_totals)
        self.assertIsInstance(win_total, dict)
        self.assertTrue(bool(win_total))
        self.assertIn('team', win_total.keys())
        self.assertIsInstance(win_total['season_year'], int)
        self.assertIsInstance(win_total['over_odds'], int)
        self.assertIsInstance(win_total['under_odds'], int)
        logging.info(win_total)


if __name__ == '__main__':
    unittest.main()
