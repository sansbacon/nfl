'''
odds_test.py
'''

import re
import unittest

from bs4 import BeautifulSoup as BS, NavigableString

from nfl.dates import convert_format, datetostr
from nfl.scrapers.scraper import FootballScraper
from nfl.teams import city_to_code


class TestOdds(unittest.TestCase):

    def setUp(self):
        self.s = FootballScraper(cache_name='test-odds')

    '''
    def test_get(self):
        url = 'http://www.footballlocks.com/nfl_odds_week_1.shtml'
        content = self.s.get(url)
        self.assertIsNotNone(content)
        self.assertIsInstance(content, basestring)

    def test_parse(self):
        url = 'http://www.footballlocks.com/nfl_odds_week_1.shtml'
        content = self.s.get(url)
        soup = BS(content, 'lxml')
        for t in soup.find_all('table', {'width': 644, 'cellspacing': 0, 'cellpadding': 3}):
            print('match')

        for t in soup.find_all('table', {'cols': 6, 'width': 644, 'cellspacing': 6, 'border': 0}):
            print('match 2')
    '''

    def fix_odds(self, o):
        h = {'season_year': int(o['season_year']), 'week': int(o['week'])}
        v = {'season_year': int(o['season_year']), 'week': int(o['week'])}
        try:
            gd = o['game_date'].split(' ')[0] + '/' + str(o['season_year'])
            gd = convert_format(gd, 'nfl')
            h['game_date'] = gd
            v['game_date'] = gd
        except:
            h['game_date'] = datetostr(o['game_date'], 'nfl')
            v['game_date'] = h['game_date']
        try:
            fav = o['favorite']
            dog = o['underdog']

            if '(' in fav:
                h['team_code'] = city_to_code(fav.split('(')[0])
                h['opp'] = city_to_code(dog)
                if (o.get('line', None) == 'PK'):
                    o['line'] = 0
                h['consensus_spread'] = float(o['line'])
                h['consensus_game_ou'] = float(o['total'])
                v['team_code'] = h['opp']
                v['opp'] = h['team_code']
                v['consensus_spread'] = 0 - float(o['line'])
                v['consensus_game_ou'] = float(o['total'])

            elif '(' in dog:
                h['opp'] = city_to_code(fav)
                h['team_code'] = city_to_code(dog.split('(')[0])
                if (o.get('line', None) == 'PK'):
                    o['line'] = 0
                h['consensus_spread'] = 0 - float(o['line'])
                h['consensus_game_ou'] = float(o['total'])
                v['opp'] = h['team_code']
                v['team_code'] = h['opp']
                v['consensus_spread'] = float(o['line'])
                v['consensus_game_ou'] = float(o['total'])

            elif 'At ' in fav:
                h['team_code'] = city_to_code(fav.split('At ')[-1])
                h['opp'] = city_to_code(dog)
                if (o.get('line', None) == 'PK'):
                    o['line'] = 0
                h['consensus_spread'] = float(o['line'])
                h['consensus_game_ou'] = float(o['total'])
                v['team_code'] = h['opp']
                v['opp'] = h['team_code']
                v['consensus_spread'] = 0 - float(o['line'])
                v['consensus_game_ou'] = float(o['total'])

            elif 'At ' in dog:
                h['opp'] = city_to_code(fav)
                h['team_code'] = city_to_code(dog.split('At ')[-1])
                if (o.get('line', None) == 'PK'):
                    o['line'] = 0
                h['consensus_spread'] = 0 - float(o['line'])
                h['consensus_game_ou'] = float(o['total'])
                v['opp'] = h['team_code']
                v['team_code'] = h['opp']
                v['consensus_spread'] = float(o['line'])
                v['consensus_game_ou'] = float(o['total'])

        except Exception as e:
            print(e)

        return [h, v]

    def test_season(self):
        q = """
        INSERT INTO gamesmeta (season_year, week, game_date, team_code, opp, consensus_spread, consensus_game_ou)
        VALUES ({}, {}, '{}', '{}', '{}', {}, {});
        """
        url = 'http://www.footballlocks.com/nfl_odds_week_{}.shtml'
        for w in range(3,18):
            headers = ['game_date', 'favorite', 'line', 'underdog', 'total']
            content = self.s.get(url.format(w))
            patt = re.compile(r'Monday Night Football.*?(<TABLE.*?</TABLE>)', re.MULTILINE | re.DOTALL)
            match = re.search(patt, content)
            if match:
                soup = BS(match.group(1), 'lxml')
                trs = soup.find_all('tr')
                for tr in trs[1:]:
                    vals = [td.text.strip() for td in tr.find_all('td')][:-1]
                    d = dict(zip(headers, vals))
                    d['season_year'] = 2016
                    d['week'] = w
                    for i in self.fix_odds(d):
                        print q.format(i['season_year'], i['week'], i['game_date'],
                                       i['team_code'], i['opp'], i['consensus_spread'], i['consensus_game_ou'])


if __name__ == '__main__':
    unittest.main()