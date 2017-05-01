from __future__ import absolute_import, print_function

import logging
import pprint
import sys
import unittest

from nba.parsers.realgm import RealgmNBAParser


class Realgm_parser_test(unittest.TestCase):

    def setUp(self):
        self.parser = RealgmNBAParser()
        with open ('files/realgm-dc.html') as infile:
            self.content = infile.read()

    def test_depth_chart(self):
        dc = self.parser.depth_charts(self.content, '20170221')
        self.assertGreaterEqual(len(dc), 0)
        logging.info(dc)


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()