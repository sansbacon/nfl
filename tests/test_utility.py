# -*- coding: utf-8 -*-
# tests/test_utility.py
# tests for nfl.utility module

import logging
import random
import sys
import unittest

import nfl.utility as nu


class Utility_test(unittest.TestCase):

    @property
    def city(self):
        return random.choice(('Chicago', 'Arizona'))

    @property
    def code(self):
        return random.choice(('CHI', 'WAS'))

    def test_digits(self):
        tstr = 'abc123'
        self.assertEqual('123', nu.digits(tstr))

    def test_flatten(self):
        d = {'keys': {'joe': 1, 'tom': 2}, 'vals': 'val'}
        d2 = {'joe': 1, 'tom': 2, 'vals': 'val'}
        self.assertEqual(nu.flatten(d), d2)

    def test_flatten_list(self):
        l = [['joe', 'tom'], ['sam', 'bob']]
        l2 = ['joe', 'tom', 'sam', 'bob']
        self.assertEqual(nu.flatten_list(l), l2)

    def test_is_float(self):
        self.assertTrue(nu.isfloat(3.14))
        self.assertTrue(nu.isfloat('3.14'))
        self.assertFalse(nu.isfloat('x'))

    def test_is_int(self):
        self.assertFalse(nu.isint(3.14))
        self.assertTrue(nu.isint('3'))
        self.assertFalse(nu.isint('x'))

    def test_merge(self):
        lod = [{'a': 1}, {'b': 2}]
        self.assertEqual(nu.merge({}, lod), {'a': 1, 'b': 2})

    def test_merge_two(self):
        lod = [{'a': 1}, {'b': 2}]
        self.assertEqual(nu.merge_two(lod[0], lod[1]), {'a': 1, 'b': 2})

    def test_pair_list(self):
        l1 = [1, 2, 3, 4]
        l2 = [5, 6, 7, 8]
        self.assertIsNotNone(nu.pair_list([l1, l2]))

    def test_dict_to_qs(self):
        d = {'a': 1, 'b': 2}
        self.assertEqual(nu.dict_to_qs(d), 'a=1&b=2')

    def test_qs_to_dict(self):
        qs = 'https://www.google.com?a=1&b=2'
        d = {'a': ['1'], 'b': ['2']}
        self.assertEqual(nu.qs_to_dict(qs), d)

    def test_sample_dict(self):
        d = {'a': 1, 'b': 2}
        self.assertIsInstance(nu.sample_dict(d, 1), dict)
        self.assertIsInstance(nu.sample_dict(d, 2), dict)

    def test_url_quote(self):
        s = 'Joe Smith'
        self.assertEqual(nu.url_quote(s), 'Joe%20Smith')
        s = '$20'
        self.assertEqual(nu.url_quote(s), '%2420')


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
