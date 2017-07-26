# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import sys
import unittest

from nfl.scrapers.wayback import WaybackScraper


class Wayback_test(unittest.TestCase):
    '''
    '''
    def setUp(self):
        self.s = WaybackScraper()

    def test_get_wayback(self):
        url = 'http://www.google.com'
        content, ts = self.s.get_wayback(url)
        self.assertIsNotNone(content)
        self.assertIsNotNone(ts)


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
