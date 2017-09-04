# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import json

from nfl.scrapers.scraper import FootballScraper


class DraftNFLScraper(FootballScraper):
    '''
    '''

    def json_file(self, fn):
        '''
        Opens draft JSON player_pool file
        Args:
            fn: 

        Returns:

        '''
        with open(fn, 'r') as infile:
            return json.load(infile)

    def player_pool(self, sha, token, auth, referer, contest_code):
        '''
        TODO: this doesn't really work right now
        Args:
            sha: 
            token: 
            auth: 
            referer: 

        Returns:

        '''
        url = 'https://api.playdraft.com/v4/player_pool/{}'
        headers = {
            'Host': 'api.playdraft.com',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Client-Type': 'web',
            'X-Client-Sha': sha,
            'X-User-Token': token,
            'X-User-Auth-Id': auth,
            'Referer': referer,
            'Origin': 'https://playdraft.com',
            'Connection': 'keep-alive',
        }
        self.get(url.format(contest_code), headers=headers)

if __name__ == "__main__":
    pass
