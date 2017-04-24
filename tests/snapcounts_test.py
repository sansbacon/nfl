'''
snapcounts_test.py
'''

import unittest

import browsercookie

from scrapers.footballoutsiders import FootballOutsidersNFLScraper
from parsers.fo import FootballOutsidersNFLParser


class TestSnapcounts(unittest.TestCase):

    
    def setUp(self):
        self.s = FootballOutsidersNFLScraper(cache_name='test-odds',
                                             cookies=browsercookie.chrome())
        self.p = FootballOutsidersNFLParser()

    
    def testSnapCounts(self):
        for season in [2016]:
            for week in range(14,18):
                content = self.s.snap_counts(season, week)

if __name__ == '__main__':
    unittest.main()
