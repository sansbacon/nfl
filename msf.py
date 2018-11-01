# -*- coding: utf-8 -*-
# msf.py
# classes to scrape and parse mysportsfeeds.com
# need an API key, free for personal use

import base64
import logging

from nflmisc.scraper import FootballScraper


class Scraper(FootballScraper):
    '''
    '''

    def __init__(self, username, password, response_format='json', league_format='1',
                 headers={}, cookies=None, cache_name=None,
                 delay=1, expire_hours=168, as_string=False):
        '''
        Scrape mysportsfeeds API

        Args:
            username(str):
            password(str):
            response_format(str): json or xml
            headers(dict): dict of headers
            cookies: cookiejar object
            cache_name(str): should be full path
            delay(int): default 1
            expire_hours(int): default 168
            as_string(bool): get string rather than parsed json

        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        auth = 'Basic ' + base64.b64encode('{}:{}'.format(username, password).encode('utf-8')).decode('ascii')
        headers['Authorization'] = auth
        FootballScraper.__init__(self, headers, cookies, cache_name, delay, expire_hours, as_string)
        self.response_format = response_format
        self.league_format = league_format

    def boxscore(self, game_id, season='latest'):
        '''
        Gets single boxscore
        
        Args:
            game_id(int):
            season(str): default 'latest'; could be 2017-2018-regular, etc.

        Returns:
            dict

        '''
        url = 'https://api.mysportsfeeds.com/v1.1/pull/nfl/{season}/game_boxscore.{format}?gameid={game_id}'
        if self.response_format == 'json':
            return self.get_json(url.format(season=season, format=self.response_format, game_id=game_id))
        else:
            return self.get(url.format(season=season, format=self.response_format, game_id=game_id))

    def player_gamelogs(self, team, season='latest'):
        '''
        Gets player gamelogs
        
        Args:
            team (str): atl, bos, chi, etc.
            season (str): latest, 2017-2018-regular, etc. 

        Returns:
            dict
            
        '''
        teams = ['ari', 'atl', 'bal', 'buf', 'car', 'chi', 'cin', 'cle', 'dal',
                 'den', 'det', 'gb', 'hou', 'ind', 'jax', 'kc', 'la', 'lac', 'mia', 'min',
                 'ne', 'no', 'nyg', 'nyj', 'oak', 'phi', 'pit', 'sea', 'sf', 'tb', 'ten', 'was']
        if team not in teams:
            raise ValueError('invalid team: {}'.format(team))
        url = 'https://api.mysportsfeeds.com/v1.2/pull/nfl/{seas}/player_gamelogs.' + self.response_format
        if self.response_format == 'json':
            return self.get_json(url.format(season), payload={'team': team})
        else:
            return self.get(url, payload={'team': team})

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
            season = '{}-{}-regular'.format(season, season + 1)
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
            season = '{}-{}-regular'.format(season, season + 1)
        if self.response_format == 'json':
            return self.get_json(url.format(season=season, format=self.response_format))
        else:
            return self.get(url.format(season=season, format=self.response_format))


class Parser(object):
    '''

    '''

    def __init__(self):
        '''
        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def boxscore(self, content):
        '''

        Args:
            content:

        Returns:

        '''
        return []

    def player_gamelogs(self, content):
        '''

        Args:
            content:

        Returns:

        '''
        return []

    def boxscore(self, content):
        '''

        Args:
            content:

        Returns:

        '''
        return []

    def season_stats(self, content):
        '''

        Args:
            content:

        Returns:

        '''
        return []

    def schedule(self, content):
        '''

        Args:
            content:

        Returns:

        '''
        return []


if __name__ == "__main__":
    pass
