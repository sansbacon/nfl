# -*- coding: utf-8 -*-

import logging
import random
import sys
import unittest

from nfl.tgf import TeamGameFinder


class Tgf_test(unittest.TestCase):

    def setUp(self):
        self.tgf = TeamGameFinder()

    def test_help_load(self):
        msg = self.tgf.help_load()
        self.assertIsNotNone(msg)

    def test_conv_col(self):
        self.assertIsInstance(self.tgf._conv_col(1.0), float)
        self.assertEqual(self.tgf._conv_col('x'), 0.0)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
