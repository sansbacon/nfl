# -*- coding: utf-8 -*-
import logging
import re

from bs4 import BeautifulSoup


class FootballOutsidersNFLParser(object):
    '''

    '''

    def dl(self, content, season, week):
        # there can be 2 teams listed on one row b/c pass and rush usually not the same team

        rush_headers = ['rush_rank', 'team', 'adj_line_yards', 'rb_yards', 'power_success', 'power_rank', 'stuffed',
                        'stuffed_rank', 'sec_level_yards', 'sec_level_rank', 'open_field_yards', 'open_field_rank']
        pass_headers = ['team', 'pass_rank', 'sacks', 'adj_sack_rate']

        soup = BeautifulSoup(content)
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
            if teams.has_key(team):
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
            if teams.has_key(team):
                for idx, h in enumerate(pass_headers):
                    if h == 'team':
                        continue
                    else:
                        teams[team][h] = pvals[idx]
            else:
                teams[team] = dict(zip(pass_headers, pvals))

            teams[team]['season_year'] = season
            teams[team]['week'] = week

        return teams.values()

    def snap_counts(self, content, season, week):
        players = []
        headers = ['player', 'team', 'position', 'started', 'total_snaps', 'off_snaps', 'off_snap_pct', 'def_snaps', 'def_snap_pct', 'st_snaps', 'st_snap_pct']
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'dataTable'})
        tb = t.find('tbody')

        for row in tb.find_all('tr'):
            cells = [td.text.strip() for td in row.find_all('td')]
            player = dict(zip(headers, cells))
            player['season'] =  season
            player['week'] = week
            players.append(player)

        return players


    def home_road_dvoa(self, years, teams, sides=['o', 'd']):
        '''
        NEED TO UPDATE
        '''
        base_url = 'http://www.footballoutsiders.com/premium/homeRoadDvoa.php?od={od}&year={y}&team={t}&week={w}'
        cols = ['team', 'home_dvoa', 'home_rank', 'road_dvoa', 'road_rank', 'total_dvoa', 'total_rank']
        hrDvoa = []

        for year in years:
            for team in teams:
                for side in sides:
                    url = base_url.format(y=year, w=week, t=team, od=side)

                    try:
                        filename = 'homeRoadDVOA-{y}_{w}_{t}.json'.format(y=year, w=week, t=team)
                        response = s.get(url, cookies=cj)
                        response.raise_for_status()

                    except requests.HTTPError:
                        print 'could not fetch {0}'.format(url)

                    finally:
                        time.sleep(.5)

                    if response.content:
                        try:
                            soup = BeautifulSoup(response.content, 'lxml')
                            table = soup.find('table', {'id': 'dataTable'})
                            trs = table.findAll('tr')

                            teamDvoa = []

                            for tr in trs[1:]:
                                vals = [td.text for td in tr.findAll('td')]
                                teamWeekDvoa = dict(zip(cols, vals))
                                teamWeekDvoa['season'] = year
                                teamWeekDvoa['team'] = team
                                teamDvoa.append(teamWeekDvoa)

                            hrDvoa += teamDvoa

                            with open(os.path.join(dldir, filename), 'w') as outfile:
                                json.dump(teamDvoa, outfile)

                        except Exception, e:
                            print 'error in processing response: {}'.format(e)

        return hrDvoa


    def one_team_line_yards(self, teams, sides=['o', 'd']):
        '''
        NEED TO UPDATE
        '''
        otly = []
        base_url = 'http://www.footballoutsiders.com/premium/oneTeamLineYards?od={od}&year={y}&team={t}&week=1'
        cols = ['year', 'adj_line_yds', 'adj_line_yds_rank', 'rb_yds', 'rb_yds_rank', 'power_success', 'power_success_rank',
                'power_success_nfl_avg', 'open_field_yds', 'open_field_yds_rank', 'open_field_yds_nfl_avg', 'sec_level',
                'sec_level_rank', 'sec_level_nfl_avg', 'stuffed', 'stuffed_rank', 'stuffed_nfl_avg', 'adj_sack_rate',
                'adj_sack_rate_rank', 'adj_sack_rate_sacks']

        for team in teams:
            for side in sides:
                url = base_url.format(y=year, t=team, od=side)

                try:
                    filename = 'otly-{t}_{s}.json'.format(s=side, t=team)
                    response = s.get(url, cookies=cj)
                    response.raise_for_status()

                except requests.HTTPError:
                    print 'could not fetch {0}'.format(url)

                finally:
                    if response.from_cache:
                        print 'got from cache'
                    else:
                        time.sleep(.5)

                if response.content:
                    try:
                        soup = BeautifulSoup(response.content, 'lxml')
                        table = soup.find('table', {'id': 'dataTable'})
                        trs = table.findAll('tr')

                        for tr in trs[1:]:
                            vals = [td.text.replace('%', '') for td in tr.findAll('td')]
                            t = dict(zip(cols, vals))
                            t['team'] = team
                            t['side'] = side
                            otly.append(t)

                    except Exception, e:
                        print 'error in processing response: {}'.format(e)

        return otly


    def weekByTeam(self, year, team, pause=1):
        '''
        Weekly DVOA by team by season
    
        Argument: 
            year(int)
            team(str)
    
        '''
        base_url = 'http://www.footballoutsiders.com/premium/weekByTeam.php?year={y}&team={t}&od=O&week=1'
        cols = ['week', 'opponent', 'total_dvoa', 'off_dvoa', 'off_pass_dvoa', 'off_rush_dvoa',
                'def_dvoa', 'def_pass_dvoa', 'def_rush_dvoa', 'st_dvoa']

        url = base_url.format(y=year, t=team)
        response = _get(url)
        extras = {'season': int(year), 'team': team}

        if not response.from_cache:
            time.sleep(pause)

        if response.content:
            return _parse(response, cols, extras)
        else:
            return None


    def weekTeamSeasonDvoa(self, content, year, week):
        '''
        Weekly DVOA by team - includes ranks and weightings
    
        Argument: 
            year: int
            week: int
    
        '''
        results = []
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'dataTable'})
        thead = t.find('thead')
        headers = [th.text for th in thead.find_all('th')]
        for tr in t.find('tbody').find_all('tr'):
            result = dict(zip(headers, [td.text for td in tr.find_all('td')]))
            result['season_year'] = 2016
            result['week'] = week
            results.append(result)

        return results


    def weekly_dvoa(self, years, weeks, teams):
        ''' need to merge 2 resources:
                weekTeamSeasonDvoa
                weekByTeam
        '''

        results = []

        for year in years:
            logging.debug(year)
            wtsds = []
            wbts = []
            combined = []

            for week in weeks:
                logging.debug(week)
                wtsds += weekTeamSeasonDvoa(year, week)

            for team in teams:
                logging.debug(team)
                wbts += weekByTeam(year, team)

            # combine results
            for wtsd in wtsds:
                for wbt in wbts:
                    if (int(wtsd['season']) == int(wbt['season']) and wtsd['team'] == wbt['team'] and int(
                            wtsd['week']) == int(wbt['week'])):
                        z = wtsd.copy()
                        z.update(wbt)
                        results.append(z)

        return results


# -*- coding: utf-8 -*-

import logging

import pandas as pd
import xlrd


class FootballOutsidersNFLParser2(object):
    '''
    Parses xls file of fantasy projections from footballoutsiders.com into player dictionaries

    Example:
        p = FootballOutsidersNFLParser(projections_file='KUBIAK.xls')
        players = p.projections()
    '''

    def __init__(self, projections_file, **kwargs):
        '''
        Args:
            projections_file(str)
            **kwargs: wanted_sheets(list of str): the sheets in the workbook you want to scrape
        '''

        self.projections_file = projections_file

        if 'wanted_cols' in 'kwargs':
            self.wanted_cols = kwargs['wanted_cols']
        else:
            self.wanted_cols = ['player', 'team', 'bye', 'pos', 'age', 'risk', 'dynamic fantasy points',
                                'position rank', 'auction value']

        if 'wanted_sheets' in 'kwargs':
            self.wanted_sheets = kwargs['wanted_sheets']
        else:
            self.wanted_sheets = ['2015 KUBIAK Projections']

    def _is_not_def(self, val):
        '''
        Exclude players of position IDP
        :param val:
        :return boolean:
        '''

        if val.lower() == 'd':
            return False
        else:
            return True

    def _is_not_idp(self, val):
        '''
        Exclude players of position IDP
        :param val:
        :return boolean:
        '''

        if 'IDP' in val:
            return False
        else:
            return True

    def _is_not_kicker(self, val):
        '''
        Exclude players of position IDP
        :param val:
        :return boolean:
        '''

        if val.lower() == 'k':
            return False
        else:
            return True

    def _parse_row(self, sheet, rowidx, column_map):
        '''
        Private method  
        :param sheet(xlrd worksheet object):
        :return players (list of dictionary):
        '''

        cells = []

        # loop through list of columns you want to scrape
        for column in self.wanted_cols:
            colidx = column_map.get(column, None)

            if colidx is not None:
                cell_value = str(sheet.cell(rowidx, colidx).value)
                cells.append(cell_value)
            else:
                logging.error('could not find column index for %s' % column)

        fixed_column_names = self._fix_headers(self.wanted_cols)
        player = dict(zip(fixed_column_names, cells))
        first_last, full_name = NameMatcher.fix_name(player['full_name'])
        player['first_last'] = first_last
        player['full_name'] = full_name
        logging.debug('player is %s' % player)
        return player

    def _parse_sheet(self, sheet):
        '''
        Private method  
        :param sheet(xlrd worksheet object):
        :return players (list of dictionary):
        '''

        players = []

        # get the column_map, key is name and value is index
        column_map = self._column_map(sheet)

        for rowidx in range(1, sheet.nrows):

            position_colidx = column_map.get('pos', None)
            position = str(sheet.cell(rowidx, position_colidx).value)

            if position_colidx:
                if self._is_not_idp(position) and self._is_not_kicker(position) and self._is_not_def(position):
                    player = self._parse_row(sheet=sheet, rowidx=rowidx, column_map=column_map)
                    players.append(player)
                else:
                    logging.debug('skipped %s' % position)
            else:
                logging.error('no position_colidx')

        return players

    def projections(self):
        '''

        :return players(list of dictionary): player dictionaries
        '''

        wb = xlrd.open_workbook(self.projections_file)

        players = []

        for sheet in wb.sheets():
            if sheet.name in self.wanted_sheets:
                players = players + self._parse_sheet(sheet)

        return players

    def _unwanted_columns(self):
        return ['Key', 'Picked', 'Rush', 'Ru', 'Rec', '300', '100', '100', 'Kick', 'XP', 'FG', 'FG Miss', 'Def',
                'Tot Tkl', 'Tkl', 'Ast', 'Sack', 'D-Int', 'Pass Def', 'Fum For', 'Fum Rec', 'TD', '-',
                'Sack', 'D-Int', 'Fum Forc', 'Fum Recd', 'Saf', 'Def TD', 'Shut out', 'PA 1-6',
                'PA 7-13', 'PA 14-20', 'PA 21-27', 'PA 28-34', 'PA 35+', 'NYA 0-199', 'NYA 200-249', 'NYA 259-299',
                'NYA 300-349', 'NYA 350-399', 'NYA 400-449', 'NYA 450-499', 'NYA 500+', '3 And Out', 'Spec Team',
                'Kick Ret Yds', 'Punt Ret Yds', 'Sp Team TDs', 'Other', 'Pass C%', 'YD/ATT', 'Net Y/P', 'YD/Run',
                'YD/Rec', '-', 'Risk', 'Playoff Adjust', 'Dynamic Fantasy Points', 'FPoints Over Baseline',
                'FPOB Rank', 'FPOB %', 'Position Rank', 'ESPN Rank', 'ESPN Delta', 'Yahoo Rank', 'Yahoo Delta',
                'ADP Rank', 'ADP Delta', 'FPOB Auction', 'Auction Value', 'Current Auction Value']

    def _fo_headers(self, header):
        ''',
        Standardizes headers from KUBIAK projections
        Assumes have already deleted unwanted columns
        '''

        fo = {
            'player': 'player_name',
            'fo id': 'site_player_id',
            'att': 'pass_att',
            'com': 'pass_cmp',
            'int': 'pass_int',
            'patd': 'pass_td',
            'payd': 'pass_yds',
            'pass dvoa': 'pass_dvoa',
            'rctd': 'rec_td',
            'rcyd': 'rec_yds',
            'rec dvoa': 'rec_dvoa',
            'rec c%': 'rec_cperc',
            'pass targets': 'pass_targets',
            'rutd': 'rush_td',
            'ruyd': 'rush_yds',
            'run dvoa': 'rush_dvoa',
            'fumb': 'fumbles'
        }

        return fo.get(header.lower(), header.lower())

    def fo(self, fn):
        try:
            df = pd.read_csv(fn)
            df.rename(columns=lambda x: _fo_headers(x), inplace=True)
            df['site'] = 'footballoutsiders'
            df.age = pd.to_numeric(df.age, errors='coerce')

            # percentage columns: pass_dvoa, rush_dvoa, rec_dvoa, rec_cperc
            for col in ['pass_dvoa', 'rush_dvoa', 'rec_dvoa', 'rec_cperc']:
                df[col] = df[col].apply(lambda x: str(x))
                df[col] = df[col].apply(lambda x: float(x.strip('%')) / 100)

            # fix nan
            df1 = df.where((pd.notnull(df)), None)

            # return list of dictionaries
            return df1[df1['pos'].isin(['QB', 'WR', 'TE', 'RB'])].T.to_dict().values()

        except Exception as e:
            logging.exception(e)
            return None

        def dvoa_table(self, table):
            '''

            Args:
                table:

            Returns:

            '''
            teams = {}
            headers = ['def_rank', 'team', 'def_dvoa', 'def_rank_last_week', 'weighted_def', 'weighted_def_rank',
                       'pass_def', 'pass_rank', 'rush_def', 'rush_rank', 'na_total', 'na_pass', 'na_rush', 'var',
                       'var_rank', 'sched', 'sched_rank']

            for row in table.findAll('tr')[2:]:
                if 'WEIGHTED' in row.get_text() or 'DVOA' in row.get_text():
                    pass
                else:
                    values = [td.get_text().strip() for td in row.findAll('td')]

                    if len(values[0]) > 0:
                        team = dict(zip(headers, values))
                        team_name = team['team']
                        teams[team_name] = team
            return teams

    def passing_table(self, table):
        '''

        Args:
            table:

        Returns:

        '''
        teams = {}
        headers = ['pass_rank', 'team', 'dvoa_wr1', 'dvoa_wr1_rank', 'ppg_wr1', 'ypg_wr1', 'dvoa_wr2',
                   'dvoa_wr2_rank', 'ppg_wr2', 'ypg_wr2', 'dvoa_wr3', 'dvoa_wr3_rank', 'ppg_wr3', 'ypg_wr3',
                   'dvoa_te', 'dvoa_te_rank', 'ppg_te', 'ypg_te', 'dvoa_rb', 'dvoa_rb_rank', 'ppg_rb', 'ypg_rb']

        # skip 2 rows which are headers
        for row in table.findAll('tr')[2:]:
            if 'DVOA' or 'TOTAL' in row.get_text():
                pass
            else:
                values = [td.get_text().strip() for td in row.findAll('td')]
                team = dict(zip(headers, values))
                team_name = team['team']
                teams[team_name] = team
        return teams


if __name__ == "__main__":
    pass