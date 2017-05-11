# update_player_positions.py
# gets profile from nfl.com and scrapes position

from collections import defaultdict
import logging
import os
import sys
import time

from configparser import ConfigParser
from fuzzywuzzy import fuzz, process
from nameparser import HumanName


from nfl.db.nflpg import NFLPostgres
from nfl.scrapers.scraper import FootballScraper
from nfl.player.position import *


def run():
    config = ConfigParser()
    configfn = os.path.join(os.path.expanduser('~'), '.pgcred')
    config.read(configfn)
    db = NFLPostgres(user=config['nfldb']['username'],
                  password=config['nfldb']['password'],
                  database=config['nfldb']['database'])

    # GET LIST OF PLAYERS WITH MISSING POSITIONS
    q = """
        select * from player where player_id IN
        (select distinct player_id from  weekly_stats where fpts_dk >=0 and passing_att < 5 and position = 'UNK')
    """
    # LOOP THROUGH PLAYER LIST
    s = FootballScraper(cache_name='pos')
    for player in db.select_dict(q):
        match = False
        if player.get('profile_url'):
            pos = position(profile_url=player['profile_url'], s=s)
            if pos and pos != 'UNK':
                uq = """UPDATE player SET {qq}position{qq}='{pos}' WHERE player_id='{pid}' AND full_name='{fn}' AND {qq}position{qq}='UNK';"""
                print(uq.format(qq='"', pid=player['player_id'], fn=player['full_name'], pos=pos))
                match = True
                time.sleep(.5)

        if not match:
            print(player)
        '''
            fbr_url = 'http://www.pro-football-reference.com/players/{}/'
            name = HumanName(player.get('full_name'))
            logging.info(name)
            # get football reference page for first letter of last name
            # <p><a href="/players/M/MoorBr24.htm">Brian Moorman</a>(P) 2001-2013</p>

            content = s.get(fbr_url.format(name.last[0]))
            soup = BeautifulSoup(content, 'lxml')

            # create counter of names - protect against duplicates
            names = defaultdict(int)
            for p in soup.find_all('p'):
                a = p.find('a')
                if a and '/players/' in a.get('href', None):
                    names[a.text] += 1

            # now try to find matching name
            players = defaultdict(list)
            for p in soup.find_all('p'):
                try:
                    a = p.find('a')
                    if '/players/' in a.get('href'):
                        if player.get('full_name') == a.text:
                            if names.get(a.text) == 1:
                                print a.parent.text
                            elif names.get(a.text) > 1:
                                players[player.get('full_name')].append(a.parent.text)
                        else:
                            mguess, prob = process.extractOne(player.get('full_name'), [a.text])
                            if prob > .90:
                                if names.get(mguess) == 1:
                                    print player.get('full_name'), a.parent.text, prob
                                else:
                                    players[player.get('full_name')].append(a.parent.text)
                except:
                    pass

        print players
        '''

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    run()
