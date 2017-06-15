# rgxref.py

import logging
import os

from configparser import ConfigParser

from nfl.db.nflpg import NFLPostgres
from nfl.names import *


# setup
config = ConfigParser()
configfn = os.path.join(os.path.expanduser('~'), '.pgcred')
config.read(configfn)
db = NFLPostgres(user=config['nfldb']['username'],
              password=config['nfldb']['password'],
              database=config['nfldb']['database'])

# step one: get the rotoguru players & player_ids
q = """select distinct gid, player_name, player_pos from rotoguru_dk"""
rgp = db.select_dict(q)

# step two: get nfl players
q2 = '''select player_id, full_name, "position" from player
        where full_name IS NOT NULL and "position" IS NOT NULL'''
nflp = db.select_dict(q2)
nflnames = {i.get('full_name'):idx for idx, i in enumerate(nflp)}

# step three: try to match
for idx, p in enumerate([i.get('player_name', '') for i in rgp]):
    rgplayer = first_last(p)
    nm = match_player(rgplayer, list(nflnames.keys()))
    if nm:
        rgpos = rgp[idx].get('player_pos')
        nflpos = nflp[nflnames[nm]]['position']
        if rgpos == nflpos:
            rgp[idx]['nflcom_id'] = nflp[nflnames[nm]]['player_id']
        else:
            print(nm, rgpos, nflpos)

print(rgp)
