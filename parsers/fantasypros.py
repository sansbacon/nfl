# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import re

from bs4 import BeautifulSoup

from nfl.scrapers.browser import BrowserScraper
from nfl.teams import long_to_code

class FantasyProsNFLParser(BrowserScraper):
    '''
    used to parse Fantasy Pros projections and ADP pages
    '''

    def __init__(self):
        '''

        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    @property
    def formats(self):
        return ['std', 'ppr', 'hppr']

    @property
    def positions(self):
        return set(self.std_positions + self.ppr_positions)

    @property
    def ppr_positions(self):
        return ['rb', 'wr', 'te', 'flex', 'qb-flex']

    @property
    def std_positions(self):
        return ['qb', 'k', 'dst']

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
        for tr in soup.find('table', {'id': 'data'}).find('tbody').find_all('tr'):
            player = {'source': 'fantasypros'}
            tds = tr.find_all('td')
            player['source_player_name'] = tds[1].find('a', {'class': 'player-name'}).text

            sm = tds[1].find_all('small')
            if sm and len(sm) == 2:
                player['source_team_code'] = sm[0].text
            elif sm:
                player['source_team_code'] = long_to_code(player['source_player_name'].split(' DST')[0].strip())
            else:
                player['source_team_code'] = 'UNK'

            # try to find player id
            try:
                a = tr.find('a', {'href': '#'})
                player['source_player_id'] = a.attrs.get('class')[-1].split('-')[-1]
            except:
                logging.exception('could not find playerid for {}'.format(player['source_player_name']))

            # get remaining stats
            posrk = tds[2].text
            player['position_rank'] = ''.join([s for s in posrk if s.isdigit()])
            player['source_player_position'] = ''.join([s for s in posrk if not s.isdigit()])
            player['adp'] = tds[-1].text

            # add to list
            players.append(player)

        return players

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
        results = []
        positions = ['QB', 'WR', 'TE', 'DST', 'RB']
        soup = BeautifulSoup(content, 'lxml')
        for tr in soup.find_all('tr', {'class': re.compile(r'mpb-player')}):
            player = {'source': 'fantasypros'}
            tds = tr.find_all('td')

            # tds[0]: rank
            player['source_player_rank'] = tds[0].text

            # tds[1]: player/id/team
            children = list(tds[1].children)
            player['source_player_name'] = children[0].text
            player['source_player_team'] = children[2].text
            a = tds[1].find('a', {'href': '#'})
            if a:
                try:
                    player['source_player_id'] = a.attrs['data-fp-id']
                except:
                    try:
                        player['source_player_id'] = a.attrs['class'][-1].split('-')[-1]
                    except (KeyError, ValueError) as e:
                        logging.exception(e)

            # tds[2]: opp
            player['source_player_opp'] = tds[2].text.split()[-1]

            # tds[3:7] data
            for k,v in zip(['best', 'worst', 'avg', 'stdev'], [td.text for td in tds[3:7]]):
                player[k] = v

            # get last updated
            try:
                player['source_last_updated'] = soup.select('h5 time')[0].attrs.get('datetime').split()[0]
            except:
                pass

            # <title>Week 1 QB Rankings, QB Cheat Sheets, QB Week 1 Fantasy Football Rankings</title>
            # but different locations on the half ppr and standard rankings pages
            title = soup.find('title')
            subtitle = title.text.split(', ')[0]
            week, pos = subtitle.split()[1:3]
            if week.isdigit and pos in positions:
                player['week'] = week
                player['pos'] = pos

            elif pos in positions:
                player['pos'] = pos
                h1 = soup.find('div', {'id': 'main'}).find('h1')
                if h1 and 'WEEK' in h1.text:
                    player['week'] = h1.text.split()[-1]
            else:
                for span in soup.find_all('span'):
                    if 'Week' in span.text:
                        player['week'] = span.text.split()[-1]
                for li in soup.find_all('li', {'class': 'active'}):
                    a = li.find('a')
                    if a:
                        player['pos'] = a.text

            results.append(player)

        return results

if __name__ == "__main__":
    pass