import copy
import logging
import os
import re

from bs4 import BeautifulSoup


class PfrNFLParser():
    '''
    '''

    def __init__(self,**kwargs):
        '''

        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())


    def _merge_team_tables(self, offense, passing, rushing):
        '''
        Takes 3 dictionaries (offense, passing, rushing), returns merged dictionary
        '''
        
        teams = copy.deepcopy(offense)

        for t in offense:
            p = passing.get(t)

        for k,v in p.items():
            teams[t][k] = v

            r = rushing.get(t)

        for k,v in r.items():
            teams[t][k] = v

        return teams

    def _season_from_path(self, path):
        '''Extracts 4-digit season from path, each html file begins with season'''

        fn = os.path.split(path)[-1]
        return fn[0:4]


    def draft(self, content, season_year):
        '''
        Parses page of draft results for single season
        
        Args:
            content: HTML string of draft page
            season_year: int 2017, 2016, etc.

        Returns:
            players: list of dict
        '''
        players = []
        soup = BeautifulSoup(content, 'lxml')
        headers = ['draft_round', 'draft_overall_pick']
        t = soup.find('table', {'id': 'drafts'})
        for tr in t.find_all('tr'):
            p = {'draft_year': season_year, 'source': 'pfr'}

            # removes header rows for each draft round
            if tr.has_attr('class') and 'thead' in tr['class']:
                continue
            else:
                th = tr.find('th')
                p[th['data-stat']] = th.text
            tds = tr.find_all('td')
            if tds:
                p[tds[0]['data-stat']] = tds[0].text
                p[tds[1]['data-stat']] = tds[1].text

                # <td class="left " data-append-csv="RamcRy00" data-stat="player" csk="Ramczyk, Ryan"><a href="/players/R/RamcRy00.htm">Ryan Ramczyk</a></td>
                p[tds[2]['data-stat']] = tds[2]['csk']
                p['source_player_id'] = tds[2]['data-append-csv']
                players.append(p)

        return players

    def fantasy_week(self, content):
        '''
        Takes HTML of 100 rows of weekly results, returns list of players

        Args:
            content: HTML string

        Returns:
            players: list of player dict
        '''
        players = []
        soup = BeautifulSoup(content, 'lxml')
        tbl = soup.find('table', {'id': 'results'})
        if tbl:
            for tr in tbl.find('tbody').findAll('tr', class_=None):
                player = {td['data-stat']: td.text for td in tr.find_all('td')}
                a = tr.find('a', {'href': re.compile(r'/players/')})
                if a:
                    try:
                        player['source_player_id'] = a['href'].split('/')[-1].split('.')[:-1]
                    except:
                        pass
                players.append(player)

        return players

    def team_plays(self, content):
        '''
        Takes HTML of 100 rows of team plays, returns list of team_plays

        Args:
            content: HTML string

        Returns:
            teams: list of team dict
        '''
        teams = []
        headers = ['team', 'season_year', 'game_date', 'opp_team', 'week', 'game_number', 'is_win', 'is_ot',
                   'off_plays', 'def_plays', 'top']

        soup = BeautifulSoup(content, 'lxml')
        tbl = soup.find('table', {'id': 'results'})
        if tbl:
            for tr in tbl.find('tbody').findAll('tr', class_=None):
                teams.append({td['data-stat']: td.text for td in tr.find_all('td')})

        else:
            for tbl in soup.find_all('table'):
                logging.info(tbl.attrs)

        return teams


    def team_season(self, content, season):
        '''
        Takes HTML file of team stats during single season
        Returns dict, key is team_season, value is team
        '''

        soup = BeautifulSoup(content, 'lxml')   
        teams = {}
    
        offense = soup.find('table', {'id': 'team_stats'}).find('tbody')
        for tr in offense.findAll('tr'):
            team = {'season': season}
    
            for td in tr.findAll('td'):
                val = td.text
            
                # fix team name - has newline and extra space
                if '\n' in val:
                    val = ' '.join(val.split('\n'))
                    val = ' '.join(val.split())
                
                # column headers on page are duplicates (yds, td, etc.)    
                # data-stat attribute has accurate column name (rush_yds)
                team[td['data-stat']] = val
        
            k = team['team'] + "_" + season
            teams[k] = team

        """
        passing = soup.find('table', {'id': 'passing'}).find('tbody')
        for tr in passing.findAll('tr'):
            team = {'season': season}
        
            for td in tr.findAll('td'):
                val = td.text
                
                # fix team name - has newline and extra space
                if '\n' in val:
                    val = ' '.join(val.split('\n'))
                    val = ' '.join(val.split())
                    
                # column headers on page are duplicates (yds, td, etc.)    
                # data-stat attribute has accurate column name (rush_yds)
                team[td['data-stat']] = val

            k = team['team'] + "_" + season
            teams[k] = {**teams[k], **team}

        rushing = soup.find('table', {'id': 'rushing'}).find('tbody')

        for tr in rushing.findAll('tr'):
            team = {'season': season}
        
            for td in tr.findAll('td'):
                val = td.text
                
                # fix team name - has newline and extra space
                if '\n' in val:
                    val = ' '.join(val.split('\n'))
                    val = ' '.join(val.split())
                    
                # column headers on page are duplicates (yds, td, etc.)    
                # data-stat attribute has accurate column name (rush_yds)
                team[td['data-stat']] = val

            k = team['team'] + "_" + season
            teams[k] = {**teams[k], **team}
            
        return teams
        """

    def parse_season(self, content, season):
        soup = BeautifulSoup(content)

        players = []

        headers = [
            'rk', 'player', 'team', 'age', 'g', 'gs', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'rush_att',
            'rush_yds', 'rush_yds_per_att',
            'rush_td', 'targets', 'rec', 'rec_yds', 'rec_yds_per_rec', 'rec_td', 'fantasy_pos', 'fantasy_points',
            'draftkings_points', 'fanduel_points', 'vbd', 'fantasy_rank_pos', 'fantasy_rank_overall'
        ]

        t = soup.find('table', {'id': 'fantasy'})
        body = t.find('tbody')

        for row in body.findAll('tr'):
            values = [cell.text for cell in row.findAll('td')]

            # filter out header rows
            if 'Receiving' in values or 'Y/A' in values:
                continue

            player = (dict(zip(headers, values)))
            player['Season'] = season

            # fix *+ in name
            # add playerid
            link = row.find('a', href=re.compile(r'/players/'))

            if link:
                player['Player'] = link.text
                pid = link['href'].split('/')[-1]
                player['Id'] = pid[:-4]

            else:
                name = player.get('Player')
                if name:
                    name.replace('*', '')
                    name.replace('*', '+')
                    player['Player'] = name

            players.append(player)

        return players

if __name__ == "__main__":
    import logging
    import random
    import json
    from nfl.scrapers.pfr import PfrNFLScraper

    logging.basicConfig(level=logging.INFO)
    s = PfrNFLScraper()
    p = PfrNFLParser()
    players = []
    season_year = 2015
    for week in range(1, 2):
        for offset in [0, 100]:#, 200, 300]:
            try:
                content = s.fantasy_week(season_year, week, offset)
                if content:
                    week_players = p.fantasy_week(content)
                    if week_players:
                        players += week_players
                        logging.info('finished week {} offset {}'.format(week, offset))
            except Exception as e:
                logging.exception(e)

    if players:
        logging.info(random.sample(players, 3))
        #with open('/home/sansbacon/fantasy-2016.json', 'w') as outfile:
        #    json.dump(players, outfile)
    else:
        logging.error('no players')
