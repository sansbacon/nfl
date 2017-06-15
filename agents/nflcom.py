from __future__ import print_function

import logging

from nfl.scrapers.nflcom import NFLComScraper
from nfl.parsers.nflcom import NFLComParser
from nfl.pipelines.nflcom import gamesmeta_table


class NFLComAgent(object):

    def __init__(self, scraper=None, parser=None, cache_name=None, cj=None):
        '''
        
        Args:
            scraper: NFLComScraper object
            parser: NFLComParser object
            cache_name: string
            cj: cookiejar object
        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        if scraper:
            self._s = scraper
        else:
            self._s = NFLComScraper(cache_name=cache_name)
        if parser:
            self._p = parser
        else:
            self._p = NFLComParser()


    def week_games(self, season, week, savedir=None):
        '''
        Gets all games from weekly gamecenter page from NFL.com
        Args:
            season: int
            week: int

        Returns:
            all_games: list of dict
        '''
        all_games = []
        try:
            for g in self._p.week_page(self._s.week_page(season, week)):
                url = g.get('url')
                # need to get the game ID, then can get relevant boxscore data
                # http://www.nfl.com/widget/gc/2011/tabs/cat-post-boxscore?gameId=2007122000&enableNGS=false
                if url:
                    url += '#tab=analyze&analyze=boxscore'
                    if savedir:
                        content = self._s.get_filecache(url, savedir)
                    else:
                        content = self._s.get(url)
                    if content:
                        all_games.append(self._p.game_page(content))
            logging.info('finished {} week {}'.format(season, week))

        except Exception as e:
            logging.exception(e)

        return all_games


    def week_pages(self, seasons, weeks):
        '''
        Gets weekly gamecenter pages from NFL.com
        Args:
            seasons: list of int
            weeks: list of int

        Returns:
            all_games: list of dict
        '''
        all_games = []
        for season in seasons:
            for week in weeks:
                try:
                    games = self._p.week_page(self._s.week_page(season, week))
                    all_games += games
                    logging.info('finished {} week {}'.format(season, week))
                except Exception as e:
                    logging.exception(e)
        return all_games


if __name__ == '__main__':
    pass