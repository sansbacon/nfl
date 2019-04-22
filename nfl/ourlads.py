"""

# ourlads.py
# classes for scraping, parsing ourlads football data

"""


import logging
import re

from sportscraper.scraper import RequestScraper


class Scraper(RequestScraper):
    """
    Scrape ourlads.com for football information

    """

    @property
    def source_team_codes(self):
        '''
        List of team_codes used by source

        Returns:
            list

        '''
        return [
            'ARZ',
            'ATL',
            'BAL',
            'BUF',
            'CAR',
            'CHI',
            'CIN',
            'CLE',
            'DAL',
            'DEN',
            'DET',
            'GB',
            'HOU',
            'IND',
            'JAX',
            'KC',
            'LAC',
            'LAR',
            'MIA',
            'MIN',
            'NE',
            'NO',
            'NYG',
            'NYJ',
            'OAK',
            'PHI',
            'PIT',
            'SEA',
            'SF',
            'TB',
            'TEN',
            'WAS'
        ]

    def depth_chart(self, source_team_code):
        """
        Gets team depth chart

        Args:
            source_team_code(str):

        Returns:
            str: HTML page

        """
        if source_team_code.upper() not in self.source_team_codes:
            raise ValueError('invalid team code %s', source_team_code)
        url = f'https://www.ourlads.com/nfldepthcharts/depthchart/{source_team_code.upper()}'
        return self.get(url)


class Parser:
    """
    Parse ourlads.com for football information

    """

    def __init__(self):
        """
        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    @classmethod
    def depth_chart(cls, response):
        """
        Parses depth chart page

        Args:
            response(requests_html.Response):

        Returns:
            list of dict

        """
        vals = []
        null_url = 'https://www.ourlads.com/nfldepthcharts/player/0/'

        for tr in response.html.find('tr'):
            tr_class = tr.attrs.get('class')
            if tr_class and tr_class[0] in ['row-dc-grey', 'row-dc-wht']:
                tds = tr.find('td')
                position = tds.pop(0).text
                depth_num = 1
                for td in tds:
                    if re.search('\d+', td.text):
                        continue
                    player = {'source_player_position': position, 'depth_num': depth_num}
                    a = td.find('a', first=True)
                    if a:
                        if a.attrs.get('href') == null_url:
                            continue
                        player['profile_url'] = a.attrs.get('href')
                        ln, fn = td.text.split(', '[0:2])
                        player['source_player_name'] = f'{fn.split()[0].title()} {ln.title()}'
                        vals.append(player)
                        depth_num += 1
        return vals


class Agent():
    '''
    Combines common scraping/parsing tasks

    '''
    def __init__(self, cache_name='ourlads-agent'):
        """
        Creates Agent object

        Args:
            cache_name(str): default 'ourlads-agent'

        """
        self._s = Scraper(cache_name=cache_name)

    def all_depth_charts(self):
        '''
        Gets all team depth charts

        Args:
            None

        Returns:
            dict

        '''
        team_depth_charts = {}
        for team_code in self._s.source_team_codes:
            response = self._s.depth_chart(team_code)
            team_depth_charts[team_code] = Parser.depth_chart(response)
        return team_depth_charts

    def depth_chart(self, source_team_code):
        '''
        Gets team depth chart

        Args:
            source_team_code(str):

        Returns:
            list: of dict

        '''
        response = self._s.depth_chart(source_team_code)
        return Parser.depth_chart(response)


if __name__ == "__main__":
    pass
