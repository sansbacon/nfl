'''
PfrNFLScraper
Class to fetch pages from pro-football-reference.com
'''

import logging
from string import ascii_uppercase

from nflmisc.scraper import FootballScraper


class PfrNFLScraper(FootballScraper):

    @property
    def pgl_finder_url(self):
        return 'https://www.pro-football-reference.com/play-index/pgl_finder.cgi?'

    @property
    def tgl_finder_url(self):
        return 'https://www.pro-football-reference.com/play-index/tgl_finder.cgi?'

    @property
    def pgl_params(self):
        '''
        Basic parameters for player gamelog finder
        
        Args:
            None
            
        Returns:
            dict
        '''

        return {
            'request': 1, 'season_start': 1, 'season_end': -1,
            'age_min': 0, 'age_max': 0, 'game_type': 'R',
            'career_game_num_min': 0, 'career_game_num_max': 499,
            'game_num_min': 0, 'game_num_max': 99,
            'week_num_min': 1, 'week_num_max': 20,
            'c1stat': 'fantasy_points', 'c1comp': 'gt', 'c1val': -5,
            'c2stat': 'choose', 'c2comp': 'gt',
            'c3stat': 'choose', 'c3comp': 'gt',
            'c4stat': 'choose', 'c4comp': 'gt',
            'c5comp': 'choose', 'c5gtlt': 'lt', 'c5val': 1.0,
            'c6mult': 1.0, 'c6comp': 'choose',
            'order_by': 'game_date', 'order_by_asc': 'Y'
        }

    def _merge_params(self, params):
        '''
        Creates merged set of params, where params overwrites defaults
        
        Args:
            params: dict

        Returns:
            dict
        '''
        context = self.pgl_params.copy()
        context.update(params)
        return context

    def draft(self, season_year):
        '''
        Gets entire draft page for single season

        Args:
            season_year: int 2016, 2017, etc.

        Returns:
            content: HTML string of that year's draft page
        '''
        url = 'http://www.pro-football-reference.com/years/{season_year}/draft.htm'
        return self.get(url.format(season_year=season_year))

    def playerstats_fantasy_weekly(self, season_year, week, pos=None, offset=0):
        '''
        Gets 100 rows of fantasy results for specific season and week

        Args:
            season_year: 2016, 2015, etc. 
            week: 1, 2, 3, etc.
            pos: 'qb', 'wr', etc.
            offset: 0, 100, 200, etc.

        Returns:
            HTML string
        '''
        if pos:
            params = self._merge_params({'year_min': season_year, 'year_max': season_year, 'offset': offset,
                                         'week_num_min': week, 'week_num_max': week, 'pos': pos})
        else:
            params = self._merge_params({'year_min': season_year, 'year_max': season_year, 'offset': offset,
                                         'week_num_min': week, 'week_num_max': week})
        return self.get(self.pgl_finder_url, payload=params)

    def playerstats_fantasy_yearly(self, season_year, pos=None, offset=0):
        '''
        Gets 100 rows of fantasy results for specific season

        Args:
            season_year: 2016, 2015, etc. 
            pos: 'qb', 'wr', etc.
            offset: 0, 100, 200, etc.

        Returns:
            HTML string
        '''
        if pos:
            params = self._merge_params({'year_min': season_year, 'year_max': season_year,
                                         'offset': offset, 'pos': pos, 'match': 'single'})
        else:
            params = self._merge_params({'year_min': season_year, 'year_max': season_year, 'offset': offset})
        return self.get(self.pgl_finder_url, payload=params)

    def player_fantasy_year(self, season_year, player_id):
        '''
        Gets fantasy page for individual player
        
        Args:
            player_id: 

        Returns:
            HTML string
        '''
        # https://www.pro-football-reference.com/players/{R}/{RyanMa00}/fantasy/{2016}
        url = 'https://www.pro-football-reference.com/players/{}/{}/fantasy/{}'
        return self.get(url.format(player_id[0], player_id, season_year))

    def playerstats_offense_weekly(self, season_year, week, pos='0', offset=0):
        '''
        Gets 100 rows of offense results for specific season and week

        Args:
            season_year (int): 2016, 2015, etc. 
            week (int): 1, 2, 3, etc.
            pos (str): '0' (for all) or 'QB', etc.
            offset (int): 0, 100, 200, etc.

        Returns:
            HTML string
            
        '''
        params = self._merge_params({'year_min': season_year, 'year_max': season_year,
                                     'offset': offset, 'match': 'game', 'pos': pos,
                                     'c2stat': 'targets', 'c2comp': 'gt', 'c2val': '-1'})
        if week > 0:
            params['week_num_min'] = week
            params['week_num_max'] = week
        content = self.get(self.pgl_finder_url, payload=params)
        logging.debug(self.urls[-1])
        return content

    def playerstats_offense_yearly(self, season_year, pos='0', offset=0):
        '''
        Gets 100 rows of offense results for specific season

        Args:
            season_year (int): 2016, 2015, etc. 
            pos (str): '0' or 'QB', etc.
            offset (int): 0, 100, 200, etc.

        Returns:
            str: HTML page
            
        '''
        params = self._merge_params({'year_min': season_year, 'year_max': season_year,
                                     'offset': offset, 'match': 'single', 'pos': pos,
                                     'c2stat': 'targets', 'c2comp': 'gt', 'c2val': '-1'})
        content = self.get(self.pgl_finder_url, payload=params)
        logging.debug(self.urls[-1])
        return content

    def playerstats_passing_weekly(self, season_year, week, offset=0):
        '''
        Gets 100 rows of offense results for specific season and week

        Args:
            season_year: 2016, 2015, etc. 
            week: 1, 2, 3, etc.
            offset: 0, 100, 200, etc.

        Returns:
            HTML string
        '''
        params = self._merge_params({'year_min': season_year, 'year_max': season_year, 'offset': offset,
                                     'week_num_min': week, 'week_num_max': week,
                                     'c1stat': 'pass_att', 'c1val': '1',
                                     'c2stat': 'targets', 'c2comp': 'gt', 'c2val': '-1'})
        content = self.get(self.pgl_finder_url, payload=params)
        logging.debug(self.urls[-1])
        return content

    def playerstats_passing_yearly(self, season_year, offset=0):
        '''
        Gets passing results for specific season

        Args:
            season_year: 2016, 2015, etc. 

        Returns:
            HTML string
        '''
        url = 'https://www.pro-football-reference.com/years/{}/passing.htm'
        content = self.get(url.format(season_year))
        logging.debug(self.urls[-1])
        return content

    def playerstats_receiving_weekly(self, season_year, week, offset=0):
        '''
        Gets 100 rows of receiving results for specific season and week

        Args:
            season_year: 2016, 2015, etc. 
            week: 1, 2, 3, etc.
            offset: 0, 100, 200, etc.

        Returns:
            HTML string
        '''
        params = self._merge_params({'year_min': season_year, 'year_max': season_year, 'offset': offset,
                                     'week_num_min': week, 'week_num_max': week, 'c1stat': 'targets', 'c1val': '1'})
        content = self.get(self.pgl_finder_url, payload=params)
        logging.debug(self.urls[-1])
        return content

    def playerstats_receiving_yearly(self, season_year, offset=0):
        '''
        Gets rushing/receiving results for specific season
    
        Args:
            season_year: 2016, 2015, etc. 
    
        Returns:
            HTML string
        '''
        url = 'https://www.pro-football-reference.com/years/{}/rushing.htm'
        content = self.get(url.format(season_year))
        logging.debug(self.urls[-1])
        return content

    def playerstats_rushing_weekly(self, season_year, week, offset=0):
        '''
        Gets 100 rows of offense results for specific season and week

        Args:
            season_year: 2016, 2015, etc. 
            week: 1, 2, 3, etc.
            offset: 0, 100, 200, etc.

        Returns:
            HTML string
        '''
        params = self._merge_params({'year_min': season_year, 'year_max': season_year, 'offset': offset,
                                     'week_num_min': week, 'week_num_max': week, 'c1stat': 'rush_att', 'c1val': '1'})
        content = self.get(self.pgl_finder_url, payload=params)
        logging.debug(self.urls[-1])
        return content

    def playerstats_rushing_yearly(self, season_year, offset=0):
        '''
        Gets rushing/receiving results for specific season

        Args:
            season_year: 2016, 2015, etc. 

        Returns:
            HTML string
        '''
        url = 'https://www.pro-football-reference.com/years/{}/rushing.htm'
        content = self.get(url.format(season_year))
        logging.debug(self.urls[-1])
        return content

    def players(self, last_initial):
        '''
        Gets player page for last initial, such as A, B, C
        
        Args:
            last_initial: str A, B, C

        Returns:
            HTML string
        '''
        try:
            last_initial = last_initial.upper()
            if last_initial in ascii_uppercase:
                url = 'https://www.pro-football-reference.com/players/{}/'.format(last_initial)
                logging.info('getting {}'.format(url))
                return self.get(url)
            else:
                raise ValueError('invalid last_initial')
        except Exception as e:
            logging.exception(e)

    def team_plays_query(self, season_start, season_end, offset):
        '''
        Gets game-by-game play counts for teams

        Args:
            season_start: int 2016, 2017, etc.
            season_end: int 2016, 2017, etc.
            offset: int 0, 100, 200, etc.

        Returns:
            content: HTML string of 100 entries
        '''
        params = {
            'request': '1',
            'match': 'game',
            'year_min': '2009',
            'year_max': '2016',
            'game_type': 'R',
            'game_num_min': '0',
            'game_num_max': '99',
            'week_num_min': '0',
            'week_num_max': '99',
            'temperature_gtlt': 'lt',
            'c1stat': 'plays_offense',
            'c1comp': 'gt',
            'c1val': '0',
            'c5val': '1.0',
            'order_by': 'game_date',
            'order_by_asc': 'Y'
        }

        return self.get(self.tgl_finder_url, payload=params)

    def team_passing_weekly(self, season_start, season_end, week):
        '''
        Gets game-by-game passing stats for teams

        Args:
            season_start: int 2016, 2017, etc.
            season_end: int 2016, 2017, etc.
            week: int 1, 2, etc.

        Returns:
            content: HTML string
        '''
        params = {
            'request': '1',
            'match': 'game',
            'year_min': season_start,
            'year_max': season_end,
            'game_type': 'R',
            'game_num_min': '0',
            'game_num_max': '99',
            'week_num_min': week,
            'week_num_max': week,
            'temperature_gtlt': 'lt',
            'c1stat': 'pass_cmp',
            'c1comp': 'gt',
            'c1val': '0',
            'c5val': '1.0',
            'order_by': 'pass_td'
        }

    def team_defense_yearly(self, season_year):
        '''
        Gets total team defense stats for specific season_year
        
        Args:
            season_year: 2016, etc.

        Returns:
            list of dict
        '''
        url = 'https://www.pro-football-reference.com/years/{}/opp.htm'
        return self.get(url.format(season_year))

    def team_defense_weekly(self, season_start, season_end, week):
        '''
        Gets game-by-game defense stats for teams

        Args:
            season_start: int 2016, 2017, etc.
            season_end: int 2016, 2017, etc.
            week: int 1, 2, etc.

        Returns:
            content: HTML string
        '''
        params = {
            'request': '1',
            'match': 'game',
            'year_min': season_start,
            'year_max': season_end,
            'game_type': 'R',
            'game_num_min': '0',
            'game_num_max': '99',
            'week_num_min': week,
            'week_num_max': week,
            'temperature_gtlt': 'lt',
            'c1stat': 'plays_defense',
            'c1comp': 'gt',
            'c1val': '0',
            'c2stat': 'pass_cmp_opp',
            'c2comp': 'gt',
            'c2val': '0',
            'c3stat': 'rush_att_opp',
            'c3comp': 'gt',
            'c3val': '0',
            'c4stat': 'pass_sacked_opp',
            'c4comp': 'gt',
            'c4val': '0',
            'c5val': '1.0',
            'order_by': 'game_date',
            'order_by_asc': 'Y'
        }

        return self.get(self.tgl_finder_url, payload=params)

    def team_offense_yearly(self, season_year):
        '''
        Gets total team offense stats for specific season_year

        Args:
            season_year: 2016, etc.

        Returns:
            str: HTML page

        '''
        url = 'https://www.pro-football-reference.com/years/{}'
        return self.get(url.format(season_year))

    def team_offense_weekly(self, season_start, season_end, week):
        '''
        Gets game-by-game offense stats for teams

        Args:
            season_start: int 2016, 2017, etc.
            season_end: int 2016, 2017, etc.
            week: int 1, 2, etc.

        Returns:
            content: HTML string
        '''
        params = {
            'request': '1',
            'match': 'game',
            'year_min': season_start,
            'year_max': season_end,
            'game_type': 'R',
            'game_num_min': '0',
            'game_num_max': '99',
            'week_num_min': week,
            'week_num_max': week,
            'temperature_gtlt': 'lt',
            'c1stat': 'rush_att',
            'c1comp': 'gt',
            'c1val': '0',
            'c5val': '1.0',
            'order_by': 'pass_td'
        }

        return self.get(self.tgl_finder_url, payload=params)

    def team_fantasy_weekly(self, team_id, week, year):
        '''
        Gets one week of fantasy gamelogs for single team

        Args:
            team_id(str):
            week(int):
            year(int):

        Returns:
            str

        '''
        url = 'https://www.pro-football-reference.com/play-index/pgl_finder.cgi?'
        params = {'c1comp': 'gt',
                  'c1stat': 'fantasy_points',
                  'c1val': '-5',
                  'c2comp': 'gt',
                  'c2stat': 'targets',
                  'c2val': '0',
                  'c5val': '1.0',
                  'career_game_num_max': '400',
                  'career_game_num_min': '1',
                  'game_num_max': '99',
                  'game_num_min': '0',
                  'game_type': 'R',
                  'match': 'game',
                  'order_by': 'game_date',
                  'order_by_asc': 'Y',
                  'pos': '0',
                  'request': '1',
                  'season_end': '-1',
                  'season_start': '1',
                  'team_id': team_id,
                  'week_num_max': week,
                  'week_num_min': week,
                  'year_max': year,
                  'year_min': year
                  }

        return self.get(url, payload=params)

if __name__ == "__main__":
    pass