from ewt.scraper import EWTScraper
import logging

class FantasyProsNFLScraper(EWTScraper):

    '''
    Downloads csv (with .xls extension) from fantasypros.com
    '''
    def __init__(self, **kwargs):
        
        # see http://stackoverflow.com/questions/8134444/python-constructor-of-derived-class
        EWTScraper.__init__(self, **kwargs)

        if 'adp_url' in 'kwargs':
            self.adp_url = kwargs['adp_url']
        else:
            self.adp_url = 'http://www.fantasypros.com/nfl/adp/overall.php?export=xls'

        if 'projection_url' in 'kwargs':
            self.projection_url = kwargs['projection_url']      
        else:
            self.projection_url = 'http://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php?export=xls'

    def get_adp(self, fname=None):
        if not fname:
            return self._get(self.adp_url)

        else:
            tmp_fname, headers = self.get_file(self.adp_url, fname)
            logging.debug('get_adp: http response headers')
            logging.debug(headers)
            return tmp_fname

    def get_season_rankings(self, fname=None):
        '''
        Download csv file and save to specified or temporary location if no fname parameter
        :param fname (str): specified location to save file
        :return tmp_fname (str), headers(dict)
        '''

        if not fname:
            return self.get(self.projection_url)

        else:
            tmp_fname, headers = self.get_file(self.projection_url, fname)
            logging.debug('get_projections: http response headers')
            logging.debug(headers)
            return tmp_fname

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    s = FantasyProsNFLScraper()
    logging.debug(s)