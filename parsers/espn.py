# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import logging
import re

from bs4 import BeautifulSoup

from nfl.teams import nickname_to_code

class ESPNNFLParser(object):

    def __init__(self):
        '''
        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())

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

    def _val(self, val):
        '''
        Converts non-numeric value to numeric 0
        
        Args:
            val: 

        Returns:
            number
        '''
        if '--' in val:
            return 0
        else:
            return val

    def adp(self, content):
        '''
        Parses season-long ADP
        
        Args:
            content: 

        Returns:
            list of dict
        '''
        players = []
        soup = BeautifulSoup(content, 'lxml')
        colors = ['#f2f2e8', '#f8f8f2']
        for row in [tr for tr in soup.find_all('tr') if tr.attrs.get('bgcolor') in colors]:
            player = {'source': 'espn'}
            tds = row.find_all('td')

            # tds[0]: rank
            player['position_rank'] = tds[0].text

            # tds[1]: name/team/pos
            try:
                a, navstr = list(tds[1].children)[0:2]
                player['source_player_name'] = a.text.replace('*','')
                player['season_year'] = a.attrs.get('seasonid')
                player['source_player_id'] = a.attrs.get('playerid')
                player['source_team_code'] = navstr.split(', ')[-1].strip()
            except:
                a = tds[1].find('a')
                player['source_player_name'] = a.text
                player['season_year'] = a.attrs.get('seasonid')
                player['source_player_id'] = a.attrs.get('playerid')
                player['source_team_code'] = nickname_to_code(a.text.split(' D/ST')[0], int(player['season_year']))

            # remaining stats
            player['source_player_position'] = tds[2].text
            player['adp'] = tds[3].text

            players.append(player)

        return players

    def fantasy_players_team(self, content):
        '''
        Parses page of fantasy players
        
        Args:
            content: HTML string

        Returns:
            list of players
        '''
        players = {}
        soup = BeautifulSoup(content, 'lxml')
        for a in soup.find_all('a', {'class': 'flexpop'}):
            pid = a.attrs.get('playerid')
            pname = a.text.strip()
            if pid and pname:
                players[pid] = pname

        return players

    def lovehate(self, season, week, lh):
        '''

        Args:
            season(int):
            week(int):
            d(dict): keys are position_love, position_hate

        Returns:
            players(list): of player dict
        '''

        players = []

        for poslh, ratings in lh.items():
            pos = poslh.split('_')[0]
            label = ratings.get('label')
            sublabel = None

            if label in ('favorite', 'bargain', 'desparate'):
                sublabel = label
                label = 'love'
            for link in ratings.get('links'):
                url = link.split('"')[1]
                site_player_id, site_player_stub = url.split('/')[7:9]
                site_player_name = link.split('>')[1].split('<')[0]

        #print season, week, pos, label, sublabel, site_player_id, site_player_stub, site_player_name

    def projections(self, content, pos):
        '''
        Parses ESPN fantasy football season-long sortable projections page

        Args:
            content: HTML string

        Returns:
            list of dict
        '''
        players = []
        soup = BeautifulSoup(content, 'lxml')

        if pos.lower() in ['qb', 'rb', 'wr', 'te', 'flex']:
            headers = [
                'pass_att', 'pass_cmp', 'pass_yds', 'pass_td', 'pass_int',
                'rush_att', 'rush_yds', 'rush_td', 'rec', 'rec_yds', 'rec_td',
                'fantasy_points_ppr'
            ]

            for row in soup.findAll("tr", {"class": "pncPlayerRow"}):
                player = {'source': 'espn'}

                tds = row.find_all('td')

                # tds[0]: rank
                player['source_position_rank'] = tds[0].text

                # tds[1]: name/team/pos
                a, navstr = list(tds[1].children)[0:2]
                player['source_player_name'] = a.text
                player['source_player_team'], player['source_player_position'] = navstr.split()[-2:]
                player['source_player_id'] = a.attrs.get('playerid')

                # loop through stats
                # they have attempts/completions in one column so have to remove & split
                attcmp = tds[2].text
                vals = [self._val(td.text) for td in tds[3:]]
                for h, v in zip(headers, attcmp.split('/') + vals):
                    player[h] = v
                players.append(player)

        elif pos.lower() == 'k':
            for row in soup.findAll("tr", {"class": "pncPlayerRow"}):
                player = {'source': 'espn'}
                tds = row.find_all('td')

                # tds[0]: rank
                player['source_position_rank'] = tds[0].text

                # tds[1]: name/team/pos
                a, navstr = list(tds[1].children)[0:2]
                player['source_player_name'] = a.text
                player['source_player_team'], player['source_player_position'] = navstr.split()[-2:]
                player['source_player_id'] = a.attrs.get('playerid')

                # loop through stats
                # they have attempts/completions in one column so have to remove & split
                player['fantasy_points_ppr'] = self._val(tds[-1].text)
                players.append(player)
        else:
            pass

        return players

    def players_position(self, content, pos):
        '''
        Parses page of ESPN players by position

        Args:
            content: 
            pos: 

        Returns:
            list of dict: source, source_player_id, source_player_name
                          source_team_code, source_team_name, college
        '''
        players = []
        soup = BeautifulSoup(content, 'lxml')
        # <tr class="oddrow player-28-2574511"><td><a href="http://www.espn.com/nfl/player/_/id/2574511/brandon-allen">
        # #Allen, Brandon</a></td><td><a href="http://www.espn.com/nfl/team/_/name/jax/jacksonville-jaguars">
        # Jacksonville Jaguars</a></td><td>Arkansas</td></tr>

        for tr in soup.find_all('tr'):
            class_matches = set(['oddrow', 'evenrow'])
            classes = set(tr.attrs.get('class', []))
            if class_matches.intersection(classes):
                player = {'source': 'espn', 'source_player_position': pos}
                tds = tr.find_all('td')

                # tds[0]: <a href="http://www.espn.com/nfl/player/_/id/2574511/brandon-allen">Allen, Brandon</a>
                player['source_player_name'] = tds[0].text
                a = tr.find('a', {'href': re.compile(r'/player/_/')})
                if a:
                    match = re.search(r'\/id\/([0-9]+)', a['href'])
                    if match:
                        player['source_player_id'] = match.group(1)

                # tds[1]: <td><a href="http://www.espn.com/nfl/team/_/name/jax/jacksonville-jaguars">Jacksonville Jaguars</a></td>
                player['source_team_name'] = tds[1].text
                a = tr.find('a', {'href': re.compile(r'/team/_/name')})
                if a:
                    match = re.search(r'name/(\w+)/', a['href'])
                    if match:
                        player['source_team_code'] = match.group(1)

                # tds[2]: <td>Arkansas</td>
                player['college'] = tds[2].text

                # add to list
                players.append(player)

        return players

    def team_roster(self, content):
        '''
        Parses team roster page into list of player dict

        Args:
            content: HTML of espn nfl team roster page

        Returns:
            list of dict
        '''
        players = []
        soup = BeautifulSoup(content, 'lxml')
        for tr in soup.find_all('tr'):
            a = tr.find('a', {'href': re.compile(r'/nfl/player/_/id/')})
            if a:
                player = {'source': 'espn'}
                tds = tr.find_all('td')
                player['source_player_position'] = tds[2].text
                player['source_player_name'] = a.text
                player['source_player_id'] = a['href'].split('/')[-2]
                players.append(player)
        return players

if __name__ == "__main__":
    pass
