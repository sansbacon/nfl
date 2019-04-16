import logging
import sys
import unittest

import nfl.watson as nw

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class Watson_test(unittest.TestCase):
    '''
    Tests nfldotcom scraper and parser
    '''

    def setUp(self):
        self.s = nw.Scraper(cache_name='test-watson-scraper')
        self.p = nw.Parser()

    def test_players(self):
        content = self.s.players(season_year=2018)
        players = self.p.players(content)
        self.assertGreater(len(players), 0)
        logging.info(players[0])

    def test_weekly_projection(self):
        pid = 18306
        content = self.s.weekly_projection(season_year=2018, pid=pid)
        projection = self.p.weekly_projection(content)
        self.assertIsInstance(projection, list)
        self.assertIsInstance(projection[0], dict)

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    unittest.main()
