from __future__ import print_function

import json
import logging
from string import ascii_uppercase

from nfl.scrapers.pfr import PfrNFLScraper
from nfl.parsers.pfr import PfrNFLParser


class ProFootballReferenceAgent(object):

    def __init__(self, scraper=None, parser=None):
        '''
        
        Args:
            scraper: PfrScraper object
            parser: PfrParser object
            cache_name: string
            cj: cookiejar object
        '''

        logging.getLogger(__name__).addHandler(logging.NullHandler())

        if scraper:
            self._s = scraper
        else:
            self._s = PfrNFLScraper(cache_name='pfr', delay=1.5)

        if parser:
            self._p = parser
        else:
            self._p = PfrNFLParser()

    def players(self, savefile=None):
        '''
        Gets all of the players from pfr

        Returns:
            list of dict
        '''
        results = []

        for letter in ascii_uppercase:
            content = self._s.players(letter)
            results += self._p.players(content)
            logging.info('completed players {}'.format(letter))

        if savefile:
            with open(savefile, 'w') as outfile:
                json.dump(results, outfile)
            logging.info('wrote results to {}'.format(savefile))

        return results

    def playerstats_offense_yearly(self):
        '''
        TODO: fully implement this
        Returns:

        '''
        import json
        from pathlib import Path
        from nfl.scrapers.pfr import PfrNFLScraper
        from nfl.parsers.pfr import PfrNFLParser

        pfrs = PfrNFLScraper(cache_name='pfrscraper')
        pfrp = PfrNFLParser()

        results = []
        for offset in range(0, 700, 100):
            content = pfrs.playerstats_offense_yearly(2017, offset)
            results += pfrp.playerstats_offense_yearly(content)
            print('finished offset {}'.format(offset))

        pth = Path.home() / 'playerstats_offense_yearly_2017.json'
        with pth.open('w') as f:
            json.dump(results, f)

if __name__ == '__main__':
    pass