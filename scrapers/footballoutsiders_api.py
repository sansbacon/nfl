# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

from nfl.scrapers.scraper import FootballScraper


class FootballOutsidersAPIScraper(FootballScraper):


    def __init__(self, headers=None, cookies=None, cache_name='fo-api', delay=1, expire_hours=168, as_string=False):
        '''
        Scrape FO API

        Args:
            headers: dict of headers
            cookies: cookiejar object
            cache_name: should be full path
            delay: int (be polite!!!)
            expire_hours: int - default 168
            as_string: get string rather than parsed json
        '''
        if not cookies:
            try:
                import browser_cookie3
                cookies = browser_cookie3.firefox()
            except:
                try:
                    import browsercookie
                    cookies = browsercookie.firefox()
                except:
                    pass

        if not headers:
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
                       'Referer': 'http://www.footballoutsiders.com/premium/index.php', 'DNT': '1'}

        FootballScraper.__init__(self, headers=headers, cookies=cookies, cache_name=cache_name,
                                 delay=delay, expire_hours=expire_hours, as_string=as_string)

    def dvoa_week(self, season, week):
        '''
        Gets DVOA for specific week in season

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/premium/weekTeamSeasonDvoa.php?od=O&year={}&team=ARI&week={}'
        return self.get(url.format(season, week))

    def team_season(self, season, team):
        '''
        Gets team DVOA for specific season

        Returns:
            HTML string
        '''
        url = 'https://www.footballoutsiders.com/premium/weekByTeam.php?od=O&year={}&team={}&week=1'
        return self.get(url.format(season, team))

    def team_week(self, season, week):
        '''
        Gets team DVOA for specific week

        Returns:
            HTML string
        '''
        url = 'https://www.footballoutsiders.com/premium/weekTeamSeasonDvoa.php?od=O&year={}&team=ARI&week={}'
        return self.get(url.format(season, week))

if __name__ == '__main__':
    pass
