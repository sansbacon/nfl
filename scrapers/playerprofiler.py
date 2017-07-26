# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

from nfl.scrapers.scraper import FootballScraper


class PlayerProfilerNFLScraper(FootballScraper):
    '''
    For use by subscribers
    Non-subscribers should be aware of site's TOS
    '''

    def player_articles(self, site_player_id):
        '''
        Gets single player article page from playerprofiler
        '''
        url = 'https://www.playerprofiler.com/wp-admin/admin-ajax.php?action=playerprofiler_articles&player_id={}'
        return self.get_json(url.format(site_player_id))

    def player_news(self, site_player_id):
        '''
        Gets single player news page from playerprofiler
        '''
        url = 'https://www.playerprofiler.com/wp-admin/admin-ajax.php?action=integrated_news&player_id={}'
        return self.get_json(url.format(site_player_id))

    def player_page(self, site_player_id):
        '''
        Gets single player page from playerprofiler
        '''
        url = 'https://www.playerprofiler.com/wp-admin/admin-ajax.php?action=playerprofiler_api&endpoint=%2Fplayer%2F{}'
        return self.get_json(url.format(site_player_id))

    def players(self):
        '''
        Gets list of players, with ids, from playerprofiler
        '''
        url = 'https://www.playerprofiler.com/wp-admin/admin-ajax.php?action=playerprofiler_api&endpoint=%2Fplayers'
        return self.get_json(url)

    def rankings(self):
        '''
        Gets current season, dynasty, and weekly rankings from playerprofiler
        '''
        url = 'https://www.playerprofiler.com/wp-admin/admin-ajax.php?action=playerprofiler_api&endpoint=%2Fplayer-rankings'
        return self.get_json(url)

if __name__ == "__main__":
    pass