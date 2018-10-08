# scripts/mfl-player-update.py
# ensures all players from myfantasyleague.com are in player table
#    and that existing players have mfl_player_id 

import json
import logging

from collections import defaultdict
from nfl.utility import *
from nfl.player.mflxref import *
from nfl.player.playerxref import player_match_fuzzy, player_match_interactive


def run():
    # step 1: get existing players from database
    # use dictionary for fuzzy matching
    # defaultdict allows multiple players with same key
    q = """SELECT * FROM base.player"""
    q2 = """SELECT * FROM base.player WHERE mfl_player_id IS NOT NULL"""

    # have dict for mfl_player_id and dict for player key
    playersd_in_db = {p['mfl_player_id']: p for p in db.select_dict(q2)}
    playersk_in_db = defaultdict(list)
    for p in db.select_dict(q):
        k = '{}_{}'.format(p['full_name'].upper(), p['pos'].upper())
        playersk_in_db[k].append(p)
     
    # step 2: get MFL players
    mfl_players = mfl_players_web(2018)

    # step 3: look for MFL players in database
    to_update = []
    to_check_out = []
    nomatch = []

    for p in mfl_players:
        # look for id match
        ln, fn = p['name'].split(', ')[0:2]
        m = playersd_in_db.get(int(p['id'])) 
        if m:
            continue
        k = '{} {}_{}'.format(fn.upper(), ln.upper(), p['position'].upper())
        matches = playersk_in_db.get(k, [])
            
        # if there is only 1 match, test to make sure name and position matches
        if len(matches) == 1:
            # need to update mfl_player_id in database
            to_update.append((p, matches[0]))
            continue

        # if more than 1 match, will need to manually resolve
        elif len(matches) > 1:
            to_check_out.append((p, matches))
            continue

        # if no match, then try fuzzy match
        nomatch.append(p)

    # step four: update players
    uq = """UPDATE base.player SET mfl_player_id = {} WHERE player_id = {};"""
    for p in to_update:
        mflp, dbp = p
        db.execute(uq.format(mflp['id'], dbp['player_id']))

    # step five: check out players
    if len(to_check_out) > 0:
        print(to_check_out)

    # step six: try fuzzy match
    updates = []
    inserts = []
    dbkeys = [k for k in playersk_in_db.keys() if len(playersk_in_db[k]) == 1]
    uq = """UPDATE base.player SET mfl_player_id = {} WHERE player_id = {};"""

    for p in nomatch:
        ln, fn = p['name'].split(', ')[0:2]
        k = '{} {}_{}'.format(fn.upper(), ln.upper(), p['position'].upper())
        match, conf = player_match_fuzzy(k, dbkeys)
        if conf >= 95:
            val = playersk_in_db[match]                                     
            if len(val) == 1:                                               
                updates.append(uq.format(p['id'], val[0]['player_id']))
                continue
            else:                                                                 
                print('manually match: {}'.format(val))
        else:
            match = player_match_interactive(k, dbkeys)
            if match:
                val = playersk_in_db[match]
                if len(val) == 1:
                    updates.append(uq.format(p['id'], val[0]['player_id']))
                    continue
                else:
                    print('manually match: {}'.format(val))
            else:
                d = {'first_name': fn, 'last_name': ln, 'mfl_player_id': int(p['id']),
                     'pos': p['position'], 'college': p.get('college'),
                     'height': p.get('height'), 'weight': p.get('weight')}
                try:
                    d['birthdate'] = datetime.datetime.fromtimestamp(int(p['birthdate']))
                except:
                    pass
                inserts.append(db._insert_statement(d, 'base.player'))
                logging.info('added {} {}'.format(d['first_name'], d['last_name']))

if __name__ == '__main__':
    run()
