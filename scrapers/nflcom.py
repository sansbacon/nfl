# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

from nfl.scrapers.scraper import FootballScraper


class NFLComScraper(FootballScraper):


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

    def injuries(self, week):
        '''
        Parses a weekly page with reported player injuries

        Args:
            week: int 1, 2, 3, etc.

        Returns:
            content: HTML string
        '''
        url = 'http://www.nfl.com/injuries?week={}'
        return self.get(url.format(week))

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
