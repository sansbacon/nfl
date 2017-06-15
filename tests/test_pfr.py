from __future__ import absolute_import, print_function, division

import logging
import sys
import unittest

from nfl.scrapers.pfr import PfrNFLScraper
from nfl.parsers.pfr import PfrNFLParser


class Pfr_test(unittest.TestCase):

    def setUp(self):
        self.s = PfrNFLScraper(cache_name='pfr-plays-query')
        self.p = PfrNFLParser()


    def test_team_plays_query(self):
        content = self.s.team_plays_query(season_start=2009, season_end=2016, offset=0)
        self.assertIsNotNone(content)
        self.assertRegexpMatches(content, r'html')
        teams = self.p.team_plays(content)
        self.assertIsNotNone(teams)
        logging.info(teams)


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()

    '''
    import json
    import os
    import pprint
    import random
    import time

    teams = []
    offset = 0
    season_min = 2009
    season_max = 2016

    results_per_season = 512
    seasons = season_max - season_min + 1

    s = PfrNFLScraper(cache_name='pfr-plays-query')
    p = PfrNFLParser()

    while offset < results_per_season * seasons:
        content = s.team_plays_query(season_start=2009, season_end=2016, offset=offset)
        team = p.team_plays(content)
        teams.append(team)
        offset += 100
        time.sleep(random.randint(2,5))
        logging.info('finished {}'.format(offset))


    with open(os.path.join(os.path.expanduser('~'), 'teamplays.json'), 'wb') as outfile:
        json.dump([item for sublist in teams for item in sublist], outfile)

    pprint.pprint(teams)
    '''