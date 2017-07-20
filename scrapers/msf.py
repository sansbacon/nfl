from nfl.scrapers.scraper import FootballScraper


class MySportsFeedsNFLScraper(FootballScraper):

    '''
    '''

    def __init__(self, username=None, password=None, response_format='json', league_format='1',
                 headers=None, cookies=None, cache_name=None,
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
        FootballScraper.__init__(self, headers, cookies, cache_name, delay, expire_hours, as_string)
        self.username = username
        self.password = password

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
        return self.get(url.format(season=season, format=self.response_format))

if __name__ == "__main__":
    pass
