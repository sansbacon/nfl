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


    def weekTeamSeasonDvoa(self, year, week, pause=1):
        '''
        Weekly DVOA by team - includes ranks and weightings
    
        Argument: 
            year(int)
            week(int)
    
        '''
        base_url = 'http://www.footballoutsiders.com/premium/weekTeamSeasonDvoa.php?od=O&team=ARI&year={y}&week={w}'
        cols = ['team', 'wl', 'total_dvoa', 'total_dvoa_rank', 'weighted_dvoa', 'weighted_dvoa_rank', 'off_dvoa',
                'off_dvoa_rank',
                'weighted_off_dvoa', 'weighted_off_dvoa_rank', 'def_dvoa', 'def_dvoa_rank', 'weighted_def_dvoa',
                'weighted_def_dvoa_rank',
                'st_dvoa', 'st_dvoa_rank', 'weighted_st_dvoa', 'weighted_st_dvoa_rank']
        url = base_url.format(y=year, w=week)
        response = _get(url)
        extras = {'season': int(year), 'week': int(week)}

        if not response.from_cache:
            time.sleep(pause)

        if response.content:
            teams = _parse(response, cols, extras)

            for idx, team in enumerate(teams):
                wl = team.get('wl')

                if wl:
                    teams[idx]['w'], teams[idx]['l'] = wl.split('-')

            return teams

        else:
            return None


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


if __name__ == "__main__":
    pass