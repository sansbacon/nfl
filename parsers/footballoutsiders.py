# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from requests_html import HTML


class FootballOutsidersNFLParser(object):
    '''

    '''

    def dl(self, content, season_year):
        # there can be 2 teams listed on one row b/c pass and rush usually not the same team

        rush_headers = ['rush_rank', 'team', 'adj_line_yards', 'rb_yards', 'power_success', 'power_rank', 'stuffed',
                        'stuffed_rank', 'sec_level_yards', 'sec_level_rank', 'open_field_yards', 'open_field_rank']
        pass_headers = ['team', 'pass_rank', 'sacks', 'adj_sack_rate']

        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'class': 'stats'})
        teams = {}

        # skip first two lines - double headers
        for tr in t.find_all('tr')[2:]:
            tds = tr.find_all('td')
            if len(tds) != len(rush_headers) + len(pass_headers):
                continue

            # rushing
            rvals = [str(td.string).replace('%', '').strip() for td in tds[0:12]]
            team = rvals[1]
            if teams.get(team):
                for idx, h in enumerate(rush_headers):
                    if h == 'team':
                        continue
                    else:
                        teams[team][h] = rvals[idx]
            else:
                teams[team] = dict(zip(rush_headers, rvals))

            # passing
            pvals = [str(td.string).replace('%', '').strip() for td in tds[12:]]
            team = pvals[0]
            if teams.get(team):
                for idx, h in enumerate(pass_headers):
                    if h == 'team':
                        continue
                    else:
                        teams[team][h] = pvals[idx]
            else:
                teams[team] = dict(zip(pass_headers, pvals))

            teams[team]['season_year'] = season_year

        return teams.values()

    def drive(self, content, offdef):
        '''

        Args:
            content: 

        Returns:

        '''
        teams = {}
        soup = BeautifulSoup(content, 'lxml')

        if offdef == 'off':
            #headers = ['team', 'team_net', 'yds_dr_net', 'pts_dr_net', 'dsr_off', 'yds_dr_off',
            #           'yds_dr_off', 'pts_dr_off', 'dsr_def', 'yds_dr_def', 'pts_dr_def', 'dsr']
            headers = [['team', 'drives', 'yds_dr', 'pts_dr', 'tov_dr', 'int_dr', 'fum_dr', 'los_dr',
                       'plays_dr', 'top_dr', 'dsr'], ['team', 'drives', 'tds_dr', 'fg_dr', 'punts_dr', 'tao_dr', 'los_ko', 'td_fg',
                        'pts_rz', 'tds_rz', 'avg_lead']]
        elif offdef == 'def':
            headers = []
        else:
            raise ValueError('invalid value for offdef: {}'.format(offdef))

        # get the first table and skip header lines
        for t, h in zip(soup.select('table.stats'), headers):
            for tr in t.find_all('tr'):
                if tr.find('td').text == 'Team':
                    continue
                else:
                    vals = [td.text.split()[0] for td in tr.find_all('td')]
                    if len(vals) == len(h):
                        context = teams.get(vals[0], {})
                        context.update(dict(zip(h, vals)))
                        teams[vals[0]] = context
                    else:
                        raise ValueError('too many values: {}'.format(vals))
        return teams

    def ol(self, content, season_year):
        '''
        
        Args:
            content: 

        Returns:

        '''
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'class': 'stats'})
        rush_headers = ['rush_rank', 'team', 'adj_line_yards', 'rb_yards', 'power_success', 'power_rank', 'stuffed',
                        'stuffed_rank', 'sec_level_yards', 'sec_level_rank', 'open_field_yards', 'open_field_rank']
        pass_headers = ['team', 'pass_rank', 'sacks', 'adj_sack_rate']

        teams = {}

        # skip first two lines - double headers
        for tr in t.find_all('tr')[2:]:
            tds = tr.find_all('td')
            if len(tds) != len(rush_headers) + len(pass_headers):
                continue

            # rushing
            rvals = [str(td.string).replace('%', '').strip() for td in tds[0:12]]
            team = rvals[1]
            if teams.get(team):
                for idx, h in enumerate(rush_headers):
                    if h == 'team':
                        continue
                    else:
                        teams[team][h] = rvals[idx]
            else:
                teams[team] = dict(zip(rush_headers, rvals))

            # passing
            pvals = [str(td.string).replace('%', '').strip() for td in tds[12:]]
            team = pvals[0]
            if teams.get(team):
                for idx, h in enumerate(pass_headers):
                    if h == 'team':
                        continue
                    else:
                        teams[team][h] = pvals[idx]
            else:
                teams[team] = dict(zip(pass_headers, pvals))

            teams[team]['season_year'] = season_year

        return teams.values()

    def qb(self, content):
        '''
        TODO: fix headers        
        Args:
            content: 

        Returns:

        '''
        teams = []
        soup = BeautifulSoup(content, 'lxml')
        headers = ['team', 'team_net', 'yds_dr_net', 'pts_dr_net', 'dsr_off', 'yds_dr_off',
                   'yds_dr_off', 'pts_dr_off', 'dsr_def', 'yds_dr_def', 'pts_dr_def', 'dsr']

        # skip first line
        for tr in soup.select('table.stats tr')[1:]:
            pass
            # Player	Team	DYAR	Rk	YAR	Rk	DVOA	Rk	VOA	QBR	Rk	Pass	Yards	EYds	TD	FK	FL	INT	C%	DPI	ALEX


    def snapcounts(self, content, season_year=None, week=None):
        '''
        
        Args:
            content (str): HTML from snapcounts page 
            season_year (int): 2017, etc.
            week (int): 1, 2, etc.

        Returns:
            list: of dict
            
        '''
        results = []
        doc = HTML(html=content)
        t = doc.html.find('#dataTable')[0]
        hdrs = [th.text.lower().strip().replace(' ', '_') for th in t.find('th')]
        for tr in t.find('tbody')[0].find('tr'):
            item = dict(zip(hdrs, [td.text.strip() for td in tr.find('td')]))
            if season_year:
                item['season_year'] = season_year
            if week:
                item['week'] = week
            results.append(item)
        return results


if __name__ == "__main__":
    pass