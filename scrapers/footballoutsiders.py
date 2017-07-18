import logging

from scraper import FootballScraper


class FootballOutsidersNFLScraper(FootballScraper):


    def dvoa_table(self, table):
        '''

        Args:
            table:

        Returns:

        '''
        teams = {}
        headers = ['def_rank', 'team', 'def_dvoa', 'def_rank_last_week', 'weighted_def', 'weighted_def_rank', 'pass_def', 'pass_rank', 'rush_def', 'rush_rank', 'na_total', 'na_pass', 'na_rush', 'var', 'var_rank', 'sched', 'sched_rank']

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
        headers = ['pass_rank', 'team', 'dvoa_wr1', 'dvoa_wr1_rank', 'ppg_wr1', 'ypg_wr1', 'dvoa_wr2', 'dvoa_wr2_rank', 'ppg_wr2', 'ypg_wr2', 'dvoa_wr3', 'dvoa_wr3_rank', 'ppg_wr3', 'ypg_wr3', 'dvoa_te', 'dvoa_te_rank', 'ppg_te', 'ypg_te', 'dvoa_rb', 'dvoa_rb_rank', 'ppg_rb', 'ypg_rb']

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


    def snap_counts(self, year, week):
        '''

        Args:
            year:
            week:

        Returns:

        '''
        url = 'http://www.footballoutsiders.com/stats/snapcounts'
        payload = {'team': 'ALL', 'week': week, 'pos': 'ALL', 'year': year, 'Submit': 'Submit'}
        return self.post(url, payload)


if __name__ == '__main__':    
    pass

