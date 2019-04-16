# -*- coding: utf-8 -*-
# tests/test_xref.py
# tests for nfl.xref module

import logging
import sys
import unittest

import nfl.xref as nx
from nflmisc.nflpg import getdb


class Xref_test(unittest.TestCase):

    def setUp(self):
        db = getdb('nfl')
        self.nfl = nx.NFL(db)
        self.pff = nx.PFF(db)

    @unittest.skip
    def test_pff_add_xref(self):
        pass

    def test_pff_get_mfld(self):
        self.assertIsInstance(self.pff.get_mfld(), dict)
        self.assertIsInstance(self.pff.get_mfld('mfl'), dict)
        self.assertIsInstance(self.pff.get_mfld('pff'), dict)
        self.assertIsInstance(self.pff.get_mfld('RANDO'), dict)

    def test_pff_get_players(self):
        self.assertIsInstance(self.pff.get_players(), list)

    def test_pff_get_playersd(self):
        self.assertIsInstance(self.pff.get_playersd('name'), dict)
        self.assertIsInstance(self.pff.get_playersd('namepos'), dict)
        with self.assertRaises(ValueError):
            self.pff.get_playersd('ERR')

    @unittest.skip
    def test_pff_match_mfl(self):
        l = [{'a': 1}, {'b': 2}]
        self.assertIsInstance(self.pff.match_mfl(l, 'id', 'name', 'pos'), list)

    @unittest.skip
    def test_nfl_add_xref(self):
        pass

    def test_nfl_get_mfld(self):
        self.assertIsInstance(self.nfl.get_mfld(), dict)
        self.assertIsInstance(self.nfl.get_mfld('mfl'), dict)
        self.assertIsInstance(self.nfl.get_mfld('nfl'), dict)
        self.assertIsInstance(self.nfl.get_mfld('RANDO'), dict)

    def test_nfl_get_players(self):
        self.assertIsInstance(self.nfl.get_players(), list)

    def test_nfl_get_playersd(self):
        self.assertIsInstance(self.nfl.get_playersd('name'), dict)
        self.assertIsInstance(self.nfl.get_playersd('namepos'), dict)
        with self.assertRaises(ValueError):
            self.nfl.get_playersd('ERR')

    @unittest.skip
    def test_nfl_match_mfl(self):
        l = [{'a': 1}, {'b': 2}]
        self.assertIsInstance(self.nfl.match_mfl(l, 'id', 'name', 'pos'), list)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
