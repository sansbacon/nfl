# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

from nfl.scrapers.scraper import FootballScraper


class NFLComScraper(FootballScraper):


    def game(self, gsis_id):
        '''
        Gets individual gamecenter page 

        Args:
            gsis_id: 

        Returns:
            content: HTML string
        '''
        url = 'http://www.nfl.com/liveupdate/game-center/{0}/{0}_gtd.json'
        return self.get(url.format(gsis_id))

    def gamebook(self, season_year, week, gamekey):
        '''
        Gets XML gamebook for individual game
        
        Args:
            season: int 2016, 2015
            week: int 1-17
            gamekey: int 56844, etc.

        Returns:
            HTML string
        '''
        url = 'http://www.nflgsis.com/{}/Reg/{}/{}/Gamebook.xml'
        if week < 10:
            week = '0{}'.format(week)
        else:
            week = str(week)
        return self.get(url.format(season_year, week, gamekey))

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

    def ol(self, season_year):
        '''
        Parses a weekly page with reported player injuries

        Args:
            week: int 1, 2, 3, etc.

        Returns:
            content: HTML string
        '''
        url = 'http://www.nfl.com/stats/categorystats?'
        params = {
          'archive': 'true',
          'conference': 'null',
          'role': 'TM',
          'offensiveStatisticCategory': 'OFFENSIVE_LINE',
          'defensiveStatisticCategory': 'null',
          'season': season_year,
          'seasonType': 'REG',
          'tabSeq': '2',
          'qualified': 'false',
          'Submit': 'Go'
        }
        return self.get(url, payload=params)

    def schedule_week(self, season, week):
        '''
        Parses a weekly schedule page with links to individual gamecenters
        Similar to score_week, but does not have scores for each quarter

        Args:
            season: int 2017, 2016, etc.
            week: int 1, 2, 3, etc.

        Returns:
            content: HTML string
        '''
        url = 'http://www.nfl.com/schedules/{0}/REG{1}'
        return self.get(url.format(season, week))

    def score_week(self, season, week):
        '''
        Parses a weekly page with links to individual gamecenters
        Similar to schedule_week, but has scores for each quarter

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