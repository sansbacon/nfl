'''
RotoguruNFLScraper

'''

import logging

from nfl.scrapers.scraper import FootballScraper


class RotoguruNFLScraper(FootballScraper):
    '''

    '''

    def dfs_week(self, year, week, sites):
        '''
        Gets rotoguru page of one week of dfs results - goes back to 2014
        '''
        
        contents = {}
        base_url = 'http://rotoguru1.com/cgi-bin/fyday.pl?week={week}&year={year}&game={site}&scsv=1'

        for site in sites:
            url = base_url.format(week=week, year=year, site=site)                 
            contents[site] = self.get(url)
                    
        return contents

    def dfs_weeks(self, years, weeks, sites):
        '''
        Gets rotoguru page of range of weeks of dfs results - goes back to 2014
        '''
        
        contents = {}
        base_url = 'http://rotoguru1.com/cgi-bin/fyday.pl?week={week}&year={year}&game={site}&scsv=1'

        for site in sites:
            contents[site] = {}
            
            for year in years:
                contents[site][year] = {}
                
                for week in weeks:
                    url = base_url.format(week=week, year=year, site=site)                 
                    contents[site][year][week] = self.get(url)
                    
        return contents

if __name__ == "__main__":
    pass
