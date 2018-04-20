# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup


class FootballDatabaseNFLParser(object):
    '''

    '''

    def dst_yearly_scoring(self, content, fdb_d=None):
        '''
        Args:
            content (str): HTML 
            fdb_d (dict): player cross-reference dictionary, key is source_player_id

        Returns:
            list: of dict

        '''
        results = []
        headers = [['fantasy_points', 'sacks', 'interceptions', 'safeties',
                    'fumbles_recovered', 'blocked_kicks',
                    'touchdowns', 'points_allowed',
                    'passing_yards', 'rushing_yards', 'total_yards']]
        soup = BeautifulSoup(content, 'lxml')
        # position, year are found in options that are selected
        pos, y = [opt['value'] for opt in soup.find_all('option', selected=True)][0: 2]
        for tr in soup.select('table.statistics')[0].find_all('tr', class_=['row0', 'row1']):
            tds = tr.find_all('td')
            player = {'season_year': y, 'source_player_position': pos,
                      'source': 'footballdatabase', 'dst_scoring_format': 'footballdatabase_standard'}
            player['source_player_name'], player['source_team_id'] = [sp.text for sp in tds[0].find_all('span')]
            player['source_player_id'] = tr.find('a')['href'].split('/')[3]
            for h, v in zip(headers, [td.text for td in tds[2:]]):
                player[h] = v
            if fdb_d:
                match = fdb_d.get(player['source_player_id'])
                if match:
                    player['nflcom_player_id'] = match['nflcom_player_id']
                    player['nflcom_team_id'] = match['nflcom_team_id']
        results.append(player)

    def dst_weekly_scoring(self, content, fdb_d=None):
        '''
        Args:
            content (str): HTML 
            fdb_d (dict): player cross-reference dictionary, key is source_player_id

        Returns:
            list: of dict
            
        '''
        results = []
        headers = [['fantasy_points', 'sacks', 'interceptions', 'safeties',
                    'fumbles_recovered', 'blocked_kicks',
                    'touchdowns', 'points_allowed',
                    'passing_yards', 'rushing_yards', 'total_yards']]
        soup = BeautifulSoup(content, 'lxml')
        # position, year, and week are found in options that are selected
        pos, y, w = [opt['value'] for opt in soup.find_all('option', selected=True)][0: 3]
        for tr in soup.select('table.statistics')[0].find_all('tr', class_=['row0', 'row1']):
            tds = tr.find_all('td')
            player = {'season_year': y, 'week': w, 'source_player_position': pos,
                      'source': 'footballdatabase', 'dst_scoring_format': 'footballdatabase_standard'}
            player['source_player_name'], player['source_team_id'] = [sp.text for sp in tds[0].find_all('span')]
            player['source_player_id'] = tr.find('a')['href'].split('/')[3]
            for h, v in zip(headers, [td.text for td in tds[2:]]):
                player[h] = v
            if fdb_d:
                match = fdb_d.get(player['source_player_id'])
                if match:
                    player['nflcom_player_id'] = match['nflcom_player_id']
                    player['nflcom_team_id'] = match['nflcom_team_id']
        results.append(player)


if __name__ == "__main__":
    pass