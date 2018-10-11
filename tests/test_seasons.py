# -*- coding: utf-8 -*-
# tests/test_dates.py
# tests for nfl.dates module

import datetime
import logging
import random
import sys
import unittest

import nfl.dates as nd


class Dates_test(unittest.TestCase):

    @property
    def dates(self):
        _dates = ('2018-10-01', '10/1/2018', '1-2-2018')
        return random.choice(_dates)

    @property
    def sites(self):
        _sites = ('fl', 'nfl', 'std', 'odd', 'db', 'bdy')
        return random.choice(_sites)

    @property
    def seas(self):
        return random.choice(range(2002, 2017))

    @property
    def week(self):
        return random.choice(range(1, 18))

    def test_convert_format(self):
        d = self.dates
        site = self.sites
        self.assertIsNotNone(nd.convert_format(d, site))

    def test_date_list(self):
        d1 = '2018-01-21'
        d2 = '2018-01-12'
        dl = nd.date_list(d1, d2)
        self.assertIsNotNone(dl)
        self.assertIsInstance(dl, list)

        d1 = datetime.datetime(2018, 1, 21)
        d2 = datetime.datetime(2018, 1, 12)
        dl = nd.date_list(d1, d2)
        self.assertIsNotNone(dl)
        self.assertIsInstance(dl, list)

        d1 = datetime.datetime(2018, 1, 21)
        d2 = datetime.datetime(2018, 1, 12)
        self.assertEqual(nd.date_list(d2, d1), [])

    def test_datetostr(self):
        d = datetime.datetime.now()
        s = self.sites
        self.assertIsNotNone(nd.datetostr(d, s))

        s = 'nfl'
        dstr = nd.datetostr(d, s)
        self.assertEqual(dstr[0:4], str(d.year))

    def test_format_type(self):
        d = self.dates
        self.assertIsNotNone(nd.format_type(d))
        d = '2018-01-01'
        self.assertEqual(nd.format_type(d), '%Y-%m-%d')
        d = '2018_1_2'
        self.assertIsNone(nd.format_type(d))

    def test_site_format(self):
        self.assertEqual('%m-%d-%Y', nd.site_format('std'))
        self.assertEqual('%Y-%m-%d', nd.site_format('nfl'))

    def test_strtodate(self):
        self.assertIsInstance(nd.strtodate(self.dates), datetime.datetime)

    def test_subtract_datestr(self):
        d1 = nd.datetostr(datetime.datetime.now(), 'nfl')
        d2 = self.dates
        self.assertGreaterEqual(nd.subtract_datestr(d1, d2), 0)


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()