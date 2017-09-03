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
        self.assertIn('body', content)

    def test_get_json(self):
        url = 'https://jsonplaceholder.typicode.com/posts'
        content = self.s.get_json(url)
        self.assertIsNotNone(content)
        self.assertIsInstance(content, list)

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()