# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division


from nfl.scrapers.scraper import FootballScraper


class ESPNNFLScraper(FootballScraper):
    '''

    '''
    def _check_pos(self, pos):
        '''
        Makes sure pos is valid and uppercase
        '''
        if pos in ['qb', 'rb', 'wr', 'te', 'dst', 'd/st', 'k',
               'QB', 'RB', 'WR', 'TE', 'K', 'D/ST', 'DST']:
            if pos in ['DST', 'dst']:
                return 'D/ST'
            else:
                return pos.upper()
        else:
            raise ValueError('invalid position: {}'.format(pos))

    def adp(self, pos):
        '''
        Gets adp by player position
        
        Args:
            pos: 'qb', 'rb', etc.

        Returns:
            HTML string
        '''
        pos = self._check_pos(pos)
        url = 'http://games.espn.com/ffl/livedraftresults?position={}'
        return self.get(url.format(pos), encoding='latin1')

    def players_position(self, pos):
        '''
        Gets page with all players by position

        Args:
            pos: qb, rb, wr, te, k, etc.

        Returns:
            HTML string
        '''
        url = 'http://www.espn.com/nfl/players?position={}&league=nfl'
        return self.get(url.format(pos), encoding='latin1')

    def projections(self, pos, offset=0):
        '''
        Gets page with projections by position

        Args:
            pos: qb, rb, wr, te, k, etc.

        Returns:
            HTML string
        '''

        pos = pos.lower()

        slot_categories = {
            'qb': 0,
            'rb': 2,
            'wr': 4,
            'te': 6,
            'dst': 16,
            'k': 17
        }

        max_offset = {
            'qb': 120,
            'rb': 240,
            'wr': 360,
            'te': 160,
            'dst': 0,
            'k': 40
        }

        if pos not in slot_categories.keys():
            raise ValueError('invalid pos {}'.format(pos))

        if offset > max_offset.get(pos):
            raise ValueError('invalid offset {}'.format(offset))

        url = 'http://games.espn.com/ffl/tools/projections?slotCategoryId={}&startIndex={}'
        return self.get(url.format(slot_categories[pos], offset), encoding='latin1')

    def team_roster(self, team_code):
        '''
        Gets list of NFL players from ESPN.com

        Args:
            team_code: str 'DEN', 'BUF', etc.

        Returns:
            HTML string
        '''
        url = 'http://www.espn.com/nfl/team/roster/_/name/{}'
        return self.get(url=url.format(team_code), encoding='latin1')


if __name__ == "__main__":
    pass
