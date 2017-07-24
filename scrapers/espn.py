# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

from nfl.scrapers.scraper import FootballScraper


class ESPNNFLScraper(FootballScraper):
    '''

    '''

    def __init__(self, headers=None, cookies=None, cache_name='espn-scraper', delay=1, expire_hours=1, as_string=False):
        '''
        Scrape espn

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
        FootballScraper.__init__(self, headers, cookies, cache_name, delay, expire_hours, as_string)

    def league_roster(self, season, league_id, team_id):
        '''
        Gets roster for team in ESPN fantasy league
        '''
        url = 'http://games.espn.com/ffl/clubhouse?'
        params = {'leagueId': league_id,
                      'teamId': team_id,
                      'seasonId': season}
        return self.get(url, payload=params)

    def projections(self, offset=0):
        '''
        Gets ESPN fantasy football projections
        '''
        url = 'http://games.espn.go.com/ffl/tools/projections?'
        params = {'startIndex': offset}
        return self.get(url, payload=params)

    def waiver_wire(self, league_id, team_id):
        '''
        Gets waiver wire from ESPN fantasy league
        league_id=302946, team_id=12
        '''
        url = 'http://games.espn.com/ffl/freeagency?'
        params = {'leagueId': league_id, 'teamId': team_id}
        return self.get(url, payload=params)

if __name__ == "__main__":
    pass
