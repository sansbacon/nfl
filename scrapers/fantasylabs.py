from datetime import datetime
import logging

from ewt.scraper import EWTScraper


class FantasyLabsNFLScraper(EWTScraper):
    '''
    FantasyLabsNFLScraper

    Usage:

        s = FantasyLabsNFLScraper()
        content = s.today()
        model = s.model()
        models = s.models(start_date='09_04_2015', end_date='11_15_2015')    
        
    '''

    def __init__(self,**kwargs):

        '''
<<<<<<< HEAD
        EWTScraper parameters: 'dldir', 'expire_time', 'headers', 'keyprefix', 'mc', 'use_cache'
=======
        NFLScraper parameters: 'dldir', 'expire_time', 'headers', 'keyprefix', 'mc', 'use_cache'
>>>>>>> ace1da00fd9afc9f38280055e9751ec1562994bb
        '''

        # see http://stackoverflow.com/questions/8134444
        EWTScraper.__init__(self, **kwargs)

        logging.getLogger(__name__).addHandler(logging.NullHandler())

        if 'model_urls' in kwargs:
            self.model_urls = kwargs['models']
        else:
            self.model_urls = {
<<<<<<< HEAD
                'default': 'http://www.fantasylabs.com/api/playermodel/1/{}/?modelId=47139',
=======
                'default': 'http://www.fantasylabs.com/api/playermodel/1/10_19_2016/?modelId=47139',
>>>>>>> ace1da00fd9afc9f38280055e9751ec1562994bb
                'bales': 'http://www.fantasylabs.com/api/playermodel/1/{0}/?modelId=170627',
                'csuram': 'http://www.fantasylabs.com/api/playermodel/1/{0}/?modelId=193726',
                'tournament': 'http://www.fantasylabs.com/api/playermodel/1/{0}/?modelId=193746',
                'cash': 'http://www.fantasylabs.com/api/playermodel/1/{0}/?modelId=193745'
            }

    def _date_list(self, d1, d2):
        '''
        Takes two dates or datestrings and returns a list of days

        Usage:
            for d in s._date_list('10_09_2015', '10_04_2015'):
                print datetime.strftime(d, '%m_%d_%Y')
        '''
        if isinstance(d1, basestring):
            try:
                d1 = datetime.strptime(d1, '%m_%d_%Y')

            except:
                logging.error('{0} is not in %m_%d_%Y format'.format(d1))
                
        if isinstance(d2, basestring):
            try:
                d2 = datetime.strptime(d2, '%m_%d_%Y')

            except:
                logging.error('{0} is not in %m_%d_%Y format'.format(d1))

        season = d1-d2

        return [d1 - datetime.timedelta(days=x) for x in range(0, season.days+1)]

    def games_day(self, game_date):
        '''
        Gets json for games on single date (can use any date in upcoming NFL week)

        Usage:
            content = s.game(game_date='10_04_2015')
            
        '''

        url = 'http://www.fantasylabs.com/api/sportevents/1/{0}'.format(game_date)
        content = self.get(url)

        if not content:
            logging.error('could not get content from url: {0}'.format(url))

        return content

    def games_days(self, start_date, end_date):
        '''
        Gets json for games in weeks that fall in date range

        Usage:
            games = s.games(start_date='10_04_2015', end_date='10_09_2015')
            
        '''

        contents = {}

        for d in self._date_list(end_date, start_date):
            datestr = datetime.strftime(d, '%m_%d_%Y')
            contents[datestr] = self.games_day(game_date=datestr)

        return contents

    def games_today(self):
        '''
        Gets json for this week's NFL games

        Usage:
            content = s.games_today()
            
        '''

        day = datetime.strftime(datetime.today(), '%m_%d_%Y')
        url = 'http://www.fantasylabs.com/api/sportevents/1/{0}'.format(day)
        content = self.get(url)

        if not content:
            logging.error('could not get content from url: {0}'.format(url))

        return content

    def model(self, model_day, model_name='default'):
        '''
        Gets json for model, default to Bales model
        Stats in most models the same, main difference is the ranking based on weights of factors present in all models

<<<<<<< HEAD
        Arguments:
            model_day (str): in mm_dd_yyyy format
            model_name (str): uses default if not specified

        Returns:
            content (str): is json string
=======
	Arguments:
	    model_day(str): in %m_%d_%Y format
            model_name(str): default, bales, jennings, cash, tournament, etc.
>>>>>>> ace1da00fd9afc9f38280055e9751ec1562994bb

        Usage:
            bales_model_json = s.model()
            csuram_model_json = s.model('csuram')

        '''

<<<<<<< HEAD
        content = None
=======
>>>>>>> ace1da00fd9afc9f38280055e9751ec1562994bb
        url = self.model_urls.get(model_name, None)

        if not url:
            logging.error('could not find url for {0} model'.format(model_name))
<<<<<<< HEAD
            url = self.model_urls.get('default')

        # have to add today's date in mm_dd_yyyy format to URL
        content = self.get(url.format(model_day))

        if not content:
=======
            content = None

        else:
            # have to add today's date in mm_dd_yyyy format to URL
            content = self.get(url.format(model_day))

    	if not content:
>>>>>>> ace1da00fd9afc9f38280055e9751ec1562994bb
            logging.error('could not get content from url: {0}'.format(url))

        return content

    def models(self, start_date, end_date, model_name='bales'):
        '''
        Gets json for models in date range, default to Bales model
        Stats in most models the same, main difference is the ranking based on weights of factors present in all models

        Usage:
            models = s.models(start_date='10_04_2015', end_date='10_09_2015', model_name='csuram')
            
        '''

        contents = {}

        for d in self._date_list(end_date, start_date):
            datestr = datetime.strftime(d, '%m_%d_%Y')
            contents[datestr] = self.model(model_day=datestr)

        return contents

<<<<<<< HEAD
=======
    def thisweek(self):
        return datetime.strftime(datetime.today(),'%m_%d_%Y')


>>>>>>> ace1da00fd9afc9f38280055e9751ec1562994bb
if __name__ == "__main__":
    pass
