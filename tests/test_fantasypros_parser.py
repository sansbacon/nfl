from __future__ import absolute_import, print_function

import logging
import sys
import unittest

from nfl.parsers.fantasypros import FantasyProsNFLParser


class Fantasypros_parser_test(unittest.TestCase):

    def setUp(self):
        self.parser = FantasyProsNFLParser()
        with open ('files/fantasypros-dc.html') as infile:
            self.content = infile.read()

    def test_depth_chart(self):
        dc = self.parser.depth_charts(self.content, '20170221')
        self.assertGreaterEqual(len(dc), 0)
        logging.info(dc)


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()