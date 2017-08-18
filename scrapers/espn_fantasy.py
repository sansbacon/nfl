# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging

from nfl.scrapers.browser import BrowserScraper


class ESPNFantasyScraper(BrowserScraper):
    '''
    '''

    def __init__(self, config, visible=False, profile=None):
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        BrowserScraper.__init__(self, visible=visible, profile=profile)
        self.user = config.get('espn', 'username')
        self.password = config.get('espn', 'password')

    def fantasy_league_rosters(self, league_id):
        '''
        Gets roster for team in ESPN fantasy league
        '''
        url = 'http://games.espn.com/ffl/leaguerosters'
        params = {'leagueId': league_id}

        try:
            from urllib.parse import urlparse, urlencode
        except ImportError:
            from urlparse import urlparse

        url = '{}?{}'.format(url, urlencode(params))
        driver = self.browser
        driver.get(url)
        self.urls.append(url)
        return self.browser.page_source

    def fantasy_team_roster(self, league_id, team_id, season):
        '''
        Gets roster for team in ESPN fantasy league
        '''
        url = 'http://games.espn.com/ffl/clubhouse'
        params = {'leagueId': league_id,
                      'teamId': team_id,
                      'seasonId': season}

        try:
            from urllib.parse import urlparse, urlencode
        except ImportError:
            from urlparse import urlparse

        url = '{}?{}'.format(url, urlencode(params))
        driver = self.browser
        driver.get(url)
        self.urls.append(url)
        return self.browser.page_source

    def fantasy_projections(self, offset=0):
        '''
        Gets ESPN fantasy football projections
        '''
        url = 'http://games.espn.go.com/ffl/tools/projections?'
        params = {'startIndex': offset}
        return self.get(url, payload=params)

    def fantasy_waiver_wire(self, league_id, team_id, season, start_index=None, position=None):
        '''
        Gets waiver wire from ESPN fantasy league
        league_id=488173, team_id=12, season=2017
        '''

        slot_categories = {
            'qb': 0,
            'rb': 2,
            'wr': 4,
            'te': 6,
            'dst': 16,
            'k': 17
        }

        params = {'leagueId': league_id, 'teamId': team_id, 'seasonId': season}

        if start_index:
            if start_index not in [0, 50, 100, 150, 200]:
                raise ValueError('start index invalid: {}'.format(start_index))
            params['startIndex'] = start_index

        if position:
            params['slotCategoryId'] = slot_categories[position.lower()]

        try:
            from urllib.parse import urlencode
        except ImportError:
            from urllib import urlencode

        url = 'http://games.espn.com/ffl/freeagency?' + urlencode(params)
        self.browser.get(url)
        self.urls.append(url)
        return self.browser.page_source

if __name__ == "__main__":
    pass
