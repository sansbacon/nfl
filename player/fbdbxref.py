'''
fbdbxref.py
cross-reference footballdatabase ids with nfl.player table ids
'''

import logging

from fuzzywuzzy import process

from nfl.names import match_player
from nfl.player.playerxref import nflcom_players
from nfl.utility import getdb


def fbdb_xref_players(db):
    '''
    Gets dict of fbdd_id:nflcom_player_id

    Arguments:
        db: NFLPostgres instance

    Returns:
        dict
        
    '''
    q = """
        select source_player_id, nflcom_player_id from extra_misc.player_xref
        where source = 'footballdatabase'
    """
    return {p['source_player_id']: p['nflcom_player_id'] for p in db.select_dict(q)}


def fbdb_xref(db, fbdb_players):
    '''
    Cross reference fantasypros players with nfl.com players

    Args:
        db(NFLPostgres): database class
        fbdb_players(list): list of fbdb players
        
    Returns:
        list
        
    '''
    # xref will hold new values
    # key is fbdb_id, value is dict, includes nflcom_player_id
    xref = {}
    multimatch = []
    nomatch = []

    # step one: get existing data
    nflp = nflcom_players(db)
    fbdbp = fbdb_xref_players(db)

    # loop through fbdb players that
    # are not already in extra_misc.player_xref
    for p in fbdb_players:
        # skip if already have xref for this player
        if fbdbp.get(p['source_player_id']) or xref.get(p['source_player_id']):
            continue

        # first try direct match
        k = '{}_{}'.format(p['source_player_name'], p['source_player_position'])
        if nflp.get(k):
            if len(nflp.get(k)) > 1:
                multimatch.append(p)
            else:
                p['nflcom_player_id'] = nflp.get(k)[0].get('player_id')
                xref[p['source_player_id']] = p

        # if direct match does not work
        # can try to do fuzzy match
        else:
            match, confidence = process.extractOne(k, list(nflp.keys()))
            print('{} | {} | {}'.format(k, match, confidence))
            is_match = input("Is this a match? ")
            if is_match == 'y':
                nflplyr = nflp[match]
                if len(nflplyr) == 1:
                    p['nflcom_player_id'] = nflplyr[0]['player_id']
                    xref[p['source_player_id']] = p
                elif len(nflplyr > 1):
                    multimatch.append(p)
            else:
                # need to log in no match
                nomatch.append(p)

    return (xref, multimatch, nomatch)


def run():
    db = getdb
    logging.basicConfig(level=logging.INFO)




if __name__ == '__main__':
    run()