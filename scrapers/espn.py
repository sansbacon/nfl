# -*- coding: utf-8 -*-

from nflmisc.scraper import FootballScraper


class ESPNNFLScraper(FootballScraper):
    '''

    '''

    @property
    def fantasy_team_codes(self):
       return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
               23, 24, 25, 26, 27, 28, 29, 30, 33, 34]

    @property
    def fantasy_teams(self):
        return {
            1: 'Atl', 2: 'Buf', 3: 'Chi', 4: 'Cin', 5: 'Cle', 6: 'Dal', 7: 'Den', 8: 'Det',
            9: 'GB', 10: 'Ten', 11: 'Ind', 12: 'KC', 13: 'Oak', 14: 'LAR', 15: 'Mia', 16: 'Min',
            17: 'NE', 18: 'NO', 19: 'NYG', 20: 'NYJ', 21: 'Phi', 22: 'Ari', 23: 'Pit', 24: 'LAC',
            25: 'SF', 26: 'Sea', 27: 'TB', 28: 'Wsh', 29: 'Car', 30: 'Jax', 33: 'Bal',34: 'Hou'
        }

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

    def fantasy_players_team(self, team_code):
        '''
        Gets page with fantasy players by team

        Args:
            team_code: 1, 2, etc.

        Returns:
            HTML string
        '''
        if team_code not in self.fantasy_team_codes:
            raise ValueError('invalid team_code: {}'.format(team_code))
        url = 'view-source:http://games.espn.com/ffl/tools/projections?proTeamId={}'
        return self.get(url.format(team_code), encoding='latin1')

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

    def projections(self, pos, season_year=None, week=0, offset=0):
        '''
        Gets page with projections by position

        Args:
            pos: str qb, rb, wr, te, k, etc.
            season_year: int 2017, 2016
            week: int 1, 2, 3
            offset: int 0, 40, 80, etc.

        Returns:
            HTML string
        '''
        pos = pos.lower()
        slot_categories = {'qb': 0, 'rb': 2, 'wr': 4, 'te': 6, 'dst': 16, 'k': 17}
        max_offset = {'qb': 120, 'rb': 240, 'wr': 360, 'te': 160, 'dst': 0, 'k': 40}

        if pos not in slot_categories.keys():
            raise ValueError('invalid pos {}'.format(pos))
        elif offset > max_offset.get(pos):
            raise ValueError('invalid offset {}'.format(offset))
        elif offset % 40 > 0:
            raise ValueError('invalid offset {}'.format(offset))

        url = 'http://games.espn.com/ffl/tools/projections?'
        if season_year:
            params = {
                'slotCategoryId': slot_categories[pos],
                'startIndex': offset,
                'seasonId': season_year
            }
        else:
            params = {
                'slotCategoryId': slot_categories[pos],
                'startIndex': offset
            }

        if week:
            params['scoringPeriodId'] = week
        else:
            params['seasonTotals'] = 'true'

        return self.get(url, payload=params, encoding='latin1')

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

    def watson(self, pid):
        '''
        
        Args:
            pid: player ID (10000, etc.)

        Returns:
            dict - parsed JSON
        '''
        url = ('http://www.watsonfantasyfootball.com/espnpartner/dallasfantasyfootball/projections/'
               'projections_{}_ESPNFantasyFootball_2017.json')
        return self.get_json(url.format(pid))

    def watson_players(self):
        '''
        Gets list of ESPN fantasy football players for Watson projections
        
        Returns:
            dict - parsed JSON
        '''

        url = ('http://www.watsonfantasyfootball.com/espnpartner/dallasfantasyfootball/'
               'players/players_ESPNFantasyFootball_2017.json')
        return self.get_json(url)

    def weekly_scoring(self, season_year, week, position):
        '''
        Gets weekly fantasy scoring page

        Args:
            season_year (int): 2017, 2016, etc.
            week (int): 1 through 17
            position (str): 'qb', 'wr', etc.
            
        Returns:
            str: HTML
            
        '''
        poscode = {'qb': 0, 'rb': 2, 'wr': 4, 'te': 6, 'dst': 16, 'k': 17}
        if position.lower() not in poscode:
            raise ValueError('invalid position: {}'.format(position))
        url = 'http://games.espn.com/ffl/leaders?&'
        params = {'scoringPeriodId': week, 'seasonId': season_year, 'slotCategoryId': position}
        return self.get(url, payload=params)

if __name__ == "__main__":
    pass
