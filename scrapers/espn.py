# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division


from nfl.scrapers.scraper import FootballScraper


class ESPNNFLScraper(FootballScraper):
    '''

    '''

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


if __name__ == "__main__":
    pass
