# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import base64
import logging

from nfl.scrapers.scraper import FootballScraper


class MySportsFeedsNFLScraper(FootballScraper):

    '''
    '''

    def __init__(self, username, password, response_format='json', league_format='1',
                 headers={}, cookies=None, cache_name=None,
                 delay=1, expire_hours=168, as_string=False):
        '''
        Scrape mysportsfeeds API

        Args:
            username: string
            password: json or xml
            headers: dict of headers
            cookies: cookiejar object
            cache_name: should be full path
            delay: int (be polite!!!)
            expire_hours: int - default 168
            as_string: get string rather than parsed json
        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        auth = 'Basic ' + base64.b64encode('{}:{}'.format(username, password).encode('utf-8')).decode('ascii')
        headers['Authorization'] = auth
        FootballScraper.__init__(self, headers, cookies, cache_name, delay, expire_hours, as_string)
        self.response_format = response_format
        self.league_format = league_format

    def boxscore(self,  game_id, season='latest'):
        '''
        Gets single boxscore
        
        Args:
            season: 
            game_id: 

        Returns:
            dict
        '''
        url = 'https://api.mysportsfeeds.com/v1.1/pull/nfl/{season}/game_boxscore.{format}?gameid={game_id}'
        if self.response_format == 'json':
            return self.get_json(url.format(season=season, format=self.response_format, game_id=game_id))
        else:
            return self.get(url.format(season=season, format=self.response_format, game_id=game_id))


    def season_stats(self, season='latest'):
        '''
        Gets season-long stats        
        Args:
            season: 

        Returns:
            dict
        '''
        url = 'https://api.mysportsfeeds.com/v1.1/pull/nfl/{season}/cumulative_player_stats.{format}'
        if isinstance(season, int):
            season = '{}-{}-regular'.format(season, season+1)
        if self.response_format == 'json':
            return self.get_json(url.format(season=season, format=self.response_format))
        else:
            return self.get(url.format(season=season, format=self.response_format))

    def schedule(self, season='latest'):
        '''
        Gets NFL schedule for season        

        Args:
            season: default latest

        Returns:
            dict            
        '''
        url = 'https://api.mysportsfeeds.com/v1.1/pull/nfl/{season}/full_game_schedule.{format}'
        if isinstance(season, int):
            season = '{}-{}-regular'.format(season, season+1)
        if self.response_format == 'json':
            return self.get_json(url.format(season=season, format=self.response_format))
        else:
            return self.get(url.format(season=season, format=self.response_format))

if __name__ == "__main__":
    pass
