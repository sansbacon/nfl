from __future__ import absolute_import, print_function, division

import logging

from nfl.dates import convert_format
from nfl.scrapers.scraper import FootballScraper
from nfl.seasons import fantasylabs_week
from nfl.utility import url_quote


class FantasyLabsNFLScraper(FootballScraper):
    '''
    FantasyLabsNFLScraper
    If you don't have a subscription, you can access the information freely-available on the website
    If you have a subscription, the scraper can use your firefox cookies and access protected content
    You cannot access protected content if you (a) have not logged in (b) have firefox open
    '''

    @property
    def model_urls(selfs):
        return {
            'default': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=47139',
            'levitan': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=524658',
            'bales': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=170627',
            'csuram': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=193726',
            'tournament': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=193746',
            'cash': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=193745'
        }

    def correlations(self):
        '''
        
        Returns:

        '''
        url = 'http://api.fantasylabs.com/api/v2/correlations/views/1'
        return self.get_json(url)

    def games(self, season_year, week, fmt='fl_matchups'):
        '''
        
        Args:
            season_year: 2017, etc.
            week: 1, 2, etc.
            fmt: 'fl_matchups', 'fl2017', etc.

        Returns:

        '''
        game_date = fantasylabs_week(season_year, week, fmt)
        url = 'http://www.fantasylabs.com/api/teams/1/{}/games/'
        return self.get_json(url.format(game_date))

    def matchups(self, team_name, game_date):
        '''
        
        Args:
            game_day: 

        Returns:

        '''
        game_date = convert_format(game_date, 'fl_matchups')
        team_name = url_quote(team_name)
        url = 'http://www.fantasylabs.com/api/matchups/1/team/{}/{}'.format(team_name, game_date)
        return self.get_json(url)

    def model(self, model_day, model_name='default'):
        '''
        TODO: need to see if this still works
        Gets json for model. Stats in most models the same, main difference is the ranking based on weights.
         
        Arguments:
            model_day (str): in mm_dd_yyyy format
            model_name (str): uses default if not specified

        Returns:
            content (str): is json string
        '''
        url = self.model_urls.get(model_name, None)
        if not url:
            logging.error('could not find url for {0} model'.format(model_name))
            url = self.model_urls.get('default')
        return self.get_json(url.format(model_date=model_day))

    def sourcedata(self, game_date):
        '''
        Gets contest data
        
        Args:
            game_day: 

        Returns:
        '''
        game_date = convert_format(game_date, 'fl2017')
        url = 'http://www.fantasylabs.com/api/sourcedata/1/{}'.format(game_date)
        return self.get_json(url)

    def vegas(self, game_date):
        '''
        Gets vegas data
        
        Args:
            game_day: 

        Returns:

        '''
        game_date = convert_format(game_date, 'fl2017')
        url = 'http://www.fantasylabs.com/api/sportevents/1/{}/vegas/'.format(game_date)
        return self.get_json(url)


if __name__ == "__main__":
    pass
