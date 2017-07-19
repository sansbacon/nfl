# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import sys
import unittest

from nfl.scrapers.footballoutsiders import FootballOutsidersNFLScraper
from nfl.parsers.footballoutsiders import FootballOutsidersNFLParser


class FO_test(unittest.TestCase):

    def setUp(self):
        self.s = FootballOutsidersNFLScraper(cache_name='fo-test')
        self.p = FootballOutsidersNFLParser()


    def test_dvoa_table(self):
        content = self.s.dvoa_table('')
        self.assertIsNotNone(content)
        self.assertRegexpMatches(content, r'html')
        logging.info('test')

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()