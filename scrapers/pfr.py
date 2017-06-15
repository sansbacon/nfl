'''
PfrNFLScraper

'''

import logging

from ewt.scraper import EWTScraper


class PfrNFLScraper(EWTScraper):


    def __init__(self, **kwargs):

        # see http://stackoverflow.com/questions/8134444
        EWTScraper.__init__(self, **kwargs)
        self.logger = logging.getLogger(__name__).addHandler(logging.NullHandler())
        self.pgl_finder_url = 'http://www.pro-football-reference.com/play-index/pgl_finder.cgi'

        if 'polite' in 'kwargs':
            self.polite = kwargs['polite']
        else:
            self.polite = True

        if 'params' in 'kwargs':
            self.params = kwargs['params']
        else:
            self.params = {
                'request':1, 'match':'game', 'year_min': 2016, 'year_max': 2016, 'season_start':1, 'season_end':-1, 'age_min':0, 'age_max':0, 'pos': '', 'game_type':'R',
                'career_game_num_min':0, 'career_game_num_max':499, 'game_num_min':0, 'game_num_max':99, 'week_num_min': 1, 'week_num_max': 17, 'c1stat':'choose', 'c1comp':'gt',
                'c2stat':'choose', 'c2comp':'gt', 'c3stat':'choose', 'c3comp':'gt', 'c4stat':'choose', 'c4comp':'gt', 'c5comp':'choose', 'c5gtlt':'lt', 'c6mult':1.0, 'c6comp':'choose',
                'offset': 0, 'order_by':'draftkings_points'
            }


    def _week_position(self, season, week, pos, offsets=[0, 100, 200]):
        '''
        Gets one week of fantasy stats for one position
        '''

        results = []

        # pfr only shows 100 per page - not a problem for QB but
        # need 2nd page for TE and 3rd page for WR and RB
        for offset in offsets:
            params = self.params
            if pos == 'QB' and offset > 0:
                continue
            elif pos == 'TE' and offset > 100:
                continue
            else:
                params['year_min'] = season
                params['year_max'] = season
                params['week_num_min'] = week
                params['week_num_max'] = week
                params['pos'] = pos
                if offset > 0: params['offset'] = offset
                content = self.get(self.pgl_finder_url, params=params)
                if content: results.append(content)

        return results


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
        base_url = """http://www.pro-football-reference.com/play-index/tgl_finder.cgi?request=1&match=game&year_min={year_min}&year_max={year_max}&game_type=R&game_num_min=0&game_num_max=99&week_num_min=0&week_num_max=99&temperature_gtlt=lt&team_conf_id=All%20Conferences&team_div_id=All%20Divisions&opp_conf_id=All%20Conferences&opp_div_id=All%20Divisions&team_off_scheme=Any%20Scheme&team_def_align=Any%20Alignment&opp_off_scheme=Any%20Scheme&opp_def_align=Any%20Alignment&c1stat=plays_offense&c1comp=gt&c1val=10&c2stat=choose&c2comp=gt&c3stat=choose&c3comp=gt&c4stat=choose&c4comp=gt&c5comp=choose&c5gtlt=lt&c6mult=1.0&c6comp=choose&order_by=game_date&order_by_asc=Y&offset={offset}"""
        return self.get(base_url.format(year_min=season_start, year_max=season_end, offset=offset))


    def week_positions(self, season, week, positions=['QB', 'RB', 'WR', 'TE'], slp=2):
        '''
        Gets one week of fantasy stats for all positions
        '''
        results = {p:'' for p in positions}
        for pos in positions:
            results[pos] = self._week_position(season, week, pos)

        return results

if __name__ == "__main__":
    pass
