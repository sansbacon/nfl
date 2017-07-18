import logging

from nfl.scrapers.scraper import FootballScraper


class FantasyLabsNFLScraper(FootballScraper):
    '''
    FantasyLabsNFLScraper
    If you don't have a subscription, you can access the information freely-available on the website
    If you have a subscription, the scraper can use your firefox cookies and access protected content
    You cannot access protected content if you (a) have not logged in (b) have firefox open

    Usage:

        s = FantasyLabsNFLScraper()
        content = s.today()
        model = s.model('11_30_2016', 'levitan')
       
    '''

    @property
    def model_urls(selfs):
        return {
            'default': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=47139',
            'levitan': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=524658',
            'bales': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=170627',
            'csuram': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=193726',
            'tournament': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=193746',
            'cash': 'http://www.fantasylabs.com/api/playermodel/1/{model_date}/?modelId=193745'
        }

    def games_day(self, game_date):
        '''
        Gets json for games on single date (can use any date in upcoming NFL week)

        Usage:
            content = s.game(game_date='10_04_2015')
            
        '''
        url = 'http://www.fantasylabs.com/api/sportevents/1/{0}'.format(game_date)
        return self.get(url)

    def model(self, model_day, model_name='default'):
        '''
        Gets json for model. Stats in most models the same, main difference is the ranking based on weights.
         
        Arguments:
            model_day (str): in mm_dd_yyyy format
            model_name (str): uses default if not specified

        Returns:
            content (str): is json string
        '''
        url = self.model_urls.get(model_name, None)
        if not url:
            logging.error('could not find url for {0} model'.format(model_name))
            url = self.model_urls.get('default')
        return self.get(url.format(model_date=model_day))

if __name__ == "__main__":
    pass
