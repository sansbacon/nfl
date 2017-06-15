from __future__ import absolute_import, print_function

import logging
import random
import sys
import unittest

from nfl.parsers.fantasydata import FantasyDataNFLParser


logger = logging.getLogger()
logger.level = logging.DEBUG


class Fantasydata_test(unittest.TestCase):
    '''
    Tests nfldotcom scraper and parser
    '''

    def setUp(self):
        self.p = FantasyDataNFLParser()
        self.stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(self.stream_handler)

    def tearDown(self):
        logger.removeHandler(self.stream_handler)

    def test_dst(self):
        with open('data/DST.html', 'r') as infile:
            content = infile.read()
        results = self.p.dst(content, season=2002, week=1)
        logger.info(results)
        self.assertIsNotNone(results)


if __name__=='__main__':
    unittest.main()
