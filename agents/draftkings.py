from __future__ import print_function

import csv
import json
import logging
import os
import re
import StringIO
import time

import pandas as pd

import browsercookie
import requests
import requests_cache


class DraftKingsNFLAgent(object):

    def __init__(self, cache_name=None):
        logging.getLogger(__name__).addHandler(logging.NullHandler())

        self.s = requests.Session()
        self.s.cookies = browsercookie.firefox()
        self.s.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'})

        if cache_name:
            requests_cache.install_cache(cache_name)
        else:
            requests_cache.install_cache(os.path.join(os.path.expanduser("~"), '.rcache', 'dk-nfl-cache'))


    def _parse_contests(self, contests):
        '''
        Gets the useful data from contest dict

        Args:
            contests(list): of contest dict

        Returns:
            parsed(list): of contest dict
        '''

        wanted = ['ContestId', 'CreatorUserId', 'DraftGroupId', 'IsDirectChallenge', 'LineupId', 'MaxNumberPlayers', 'PlayerPoints', 'Sport',
                  'TimeRemaining', 'TimeRemainingOpp', 'TotalPointsOpp', 'UserContestId', 'UsernameOpp']

        return [{k:v for k,v in c.items() if k in wanted} for c in contests]

    def live_contests(self):
        '''
        Gets list of contests

        Returns:
            contests(list): of contest dict
        '''
        r = self.s.get('https://www.draftkings.com/mycontests')
        r.raise_for_status()
        pattern = re.compile(r'live\:\s+(\[.*?\]),\s+upcoming', re.DOTALL | re.MULTILINE | re.IGNORECASE)
        match = re.search(pattern, r.content)
        if match:
            js = match.group(1)
            contests = json.loads(js)
            return self._parse_contests(contests)
        else:
            return None

    def live_hth(self):
        '''
        Gets list of live head-to-head contests (defined as MaxNumberPlayers = 2)

        Returns:
            hth(list): of contest dict
        '''
        return [c for c in self.live_contests() if c.get('MaxNumberPlayers') == 2]

    def contest_lineup(self, contest_id, user_contest_id, draft_group_id):
        url = 'https://www.draftkings.com/contest/gamecenter/{}?uc={}'.format(contest_id, user_contest_id)
        r = self.s.get(url)
        r.raise_for_status()

        # contest page has var teams =
        # [{"uc":623324083,"u":725157,"un":"sansbacon","t":"(1/1)","r":1,"pmr":102,"pts":148.88},
        # {"uc":623263592,"u":1679292,"un":"Meth","t":"(1/1)","r":2,"pmr":102,"pts":132.96}]
        # need to get 'uc' to create idList parameter below
        match = re.search(r'var teams = (.*?);', r.content)
        if match:
            id_list = [t['uc'] for t in json.loads(match.group(1))]

            # have to send POST to get lineup data (page HTML is just a stub filled in with AJAX)
            payload = {"idList":id_list,"reqTs":int(time.time()),"contestId":contest_id,"draftGroupId":draft_group_id}
            r = self.s.post('https://www.draftkings.com/contest/getusercontestplayers', data=payload)
            r.raise_for_status()
            wanted = ['fn', 'ln', 'htabbr', 'htid', 'pcode', 'pid', 'pn', 'pts', 's']
            return [{k: v for k, v in p.items() if k in wanted} for p in json.loads(r.content)['data'][str(id_list[1])]]

        else:
            return None

    def salaries(self):
        url = 'https://www.draftkings.com/lobby#/NFL/0/All'
        r = self.s.get(url)
        match = re.search(r'var packagedContests = (.*?);', r.content)
        if match:
            contest = json.loads(match.group(1))[0]
            dgid = contest.get('dg')
            curl = 'https://www.draftkings.com/lineup/getavailableplayerscsv?contestTypeId=21&draftGroupId={}'
            r = self.s.get(curl.format(dgid))
            f = StringIO.StringIO(r.content)
            dfr = pd.read_csv(f)
            return dfr.T.to_dict().values()
        else:
            return None

if __name__ == '__main__':
    pass