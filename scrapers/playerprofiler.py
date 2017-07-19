# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

from nfl.scrapers.scraper import FootballScraper


class PlayerProfilerNFLScraper(FootballScraper):
    '''
    For use by subscribers
    Non-subscribers should be aware of site's TOS
    '''

    def player_page(self, site_player_id):
        '''
        Gets single player page from playerprofiler
        '''
        url = 'https://www.playerprofiler.com/wp-admin/admin-ajax.php?'
        params = {'action': 'playerprofiler_api',
                 'endpoint': '%2Fplayer%2F{}'.format(site_player_id)}
        return self.get(url, payload=params)

    def players(self):
        '''
        Gets list of players, with ids, from playerprofiler
        '''
        url = 'https://www.playerprofiler.com/wp-admin/admin-ajax.php?'
        params = {'action': 'playerprofiler_api',
                 'endpoint': '%2Fplayers%2F'}
        return self.get(url, payload=params)

    def rankings(self):
        '''
        Gets current season, dynasty, and weekly rankings from playerprofiler
        '''
        url = 'https://www.playerprofiler.com/wp-admin/admin-ajax.php?'
        params = {'action': 'playerprofiler_api',
                 'endpoint': '%2Fplayer-rankings'}
        return self.get(url, payload=params)

if __name__ == "__main__":
    pass