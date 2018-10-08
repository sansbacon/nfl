import logging
import re

from bs4 import BeautifulSoup, Comment
import demjson

from nfl.dates import convert_format
from nfl.names import first_last_pair
from nfl.utility import merge, digits


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

    def players(self, content):
        '''
        Returns alphabetical player page on nfl.com

        Args:
            content: HTML string   

        Returns:
            list of dict
        '''
        soup = BeautifulSoup(content, 'lxml')

    def esb_id(self, content):
        '''
        Gets player esb_id
        
        Args:
            content: 

        Returns:
            esb_id
        '''
        soup = BeautifulSoup(content, 'lxml')
        # GSIS ID and ESB ID are buried in the comments
        for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
            if 'GSIS' in c:
                parts = [part.strip() for part in c.split('\n')]
                return parts[2].split(':')[-1].strip()
        return None

    def player_page(self, content, profile_id):
        '''
        Returns data from individual player page
        
        Args:
            content: HTML string

        Returns:
            dict
        '''
        soup = BeautifulSoup(content, 'lxml')
        player = {}

        # GSIS ID and ESB ID are buried in the comments
        for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
            if 'GSIS' in c:
                parts = [part.strip() for part in c.split('\n')]
                esb_id = parts[2].split(':')[-1].strip()
                gsis_id = parts[3].split(':')[-1].strip()
                player['player_id'] = gsis_id
                player['profile_id'] = profile_id
                if esb_id:
                    player['esb_id'] = esb_id
                break

        # Most player data is found in the player-profile div
        # Then have to loop through paragraphs in that div
        paras = soup.find('div', {'id': 'player-profile'}).find_all('p')

        if not paras or len(paras) < 6:
            paras = soup.find('div', {'id': 'player-info'}).find_all('p')

        if not paras or len(paras) < 6:
            return None

        try:
            # paras[0]: name and number
            spans = paras[0].find_all('span')
            name = spans[0].text.strip()
            player['full_name'] = name
            player['first_name'], player['last_name'] = first_last_pair(name)
            number, pos = spans[1].text.split()
            player['number'] = digits(number)
            player['position'] = pos

            # paras[1]: team
            player['team'] = paras[1].find('a')['href'].split('=')[-1]
        except Exception as e:
            logging.exception(e)
            return None

        try:
            # paras[2]: height, weight, age
            parts = paras[2].text.split()
            feet,inches = parts[1].split('-')
            player['height'] = int(digits(feet)) * 6 + int(digits(inches))
            player['weight'] = digits(parts[3])
            player['age'] = digits(parts[5])
        except Exception as e:
            logging.exception(e)

        try:
            # birthdate
            parts = paras[3].text.split()
            player['birthdate'] = parts[1].strip()
        except Exception as e:
            logging.exception(e)

        try:
            # college
            parts = paras[4].text.split()
            player['college'] = parts[1].strip()
        except Exception as e:
            logging.exception(e)

        try:
            # years pro
            parts = paras[5].text.split()
            ordinal = parts[1].strip()
            player['years_pro'] = ''.join(ch for ch in ordinal if ch.isdigit())
        except Exception as e:
            logging.exception(e)

        # status
        player['status'] = 'Active'

        return player

    def player_search_name(self, content):
        '''
        Parses player search results

        Args:
            content(str): HTML page

        Returns:
            tuple - full_name, nfl_name, profile_id

        '''
        vals = []
        soup = BeautifulSoup(content, 'lxml')
        patt = re.compile(r'\/player.*?\d+\/profile', re.IGNORECASE | re.UNICODE)

        for a in soup.find_all('a', {'href': patt}):
            nfl_name, profile_id = a['href'].split('/')[-3:-1]
            vals.append((a.text, nfl_name, profile_id))
        return vals

    def position(self, content):
        '''
        Returns player's position from his profile page on nfl.com
        Args:
            content: HTML string   
        Returns:
            pos: 'QB', 'RB', 'WR', 'TE', 'UNK'
        '''
        allowed = ['C', 'CB', 'DB', 'DE', 'DL', 'DT', 'FB', 'FS', 'G', 'ILB',
                   'K', 'LB', 'LS', 'MLB', 'NT', 'OG', 'OL', 'OLB', 'OT',
                   'P', 'QB', 'RB', 'SAF', 'SS', 'T', 'TE', 'WR', 'UNK', 'DST']

        xref = {'ML': 'LB', 'IL': 'LB', 'SAF': 'S'}
        patt = re.compile(r'[A-Z]{1}.*?,\s+([A-Z]{1,3})', re.IGNORECASE | re.UNICODE)
        soup = BeautifulSoup(content, 'lxml')
        title = soup.title.text
        match = re.search(patt, title)
        try:
            pos = match.group(1)
            if pos in allowed:
                return pos
            else:
                return xref.get(pos, u'UNK')
        except:
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