# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import time

from nfl.scrapers.scraper import FootballScraper


class ESPNNFLScraper(FootballScraper):
    '''

    '''

    def fantasy_league_roster(self, season, league_id, team_id):
        '''
        Gets roster for team in ESPN fantasy league
        '''
        url = 'http://games.espn.com/ffl/clubhouse?'
        params = {'leagueId': league_id,
                      'teamId': team_id,
                      'seasonId': season}
        return self.get(url, payload=params)

    def nfl_team_roster(self, team_code):
        '''
        Gets list of NFL players from ESPN.com

        Args:
            team_code: str 'DEN', 'BUF', etc.

        Returns:
            HTML string
        '''
        url = 'http://www.espn.com/nfl/team/roster/_/name/{}'
        return self.get(url=url.format(team_code), encoding='latin1')

    def fantasy_projections(self, offset=0):
        '''
        Gets ESPN fantasy football projections
        '''
        url = 'http://games.espn.go.com/ffl/tools/projections?'
        params = {'startIndex': offset}
        return self.get(url, payload=params)

    def fantasy_waiver_wire(self, league_id, team_id):
        '''
        Gets waiver wire from ESPN fantasy league
        league_id=302946, team_id=12
        '''
        url = 'http://games.espn.com/ffl/freeagency?'
        params = {'leagueId': league_id, 'teamId': team_id}
        return self.get(url, payload=params)

if __name__ == "__main__":
    pass
