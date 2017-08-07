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

                try:
                    # <td class="left " data-append-csv="RamcRy00" data-stat="player" csk="Ramczyk, Ryan"><a href="/players/R/RamcRy00.htm">Ryan Ramczyk</a></td>
                    p[tds[2]['data-stat']] = tds[2]['csk']
                    p['source_player_id'] = tds[2]['data-append-csv']
                except:
                    try:
                        # /players/C/CarrDa00.htm
                        a = tr.find('a', {'href': re.compile(r'/players/')})
                        p['source_player_id'] = a['href'].split('.htm')[0].split('/')[-1]
                    except:
                        pass
            if p.get('source_player_id'):
                players.append(p)
            else:
                logging.error('missing id: {}'.format(p))

        return players

    def fantasy_week(self, content, season_year=None):
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
                if season_year:
                    player['season_year'] = season_year

                a = tr.find('a', {'href': re.compile(r'/players/')})
                if a:
                    try:
                        pid = a['href'].split('/')[-1].split('.')[:-1]
                        pid = pid[0]
                        player['source_player_id'] = pid
                    except:
                        pass
                players.append(player)

        return players

    def players(self, content):
        '''
        Parses page of players with same last initial (A, B, C, etc.) 

        Args:
            content: HTML string

        Returns:
            list of dict
        '''
        results = []
        soup = BeautifulSoup(content, 'lxml')
        for p in soup.select('div#div_players p'):
            try:
                player = {'source': 'pfr'}
                name, posyears = p.text.split('(')
                pos, years = posyears.split(')')
                player['source_player_name'] = name.strip()
                player['source_player_position'] = pos.strip()
                player['source_player_years'] = years.strip()
                a = p.find('a')
                if a:
                    id = a['href'].split('/')[-1].split('.htm')[0]
                    player['source_player_id'] = id.strip()
                results.append(player)
            except:
                pass

        return results

    def player_fantasy_season(self, content, season_year=None):
        '''
        Parses player fantasy page for season
        
        Args:
            content: HTML string
            season_year: 2016, etc.

        Returns:
            list of dict
        '''
        players = []
        soup = BeautifulSoup(content, 'lxml')

        try:
            for tr in soup.find('table', {'id': 'player_fantasy'}).find('tbody').find_all('tr'):
                player = {td['data-stat']: td.text for td in tr.find_all('td')}
                if season_year:
                    player['season_year'] = season_year
                players.append(player)
        except Exception as e:
            logging.exception(e)

        return players

    def player_page(self, content, pid):
        '''
        Parses player page 

        Args:
            content: HTML string

        Returns:
            dict: source, source_player_id, source_player_name, 
                  source_player_position, source_player_dob
        '''
        player = {'source': 'pfr', 'source_player_id': pid}
        soup = BeautifulSoup(content, 'lxml')

        #source_player_name
        h1 = soup.find('h1', {'itemprop': 'name'})
        if h1:
            player['source_player_name'] = h1.text

        #source_player_position
        try:
            meta = soup.find('meta', {'name': 'Description'})
            metac = meta.attrs.get('content')
            player['source_player_position'] = metac.split(',')[0].split(': ')[-1]
        except:
            pass

        # source_player_dob
        span = soup.find('span', {'id': 'necro-birth'})
        if span:
            player['source_player_dob'] = span.attrs.get('data-birth')

        return player

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

    def team_defense_weekly(self, content):
        '''
        Team defense stats for single week

        Args:
            content: HTML string

        Returns:
            teams: list of dict
        '''
        teams = []
        soup = BeautifulSoup(content, 'lxml')
        defense = soup.find('table', {'id': 'results'}).find('tbody')
        for tr in defense.findAll('tr'):
            teams.append({td['data-stat']: td.text for td in tr.find_all('td')})
        return teams

    def team_defense_yearly(self, content, season_year=None):
        '''
        Team defense stats for total season

        Args:
            content: HTML string

        Returns:
            teams: list of dict
        '''
        teams = []
        soup = BeautifulSoup(content, 'lxml')
        defense = soup.find('table', {'id': 'team_stats'}).find('tbody')
        for tr in defense.findAll('tr'):
            team = {td['data-stat']: td.text for td in tr.find_all('td')}
            if season_year:
                team['season_year'] = season_year
            teams.append(team)
        return teams

    def team_offense_weekly(self, content):
        '''
        
        Args:
            content: HTML string

        Returns:
            teams: list of dict
        '''
        teams = []
        soup = BeautifulSoup(content, 'lxml')
        offense = soup.find('table', {'id': 'results'}).find('tbody')
        for tr in offense.findAll('tr'):
            teams.append({td['data-stat']: td.text for td in tr.find_all('td')})
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
        return teams

if __name__ == "__main__":
    pass