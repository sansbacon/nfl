from __future__ import absolute_import, print_function, division

from nfl.scrapers.scraper import FootballScraper


class FantasyProsNFLScraper(FootballScraper):

    '''
    '''

    def adp(self, fmt):
        '''
        Gets ADP page        

        Args:
            fmt: 'std', 'ppr'

        Returns:
            content: HTML string of page
        '''
        if fmt == 'std':
            url = 'https://www.fantasypros.com/nfl/adp/overall.php'
        elif fmt == 'ppr':
            url = 'https://www.fantasypros.com/nfl/adp/ppr-overall.php'
        else:
            raise ValueError('invalid format: {}'.format(fmt))

        return self.get(url)

    def draft_rankings(self, pos, fmt):
        '''
        Gets draft rankings page

        Args:
            pos: 'qb', 'rb', 'wr', 'te', 'flex', 'qb-flex', 'k', 'dst'
            fmt: 'std', 'ppr', 'hppr'

        Returns:
            content: HTML string of page
        '''
        std_positions = ['qb', 'k', 'dst']
        ppr_positions = ['rb', 'wr', 'te', 'flex', 'qb-flex']
        formats = ['std', 'ppr', 'hppr']
        if fmt not in formats:
            raise ValueError('invalid format: {}'.format(fmt))

        if pos in std_positions:
            url = 'https://www.fantasypros.com/nfl/rankings/{pos}-cheatsheets.php'

        elif pos in ppr_positions:
            if fmt == 'std':
                url = 'https://www.fantasypros.com/nfl/rankings/{pos}-cheatsheets.php'
            elif fmt == 'ppr':
                url = 'https://www.fantasypros.com/nfl/rankings/ppr-{pos}-cheatsheets.php'
            elif fmt == 'hppr':
                url = 'https://www.fantasypros.com/nfl/rankings/half-point-ppr-{pos}-cheatsheets.php'
        else:
            raise ValueError('invalid position: {}'.format(pos))

        return self.get(url)

    def projections(self, pos, fmt, week):
        '''
        Gets rest-of-season rankings page

        Args:
            pos: 'qb', 'rb', 'wr', 'te', 'flex', 'qb-flex', 'k', 'dst'
            fmt: 'std', 'ppr', 'hppr'
            week: 'draft' or 1-17

        Returns:
            content: HTML string of page
        '''
        formats = ['std', 'ppr', 'hppr']
        if fmt not in formats:
            raise ValueError('invalid format: {}'.format(fmt))

        std_positions = ['qb', 'k', 'dst']
        ppr_positions = ['rb', 'wr', 'te', 'flex', 'qb-flex']

        if pos in std_positions:
            url = 'https://www.fantasypros.com/nfl/projections/{pos}.php'
        elif pos in ppr_positions:
            if fmt == 'std':
                url = 'https://www.fantasypros.com/nfl/projections/{pos}.php'
            elif fmt == 'ppr':
                url = 'https://www.fantasypros.com/nfl/projections/ppr-{pos}.php'
            elif fmt == 'hppr':
                url = 'https://www.fantasypros.com/nfl/projections/half-point-ppr-{pos}.php'
        else:
            raise ValueError('invalid position: {}'.format(pos))

        params = {'week': week}
        return self.get(url, payload=params)

    def ros_rankings(self, pos, fmt):
        '''
        Gets rest-of-season rankings page

        Args:
            pos: 'qb', 'rb', 'wr', 'te', 'flex', 'qb-flex', 'k', 'dst'
            fmt: 'std', 'ppr', 'hppr'

        Returns:
            content: HTML string of page
        '''

        formats = ['std', 'ppr', 'hppr']
        if fmt not in formats:
            raise ValueError('invalid format: {}'.format(fmt))

        std_positions = ['qb', 'k', 'dst']
        ppr_positions = ['rb', 'wr', 'te', 'flex', 'qb-flex']

        if pos in std_positions:
            url = 'https://www.fantasypros.com/nfl/rankings/ros-{pos}.php'
        elif pos in ppr_positions:
            if fmt == 'std':
                url = 'https://www.fantasypros.com/nfl/rankings/ros-{pos}.php'
            elif fmt == 'ppr':
                url = 'https://www.fantasypros.com/nfl/rankings/ros-ppr-{pos}-cheatsheets.php'
            elif fmt == 'hppr':
                url = 'https://www.fantasypros.com/nfl/rankings/ros-half-point-ppr-{pos}-cheatsheets.php'
        else:
            raise ValueError('invalid position: {}'.format(pos))

        return self.get(url)

    def weekly_rankings(self, pos, fmt, week=None):
        '''
        Gets weekly rankings page
        
        Args:
            pos: 'qb', 'rb', 'wr', 'te', 'flex', 'qb-flex', 'k', 'dst'
            fmt: 'std', 'ppr', 'hppr'
            week: default None, int between 1-17

        Returns:
            content: HTML string of page
        '''
        std_positions = ['qb', 'k', 'dst']
        ppr_positions = ['rb', 'wr', 'te', 'flex', 'qb-flex']
        formats = ['std', 'ppr', 'hppr']
        if fmt not in formats:
            raise ValueError('invalid format: {}'.format(fmt))

        if pos in std_positions:
            url = 'https://www.fantasypros.com/nfl/rankings/{pos}.php'
        elif pos in ppr_positions:
            if fmt == 'std':
                url = 'https://www.fantasypros.com/nfl/rankings/{pos}.php'
            elif fmt == 'ppr':
                url = 'https://www.fantasypros.com/nfl/rankings/ppr-{pos}.php'
            elif fmt == 'hppr':
                url = 'https://www.fantasypros.com/nfl/rankings/half-point-ppr-{pos}.php'
        else:
            raise ValueError('invalid position: {}'.format(pos))

        if week:
            url = url + '?week={}'.format(week)

        return self.get(url)


if __name__ == "__main__":
    pass
