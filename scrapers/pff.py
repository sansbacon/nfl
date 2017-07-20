# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

from nfl.scrapers.scraper import FootballScraper


class PFFScraper(FootballScraper):


    def __init__(self, headers=None, cookies=None, cache_name='fo-api', delay=1, expire_hours=168, as_string=False):
        '''
        Scrape profootballfocus

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

    def depth_charts(self, team_id):
        '''
        Gets pff depth charts

        Args:
            team_id: int 1, 2, etc.

        Returns:
            dict
        '''
        url = 'https://grades.profootballfocus.com/api/offenses/depth_charts?team_id={}'
        return self.get_json(url.format(team_id))

    def position_grades(self, pos):
        '''
        Gets pff grades

        Args:
            pos: 'QB', 'WR', 'TE', 'RB', etc.

        Returns:
            dict
        '''
        url = 'https://grades.profootballfocus.com/api/players?position={}'
        return self.get_json(url.format(pos))

    def player_grades_career(self, player_id):
        '''
        Gets pff grades for player each season

        Args:
            player_id: int

        Returns:
            dict
        '''
        url = 'https://grades.profootballfocus.com/api/players/{}/grades_by_season'
        return self.get_json(url.format(player_id))

    def player_grades_week(self, player_id):
        '''
        Gets pff grades for player each season

        Args:
            player_id: int

        Returns:
            dict
        '''
        url = 'https://grades.profootballfocus.com/api/players/{}/grades_by_week'
        return self.get_json(url.format(player_id))

    def player_snaps_season(self, player_id):
        '''
        Gets pff snap counts for most recent season

        Args:
            player_id: int

        Returns:
            dict
        '''
        url = 'https://grades.profootballfocus.com/api/players/{}/snaps_by_week'
        return self.get_json(url.format(player_id))

    def players(self, team_id):
        '''
        Gets profootballfocus players for team

        Args:
            team_id: int 1, 2, etc.
            
        Returns:
            dict
        '''
        return self.get_json('https://grades.profootballfocus.com/api/players?team_id={}'.format(team_id))

    def teams(self):
        '''
        Gets profootballfocus teams
        
        Returns:
            dict
        '''
        return self.get_json('https://grades.profootballfocus.com/api/teams')

if __name__ == '__main__':
    pass
