import logging
from urllib import urlencode

from nfl.scrapers.scraper import FootballScraper


class FantasyFootballCalculatorScraper(FootballScraper):
    '''
    Obtains html content of NFL fantasy projections or ADP page of fantasycalculator.com       
    '''

    def __init__(self):
        '''
        Args:
        '''
        FootballScraper.__init__(self)


    def adp(self, fmt='ppr', teams=14):
        '''
        
        Args:
            fmt: 
            teams: 

        Returns:

        '''
        url = 'https://fantasyfootballcalculator.com/adp_xml.php?format={}&teams={}'
        return self.get(url.format(fmt, teams))


    def projections(self, url=None, fname=None):
        '''
        Fetch projections url, try cache, then file, then web
        Args:
            url (str): url for the fantasy football calculator projections page
        Returns:
            Str if successful, None otherwise.
        '''
        url = 'https://fantasyfootballcalculator.com/rankings'
        return self.get(url)


if __name__ == "__main__":
    pass