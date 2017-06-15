'''
NFLDotComScraper

'''
import logging

from nfl.scrapers.scraper import FootballScraper


class NFLComScraper(FootballScraper):


    def __init__(self, headers=None, cookies=None, cache_name=None, delay=1, expire_hours=168):
        '''
        
        Args:
            headers: dict 
            cookies: cookiejar object
            cache_name: string
            delay: int
            expire_hours: int
        '''
        # see http://stackoverflow.com/questions/8134444
        FootballScraper.__init__(self, headers=headers, cookies=cookies, cache_name=cache_name, delay=delay, expire_hours=expire_hours)
        self.logger = logging.getLogger(__name__).addHandler(logging.NullHandler())

    def gamecenter_json(self, gsis_id):
        '''
        Gets individual gamecenter page 

        Args:
            gsis_id: 

        Returns:
            content: HTML string
        '''
        url = 'http://www.nfl.com/liveupdate/game-center/{0}/{0}_gtd.json'
        return self.get(url.format(gsis_id))

    def upcoming_week_page(self, season, week):
        '''
        Parses a weekly page with links to individual gamecenters

        Args:
            season: int 2017, 2016, etc.
            week: int 1, 2, 3, etc.

        Returns:
            content: HTML string
        '''
        url = 'http://www.nfl.com/schedules/{0}/REG{1}'
        return self.get(url.format(season, week))

    def week_page(self, season, week):
        '''
        Parses a weekly page with links to individual gamecenters
        
        Args:
            season: int 2017, 2016, etc.
            week: int 1, 2, 3, etc.

        Returns:
            content: HTML string
        '''
        url = 'http://www.nfl.com/scores/{0}/REG{1}'
        return self.get(url.format(season, week))


if __name__ == "__main__":
    pass
