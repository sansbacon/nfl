'''
flabsxref.py
cross-reference fantasylabs players with player table ids
'''

import copy
import logging

from nfl.player.playerxref import *

logging.getLogger(__name__).addHandler(logging.NullHandler())


def flabs_player_dict(db):
    '''
    Creates dict of flabs_id: id from player table

    Args:
        db: NFLPostgres object (or subclass)

    Returns:
        dict

    '''
    q = """SELECT player_id AS pid, source_player_id as spid 
           FROM base.player_xref
           WHERE source='fantasylabs'"""

    return {int(p['spid']): p['pid'] for p in db.select_dict(q)}


def flabs_player_list(db):
    '''
    Creates list from player_xref table

    Args:
        db: NFLPostgres object (or subclass)

    Returns:
        list: of dict

    '''
    q = """SELECT * 
           FROM base.player_xref
           WHERE source='fantasylabs'"""
    return db.select_dict(q)


def update_flabs_xref(db, players):
    '''
    Updates player_xref table

    Args:
        db (NFLPostgres): instance
        players (list): of dict

    Returns:
        list: of dict

    '''
    fixed = []
    manual = []
    pdict = player_dict(db)
    fld = flabs_player_dict(db)

    for p in players:

        # try direct match
        match = fld.get(p['PlayerId'])
        if match:
            d = copy.deepcopy(p)
            d['player_id'] = match
            fixed.append(d)
            continue

        # now try key match
        pk = p['Player_Name'] + '_' + p['Position']
        match = pdict.get(pk)
        if match and len(match) == 1:
            # update base.player_xref
            # add player_id to dict
            logging.info('direct match')
            d = {'player_id': match[0]['pid'],
                 'source': 'fantasylabs',
                 'source_player_id': p['PlayerId'],
                 'source_player_name': p['Player_Name'],
                 'source_player_position': p['Position']}
            fixed.append(d)
            db._insert_dict(d, 'base.player_xref')
            fld = flabs_player_dict(db)
        elif match and len(match) > 1:
            manual.append(p)
        else:
            pkey = player_match_interactive(pk, pdict.keys(), choices=3)
            match = pdict.get(pkey)
            if match and len(match) == 1:
                logging.info('fuzzy match')
                pid = match[0]['pid']
                d = {'player_id': pid,
                     'source': 'fantasylabs',
                     'source_player_id': p['PlayerId'],
                     'source_player_name': p['Player_Name'],
                     'source_player_position': p['Position']}
                fixed.append(d)
                db._insert_dict(d, 'base.player_xref')
                fld = flabs_player_dict(db)
            elif match and len(match) > 1:
                manual.append(p)
        if not match:
            manual.append(p)
            logging.info('no match')

    return fixed, manual


if __name__ == '__main__':
    pass