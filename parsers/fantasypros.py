# -*- coding: utf-8 -*-
import logging
import re

from bs4 import BeautifulSoup


class FantasyProsNFLParser(object):
    '''
    used to parse Fantasy Pros projections and ADP pages
    '''

    def __init__(self):
        '''

        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def _tr(self, tr, headers):
        '''
        Private method to parse tr element
        
        Args:
            tr: BeautifulSoup element
            headers: list of headers

        Returns:
            player
        '''
        vals = [td.text.strip() for td in tr.find_all('td')]
        player = dict(zip(headers, vals))
        teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAC',
                 'KC', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'OAK', 'PHI', 'PIT', 'SD', 'SEA', 'SF',
                 'STL', 'TB', 'TEN', 'WAS']

        # player_id in <a href="#" class="fp-player-link fp-id-11645" fp-player-name="Le'Veon Bell"></a>
        a = tr.find('a', {'href': '#'})
        if a:
            player['source_player_id'] = a.attrs['class'][-1].split('-')[-1]
            player['player'] = a['fp-player-name']

        # team and bye in <small></small>
        for child in tr.findChildren():
            if child.name == 'small':
                if child.text.strip() in teams:
                    player['team_code'] = child.text.strip()
                else:
                    player['bye'] = child.text.strip().replace(')', '').replace('(', '')
        return player

    def adp(self, content):
        '''
        Parses adp page
        
        Args:
            content: HTML string

        Returns:
            list of player dict
        '''
        players = []
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'data'})
        headers = ['rank', 'player', 'pos', 'yahoo', 'espn', 'cbs', 'ffc', 'nfl', 'fantrax', 'dw', 'avg']
        return [self._tr(tr, headers) for tr in t.find_all('tr')]

    def depth_charts(self, content, team, as_of=None):
        '''
        Team depth chart from fantasypros

        Args:
            content: HTML string
            team: string 'ARI', etc.
            as_of: datestr

        Returns:
            dc: list of dict
        '''
        dc = []
        soup = BeautifulSoup(content, 'lxml')
        for tr in soup.find_all('tr', {'class': re.compile(r'mpb')}):
            p = {'source': 'fantasypros', 'team_code': team, 'as_of': as_of}
            p['source_player_id'] = tr['class'][0].split('-')[-1]
            tds = tr.find_all('td')
            p['source_player_role'] = tds[0].text
            p['source_player_name'] = tds[1].text
            dc.append(p)
        return dc

    def draft_rankings_overall(self, content):
        '''
        Parses adp page

        Args:
            content: HTML string

        Returns:
            list of player dict
        '''
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'data'})
        headers = ['rank', 'player', 'pos', 'bye', 'best', 'worst', 'avg', 'stdev', 'adp', 'vs_adp']
        return [self._tr(tr, headers) for tr in t.find_all('tr', {'class': re.compile(r'mpb-player')})]

    def draft_rankings_position(self, content):
        '''
        Parses adp page
        
        Args:
            content: HTML string

        Returns:
            list of player dict
        '''
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'data'})
        headers = ['rank', 'player', 'bye', 'best', 'worst', 'avg', 'stdev', 'adp', 'vs_adp']
        return [self._tr(tr, headers) for tr in t.find_all('tr', {'class': re.compile(r'mpb-player')})]

    def projections(self, content, pos):
        '''
        Parses projections page

        Args:
            content: HTML string

        Returns:
            list of player dict
        '''
        pos = pos.upper()
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'data'})

        if pos == 'QB':
            headers = ['player', 'pass_att', 'pass_cmp', 'pass_yds', 'pass_td', 'pass_int',
                       'rush_att', 'rush_yds', 'rush_td', 'fl', 'fpts']
        elif pos == 'RB':
            headers = ['player', 'rush_att', 'rush_yds', 'rush_td', 'rcvg_rec', 'rcvg_yds', 'rcvg_tds', 'fl', 'fpts']
        elif pos == 'WR':
            headers = ['player', 'rush_att', 'rush_yds', 'rush_td', 'rcvg_rec', 'rcvg_yds', 'rcvg_tds', 'fl', 'fpts']
        elif pos == 'TE':
            headers = ['player', 'rcvg_rec', 'rcvg_yds', 'rcvg_tds', 'fl', 'fpts']
        elif pos == 'K':
            headers = ['player', 'fg', 'fga', 'xpt', 'fpts']
        elif pos == 'DST':
            headers = ['player', 'sack', 'int', 'fr', 'ff', 'td', 'assist', 'safety', 'pa', 'yds_agnst', 'fpts']

        return [self._tr(tr, headers) for tr in t.find_all('tr', {'class': re.compile(r'mpb-player')})]

    def weekly_rankings(self, content):
        '''
        Parses weekly rankings page for specific position

        Args:
            content: HTML string

        Returns:
            list of player dict
        '''
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'data'})
        headers = ['rank', 'player', 'opp', 'best', 'worst', 'avg', 'stdev']
        return [self._tr(tr, headers) for tr in t.find_all('tr', {'class': re.compile(r'mpb-player')})]

if __name__ == "__main__":
    pass