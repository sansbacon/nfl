import logging
import re

from bs4 import BeautifulSoup
import demjson

from nfl.dates import convert_format
from nfl.utility import merge


class NFLComParser(object):
    '''
    Used to parse NFL.com GameCenter pages, which are json documents with game and play-by-play stats
    '''

    def __init__(self):
        logging.getLogger(__name__).addHandler(logging.NullHandler())


    def _gamecenter_team(self, team):
        '''
        Parses home or away team into stats dictionary       
        Args:
            team: dictionary representing home or away team
        Returns:
            players: dictionary of team stats
        '''
        categories = ['passing', 'rushing', 'receiving', 'fumbles', 'kickret', 'puntret', 'defense']
        players = {}
        for category in categories:
            for player_id, player_stats in team[category].items():
                if not player_id in players:
                    players[player_id] = {'player_id': player_id}
                    players[player_id][category] = player_stats
        return players


    def gamecenter(self, parsed):
        '''
        Parses gamecenter (json document)
        Args:
            content: parsed json document
        Returns:
            dict            
        Misc:
            puntret: avg, lng, lngtd, name, ret, tds
            fumbles: lost, name, rcv, tot, trcv, yds
            defense: ast, ffum, int, name, sk, tkl
            rushing: att, lng.lngtd, name, tds, twopta, twoptm, yds
            receiving: lng, lngtd, name, rec, tds, twopta, twoptm, yds
            passing: att, cmp, ints, name, tds, twopta, twoptm, yds
        '''
        game_id = parsed.keys()[0]
        home_team_stats = self._gamecenter_team(parsed[game_id]['home']['stats'])
        away_team_stats = self._gamecenter_team(parsed[game_id]['away']['stats'])
        return merge(dict(),[home_team_stats, away_team_stats])

    def game_page(self, content):
        '''
        Parses individual game page from NFL.com

        Args:
            content: 

        Returns:
            teams: list of dict
        '''
        games = []
        soup = BeautifulSoup(content, 'lxml')

        for a in soup.findAll('a', {'class': 'game-center-link'}):
            game = {}
            pattern = re.compile(r'/gamecenter/(\d+)/(\d+)/REG(\d+)/([a-zA-Z0-9]+[@]{1}[a-zA-Z0-9]+)')
            match = re.search(pattern, a['href'])
            if match:
                game['gsis_id'], game['season_year'], game['week'], game['matchup'] = match.groups()
                game['away'], game['home'] = game['matchup'].split('@')
                game['game_date'] = convert_format(game['gsis_id'][0:8], 'nfl')
                game['url'] = 'http://www.nfl.com{}' + a['href']
            if game:
                games.append(game)
        return games

    def injuries(self, content, season, week):
        '''
        Returns injured players from injruies page
        Args:
            content: HTML string   
        Returns:
            list of player dict
        '''
        players = []
        away_patt = re.compile(r'dataAway.*?(\[.*?\]);',
                               re.MULTILINE | re.IGNORECASE | re.DOTALL)
        home_patt = re.compile(r'dataHome.*?(\[.*?\]);',
                               re.MULTILINE | re.IGNORECASE | re.DOTALL)
        awayAbbr_patt = re.compile(r'awayAbbr\s+=\s+\'([A-Z]+)\'')
        homeAbbr_patt = re.compile(r'homeAbbr\s+=\s+\'([A-Z]+)\'')

        soup = BeautifulSoup(content, 'lxml')

        # values are embedded in <script> tag
        # I am trying to scrape the homeAbbr and awayAbbr variables
        for script in soup.find_all('script'):
            try:
                # get away and home team codes
                match = re.search(awayAbbr_patt, script.text)
                if match:
                    away_team = match.group(1)

                match = re.search(homeAbbr_patt, script.text)
                if match:
                    home_team = match.group(1)

                # away team
                away_player = {'team_code': away_team, 'season_year': season, 'week': week}
                match = re.search(away_patt, script.text)
                if match:
                    for player in demjson.decode(match.group(1)):
                        context = away_player.copy()
                        context.update(player)
                        players.append(context)

                # home team
                home_player = {'team_code': home_team, 'season_year': season, 'week': week}
                match = re.search(home_patt, script.text)
                if match:
                    for player in demjson.decode(match.group(1)):
                        context = home_player.copy()
                        context.update(player)
                        players.append(context)
            except:
                pass

        return players

    def ol(self, content):
        '''
        Parses offensive line stats page on nfl.com
        
        Args:
            content: HTML string   

        Returns:
            teams
        '''
        soup = BeautifulSoup(content, 'lxml')
        headers = ['rank', 'team', 'experience', 'rush_att', 'rush_yds', 'rush_ypc', 'rush_tds',
                   'rush_fd_left', 'rush_neg_left', 'rush_pty_left', 'rush_pwr_left',
                   'rush_fd_center', 'rush_neg_center', 'rush_pty_center', 'rush_pwr_center',
                   'rush_fd_right', 'rush_neg_right', 'rush_pty_right', 'rush_pwr_right', 'sacks', 'qb_hits']

        return [dict(zip(headers, [td.text.strip() for td in tr.find_all('td')]))
                for tr in soup.find('table', {'id': 'result'}).find('tbody').find_all('tr')]


    def position(self, content):
        '''
        Returns player's position from his profile page on nfl.com
        Args:
            content: HTML string   
        Returns:
            pos: 'QB', 'RB', 'WR', 'TE', 'UNK'
        '''
        patt = re.compile(r'[A-Z]{1}.*?,\s+([A-Z]{1,2})', re.IGNORECASE | re.UNICODE)
        soup = BeautifulSoup(content, 'lxml')
        title = soup.title.text
        match = re.search(patt, title)
        if match:
            return match.group(1)
        else:
            return u'UNK'

    def upcoming_week_page(self, content):
        '''
        Parses upcoming week page for 2017 season

        Args:
            content: 

        Returns:
            result: list of game dict
        '''
        games = []
        wanted = ['data-game-id', 'data-away-abbr', 'data-home-abbr', 'data-gc-url', 'data-localtime', 'data-site']
        soup = BeautifulSoup(content, 'lxml')
        for div in soup.select('div.schedules-list-content'):
            games.append({att: div[att] for att in div.attrs if att in wanted})
        return games

    def week_page(self, content):
        '''
        Parses weekly scoreboard page from NFL.com
    
        Args:
            content: 
    
        Returns:
            games: dict of gsis_id and dict
        '''
        games = []
        soup = BeautifulSoup(content, 'lxml')

        # weekly page will have links to individual games in format:
        # <a href="/gamecenter/2014090400/2014/REG1/packers@seahawks" class="game-center-link" . . . </a>
        for a in soup.findAll('a', {'class': 'game-center-link'}):
            game = {}
            pattern = re.compile(r'/gamecenter/(\d+)/(\d+)/REG(\d+)/([a-zA-Z0-9]+[@]{1}[a-zA-Z0-9]+)')
            match = re.search(pattern, a['href'])
            if match:
                game['gsis_id'], game['season_year'], game['week'], game['matchup'] = match.groups()
                game['away'], game['home'] = game['matchup'].split('@')
                game['game_date'] = convert_format(game['gsis_id'][0:8], 'nfl')
                game['url'] = 'http://www.nfl.com{}' + a['href']
            if game:
                games.append(game)

        return games


if __name__ == "__main__":
    pass