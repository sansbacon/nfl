# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import random
import sys
import unittest

from nfl.scrapers.betonline import BetOnlineNFLScraper
from nfl.parsers.betonline import BetOnlineNFLParser

class TestBetOnline(unittest.TestCase):


    def setUp(self):
        self.s = BetOnlineNFLScraper(cache_name='test-betonline')
        self.p = BetOnlineNFLParser()

    def test_lines(self):
        content = self.s.lines()
        self.assertIn('xml', content)
        lines = self.p.lines(content)
        self.assertIsNotNone(lines)

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()