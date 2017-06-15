# -*- coding: utf-8 -*-
from collections import deque
import logging
import re

from bs4 import BeautifulSoup


class FantasyProsNFLParser(object):
    '''
    used to parse Fantasy Pros projections and ADP pages
    '''

    def __init__(self, **kwargs):

        if 'logger' in kwargs:
            self.logger = kwargs['logger']
        else:
            self.logger = logging.getLogger(__name__)

    def _wr_flex(self, t, season, week, position='flex'):
        '''
        Different table structure for flex vs. positional rankings
        Args:
            t:
            season:
            week:
            position:

        Returns:
            players(list): of player dict
        '''
        players = []
        headers = ['weekly_rank', 'site_player_id', 'site_player_name', 'team', 'best', 'worst', 'avg', 'stdev']
        for tr in t.findAll('tr'):
            td = tr.find('td')

            # skip these rows without further processing
            if not td: continue
            if td.text and re.match(r'[A-Z]+', td.text): continue

            # rank in td[0]
            td = tr.find('td')
            if td:
                rank = td.text
            else:
                rank = None

            # most pages have 2 links, easiest to parse 2nd link that has no text
            a = tr.find('a', class_='fp-player-link')
            if a and a.has_attr('fp-player-name'):
                site_player_name = a['fp-player-name']
            else:
                site_player_name = None
            if a and a.has_attr('class'):
                site_player_id = a['class'][-1].split('-')[-1]
            else:
                site_player_id = None

            if not site_player_name:
                a = tr.find('a')
                if a: site_player_name = a.text

            # player team wrapped in <small> element
            if tr.find('small'):
                match = re.match(r'\(([A-Z]+)\)', tr.find('small').text)
                if match:
                    team = match.group(1)
                else:
                    team = tr.find('small').text
                    if team: team = team.strip().split(' ')[0].replace('(', '').replace(')', '')

            # need best, worst, ave, std tds[2:]
            tds = tr.findAll('td', {'class': re.compile(r'tier')})
            if tds:
                summ = [td.text.strip() for td in tds]
            else:
                summ = [td.text.strip() for td in tr.findAll('td')[3:]]

            # zip up and add
            player = dict(zip(headers, [rank, site_player_id, site_player_name, team] + summ))
            player['season'] = season
            player['week'] = week
            player['pos'] = position
            player['site'] = 'fantasypros'
            players.append(player)

        return players

    def _wr_no_flex(self, t, season, week, position):
        '''
        Different table structure for flex vs. positional rankings
        Args:
            t:
            season:
            week:
            position:

        Returns:
            players(list): of player dict

        '''
        return [t, season, week, position]


    def depth_charts(self, content, team, as_of=None):
        '''
        Team depth chart from fantasypros
        
        Args:
            content: HTML string
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

    '''
    def weekly_rankings(self, content, season, week, position):
        players = []
        content = content.replace("\xc2\xa0", "")
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', id='data')
        headers = ['weekly_rank', 'site_player_id', 'site_player_name', 'team', 'best', 'worst', 'avg', 'stdev']
        for tr in t.findAll('tr'):
            td = tr.find('td')

            # skip these rows without further processing
            if not td: continue
            if td.text and re.match(r'[A-Z]+', td.text): continue

            # rank in td[0]
            td = tr.find('td')
            if td:
                rank = td.text
            else:
                rank = None

            # most pages have 2 links, easiest to parse 2nd link that has no text
            a = tr.find('a', class_='fp-player-link')
            if a and a.has_attr('fp-player-name'):
                site_player_name = a['fp-player-name']
            else:
                site_player_name = None
            if a and a.has_attr('class'):
                site_player_id = a['class'][-1].split('-')[-1]
            else:
                site_player_id = None

            if not site_player_name:
                a = tr.find('a')
                if a: site_player_name = a.text

            # player team wrapped in <small> element
            if tr.find('small'):
                match = re.match(r'\(([A-Z]+)\)', tr.find('small').text)
                if match:
                    team = match.group(1)
                else:
                    team = tr.find('small').text
                    if team: team = team.strip().split(' ')[0].replace('(', '').replace(')', '')

            # need best, worst, ave, std tds[2:]
            tds = tr.findAll('td', {'class': re.compile(r'tier')})
            if tds:
                summ = [td.text.strip() for td in tds]
            else:
                summ = [td.text.strip() for td in tr.findAll('td')[3:]]

            # zip up and add
            player = dict(zip(headers, [rank, site_player_id, site_player_name, team] + summ))
            player['season'] = season
            player['week'] = week
            player['pos'] = position
            player['site'] = 'fantasypros'
            players.append(player)

        return players

    def weekly_rankings(self, content, season, week, position):
        TODO: need to write parsing routine for flex rankings page
        TODO: need to adjust for standard, half-ppr, and ppr
              add column to weekly_rankings table and adjust the unique constratint accordingly
        Args:
            content:
            season:
            week:
            position:

        Returns:  

        content = content.replace("\xc2\xa0", "")
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', id='data')

        if position == 'flex':
            return self._wr_flex(t, season, week)
        else:
            return self._wr_no_flex(t, season, week, position)

    
        def weekly_rankings_html(content):
            players = []
            soup = BeautifulSoup(content, 'lxml')
            t = soup.find('table', id='data')
            headers = ['rank', 'site_player_id', 'site_player_name', 'team', 'best', 'worst', 'ave', 'stdev']
            for tr in t.findAll('tr'):
                vals = []
                td = tr.find('td')
                if not td:
                    next
                elif td.text and re.match(r'[A-Z]+', td.text):
                    next
                else:
                    tds = tr.findAll('td')
                    rank = tds[0].text
                    a = tr.find('a')
                    if a:
                        cl = a.get('class', None)
                        if cl:
                            site_player_id = a['class'].split('-')[-1]
                        else:
                            site_player_id = None
                        ppn = a.get('pf-player-name', None)
                        if ppn:
                            site_player_name = ppn
                        else:
                            site_player_name = a.text
                        matchup = tr.find('small')
                        if matchup:
                            match = re.match(r'\(([A-Z]+)\)', matchup.text)
                            if match:
                                team = match.group(1)
                            else:
                                team = matchup.text.strip().split(' ')[0].replace('(', '').replace(')', '')
                        else:
                            team = matchup.text

                        print(rank, site_player_id, site_player_name, team)

    '''


    def weekly_flex_rankings(self, content, season, week, scoring_type):
        soup = BeautifulSoup(content, 'lxml')
        tbody = soup.find('table', {'id': 'data'}).find('tbody')

        players = []

        for tr in tbody.find_all('tr'):
            player = {'site': 'fantasypros', 'season': season, 'week': week, 'scoring_type': scoring_type,
                      'ranking_type': 'flex'}
            a = tr.find('a', {'href': re.compile(r'/nfl/players')})
            if a:
                player['site_player_name'] = a.text.strip()

            cls = tr.get('class')
            if cls and len(cls) > 0:
                player['site_player_id'] = cls[0].split('-')[-1]

            tds = deque(tr.find_all('td'))
            if tds and len(tds) == 8:
                player['flex_rank'] = tds.popleft().text.strip()
                player['team'] = tds.popleft().find('small').text.strip()
                player['position_rank'] = tds.popleft().text.strip()
                player['opp'] = tds.popleft().text.strip()
                player['best'] = tds.popleft().text.strip()
                player['worst'] = tds.popleft().text.strip()
                player['avg'] = tds.popleft().text.strip()
                player['stdev'] = tds.popleft().text.strip()
                players.append(player)

        return players


    def _average_adp(self, values):
        '''
        Takes list of values, returns average after dropping high/lows if 4 or more, just average otherwise
        :param values (list):
        :return average (float):
        '''

        if len(values) < 4:
            return sum(values) / float(len(values))

        else:
            values.sort()
            trimmed = values[1:-1]
            return sum(trimmed) / float(len(trimmed))


    def _headers_from_csv(self, header_trigger, content=None, fname=None):
        '''
        Parses csv content or file and returns header row and line number of header row
        :param header_trigger (str): something that appears in header line that identifies it
        :param content: fetch .csv from web
        :param fname: fetch .csv from file
        :return: headers (list): List of headers from .csv file
        '''

        # the csv file has a number of lines to skip before header line
        n = 0
        if content:
            for line in content.splitlines():
                n += 1

                if header_trigger in line:
                    headers = [x.strip() for x in line.split('\t') if x is not None and x is not ""]
                    break
        elif fname:
            # first time around just skipping irrelevant lines, going to header lines
            # save value of 'n' for reading later on
            with open(fname, "rU") as f:
                for line in f.readlines():
                    n += 1

                    if header_trigger in line:
                        headers = [x.strip() for x in line.split('\t') if x is not None and not x == '']
                        break

                f.close()
        else:
            raise ValueError('must pass content or fname')

        return headers, n


    def _parse_adp_row(self, row):
        '''
        Private method converts row to dictionary, calculates average ADP
        :param row: from csv.dictreader
        :return player(dictionary: row parsed into dictionary + calculated field
        '''

        player = {}
        values = []

        for k in row.keys():
            value = row.get(k, None)

            if value is not None and re.match(r'\d+', value):
                try:
                    player[k] = float(value)
                    values.append(player[k])
                except:
                    player[k] = value
                    logging.debug('key is %s, value is %s of type %s' % (k, player[k], type(player[k])))

            elif value is not None and not value == '':
                player[k] = value

        if len(values) < 4:
            player['average_adp'] = sum(values) / float(len(values))

        else:
            values.sort()
            trimmed = values[1:-1]
            player['average_adp'] = sum(trimmed) / float(len(trimmed))

        return player


    def adp(self, content=None, fname=None):
        '''
        Parses csv and returns list of player dictionaries
        Args:
            content (str): csv typically fetched by FantasyProsNFLScraper class
            fname (str): path to local csv file
        Returns:
            List of dictionaries if successful, empty list otherwise.
        '''

        players = []
        header_trigger = 'ESPN'

        if content:
            headers, n = self._headers_from_csv(header_trigger=header_trigger, content=content)
            headers = self.fix_headers(headers)
            lines = islice(content.splitlines(), n, None)

            reader = csv.DictReader(lines, fieldnames=headers, dialect=csv.excel_tab)
            for row in reader:
                player = self._parse_adp_row(row)
                players.append(player)

        elif fname:
            # the csv file has a number of lines to skip before header line
            # will open and read the file twice, 2nd time around take slice starting after header line

            # use fix_headers to try to standardize across sites (although not perfect)
            headers, n = self._headers_from_csv(fname=fname, header_trigger='ESPN')
            headers = self.fix_headers(headers)
            f = islice(open(fname, "rU"), n, None)
            reader = csv.DictReader(f, fieldnames=headers, dialect=csv.excel_tab)

            for row in reader:
                player = self._parse_adp_row(row)
                players.append(player)

        else:
            raise ValueError('must pass content or fname parameter')

        return players


    def fix_header(self, header):
        '''
        Looks at global list of headers, can provide extras locally
        :param headers:
        :return:
        '''

        fixed = {
            'Rank': 'overall_rank',
            'Player Name': 'full_name',
            'Position': 'position',
            'Team': 'team',
            'Bye Week': 'bye',
            'Best Rank': 'best_rank',
            'Worst Rank': 'worst_rank',
            'Worst Rank': 'worst_rank',
            'Avg Rank': 'average_rank',
            'Std Dev': 'stdev_rank',
            'ADP': 'adp'
        }

        # TODO: normal pattern was not working
        # return fixed.get(header, header)
        fixed_header = self._fix_header(header)
        logging.debug('parser._fix_header fixed header')
        logging.debug(fixed_header)

        # fixed_header none if not found, so use local list
        if not fixed_header:
            return fixed.get(header, header)

        else:
            return fixed_header


    def fix_headers(self, headers):
        return [self.fix_header(header) for header in headers]


    def _player_page(self, content, pos):
        '''
        Parses page of fantasypros players
    
        Args:
            content(str):
    
        Returns:
            players(list): of player dict, keys: pos, site, site_player_id, site_player_name
        '''

        players = []
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'data'})
        tbody = t.find('tbody')
        pattern = re.compile(r'mpb-player-(\d+)')

        for tr in tbody.findAll('tr', {'class': pattern}):
            p = {'site': 'fantasypros', 'pos': pos}

            sm = tr.find('small', {'class': 'grey'})
            if sm:
                p['team'] = sm.text

            a = tr.find('a', {'href': re.compile(r'/nfl/players')})
            try:
                match = re.match(pattern, tr['class'][0])
                if match:
                    p['site_player_id'] = match.group(1)
                    p['site_player_name'] = a.text
                    players.append(p)

            except Exception as e:
                logging.exception(e)

        return players


    def players(self, dir):
        '''
        Arguments:
            dir(str): directory where HTML files located
    
        Returns:
            players (list): dict with player_id from nfl.players
    
        Usage:
            p = FantasyProsNFLParser()
            players = p.players('/home/sansbacon/fpros')
            with open('fpros-players.json', 'w') as outfile:
                json.dump(players, outfile)
        '''
        players = []
        base_fname = os.path.join(dir, '{}.html')
        for pos in ['QB', 'RB', 'TE', 'WR']:
            fname = base_fname.format(pos.lower())
            if os.path.exists(fname):
                with open(fname, 'r') as infile:
                    players += self._player_page(infile.read(), pos)

        return players


    def _parse_projections_rows(self, reader):
        players = []

        for row in reader:
            row = {k: v for k, v in row.items() if k and v}

            # fantasypros lists position as RB1, QB2, so need to strip numbers
            row['position'] = ''.join(i for i in row['position'] if not i.isdigit())

            # standardize names for lookup
            full_name, first_last = NameMatcher.fix_name(row['full_name'])
            row['full_name'] = full_name
            row['first_last'] = first_last
            players.append(row)

        return players


    def projections(self, content=None, fname=None):
        header_trigger = 'ADP'

        if content:

            # the csv file has a number of lines to skip before header line
            headers, n = self._headers_from_csv(content=content, header_trigger=header_trigger)
            headers = self.fix_headers(headers)
            lines = islice(content.splitlines(), n, None)
            reader = csv.DictReader(lines, fieldnames=headers, dialect=csv.excel_tab)
            players = self._parse_projections_rows(reader)

        elif fname:

            # the csv file has a number of lines (n) to skip before header line
            headers, n = self._headers_from_csv(fname=fname, header_trigger=header_trigger)
            headers = self.fix_headers(headers)
            lines = islice(content.splitlines(), n, None)
            reader = csv.DictReader(lines, fieldnames=headers, dialect=csv.excel_tab)
            players = self._parse_projections_rows(reader)

        else:
            raise ValueError('must pass content or fname parameter')

        return players


if __name__ == "__main__":
    #from nfl.scrapers.scraper import FootballScraper
    #s = FootballScraper(cache_name='fpros')

    import requests
    from httpcache import CachingHTTPAdapter
    s = requests.Session()
    s.mount('http://', CachingHTTPAdapter())
    r = s.get('https://www.fantasypros.com/nfl/depth-chart/arizona-cardinals.php')
    parser = FantasyProsNFLParser()
    print parser.depth_charts(content=r.content, team='ARI', as_of='20170221')
    #pass
