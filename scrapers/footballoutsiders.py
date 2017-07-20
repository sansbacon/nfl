# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

from scraper import FootballScraper


class FootballOutsidersNFLScraper(FootballScraper):

    def dl(self, season=''):
        '''
        Gets DL stats page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/dl{}'
        return self.get(url.format(season))

    def drive(self, season=''):
        '''
        Gets drivestats page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/drivestats{}'
        return self.get(url.format(season))

    def ol(self, season=''):
        '''
        Gets OL stats page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/ol{}'
        return self.get(url.format(season))

    def qb(self, season=''):
        '''
        Gets QB stats page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/qb{}'
        return self.get(url.format(season))

    def rb(self, season=''):
        '''
        Gets RB stats page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/rb{}'
        return self.get(url.format(season))

    def te(self, season=''):
        '''
        Gets TE stats page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/te{}'
        return self.get(url.format(season))

    def wr(self, season=''):
        '''
        Gets WR stats page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/wr{}'
        return self.get(url.format(season))

    def snap_counts(self, year, week):
        '''
        Gets weekly snapcounts

        Args:
            year: 2017, 2016, etc.
            week: 1, 2, etc.

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/snapcounts'
        payload = {'team': 'ALL', 'week': week, 'pos': 'ALL', 'year': year, 'Submit': 'Submit'}
        return self.post(url, payload)

    def team_defense(self, season=''):
        '''
        Gets defense DVOA page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/teamdef{}'
        return self.get(url.format(season))

    def team_offense(self, season=''):
        '''
        Gets offense DVOA page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/teamoff{}'
        return self.get(url.format(season))

    def team_efficiency(self, season=''):
        '''
        Gets team DVOA page

        Returns:
            HTML string
        '''
        url = 'http://www.footballoutsiders.com/stats/teameff{}'
        return self.get(url.format(season))

if __name__ == '__main__':    
    pass
