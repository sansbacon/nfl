# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import sys
import unittest

from nfl.scrapers.browser import BrowserScraper


class Browser_test(unittest.TestCase):

    def setUp(self):
        self.s = BrowserScraper()


    def test_get(self):
        url = 'http://www.google.com'
        content = self.s.get(url)
        self.assertIsNotNone(content)

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()