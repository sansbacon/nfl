# -*- coding: utf-8 -*-

'''
dkxref.py
cross-reference draftkings players with nfl.player table ids
'''

from __future__ import absolute_import, print_function, division

import logging

from fuzzywuzzy import process

from nfl.names import match_player
from nfl.player.playerxref import nflcom_players
from nfl.utility import memoize

logging.getLogger(__name__).addHandler(logging.NullHandler())

@memoize
def dk_players(db):
    '''
    
    Args:
        db: 

    Returns:

    '''
    q = """SELECT DISTINCT source_player_id, source_player_name, source_player_position 
           FROM extra_fantasy.dk_weekly_players"""
    return db.select_dict(q)

def dk_xref(db, dkpl=None):
    '''
    
    Returns:

    '''
    # nflp is dict of list
    nflp = nflcom_players(db)

    if not dkpl:
        dkpl = dk_players(db)

    for dkp in dkpl:
        name = dkp.get('source_player_name')
        pos = dkp.get('source_player_position')
        key = '{}_{}'.format(name, pos)

        # try to find direct match in first nflp
        match = nflp.get(key)
        if match:
            if len(match) == 1:
                pieces = ['dk', str(dkp['source_player_id']), dkp['source_player_name'], dkp['source_player_position'],
                          match[0]['player_id'], match[0]['full_name']]
                print(', '.join(pieces))

            # do something about multiple matches
            elif len(match) > 1:
                print(match)
        else:
            fuzzy, confidence = process.extractOne(key, list(nflp.keys()))
            if confidence > .85:
                match = nflp.get(fuzzy)
                pieces = ['dk', str(dkp['source_player_id']), dkp['source_player_name'], dkp['source_player_position'],
                          match[0]['player_id'], match[0]['full_name']]
                print(', '.join(pieces))

            else:
                #pieces = [str(dkp['source_player_id']), dkp['source_player_name'], dkp['source_player_position']]
                print('could not match {}'.format(key))


def dk_weekly_xref(db, dkpl):
    '''

    Returns:

    '''

    # nflp is dict of list
    nflp = nflcom_players(db)

    for idx, p in enumerate(dkpl):
        key = '{}_{}'.format(p.get('name'), p.get('position'))

        # try to find direct match in first nflp
        if key in nflp:
            if len(nflp.get(key)) == 1:
                dkpl[idx]['nflcom_player_id'] = nflp[key][0]['player_id']
                logging.info('direct match')
            else:
                if 'Jacksonville' in key:
                    dkpl[idx]['nflcom_player_id'] = nflp[key][0]['player_id']
                elif 'Michael Thomas' in key:
                    if 'NO' in p.get('team'):
                        dkpl[idx]['nflcom_player_id'] = '00-0032765'
                    else:
                        dkpl[idx]['nflcom_player_id'] = '00-0033114'
                else:
                    logging.error('need to manually handle {}'.format(key))

        else:
            fuzzy, confidence = process.extractOne(key, list(nflp.keys()))
            if confidence > .85:
                match = nflp.get(fuzzy, [])
                logging.info('fuzzy match: {} | {}'.format(key, match[0].get('full_name')))
                if (len(match) == 1):
                    dkpl[idx]['nflcom_player_id'] = match[0]['player_id']
                else:
                    logging.error('need to manually handle {}'.format(match))
            else:
                print('could not match {}'.format(key))

    return dkpl


if __name__ == '__main__':
    pass
