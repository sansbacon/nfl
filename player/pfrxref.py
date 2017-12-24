'''
pfrxref.py
cross-reference pro-football-reference ids with nfl.player table ids
'''

from collections import defaultdict
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

def pfr_nfl_xref(db):
    '''
    Returns dict (pfr_id:nfl_ic) of players from pro-football-reference that have an nfl.com id

    Args:
        db: NFLPostgres instance

    Returns:
        dict
    '''
    # step one: get the mfl player list
    q = """SELECT * FROM extra_misc.player_xref WHERE source = 'pfr'"""
    return {p['source_player_id']:p['nflcom_player_id'] for p in db.select_dict(q)}

def update_xref(db, nflcom_players, pfr_players):
    '''
    Maps pfr playerid to nfl.player player_id

    Args:
        db: NFLPostgres object (or subclass)
        nflcom_players: dict of list
        pfr_players: list of dict

    Returns:
        dict of list of duplicates and unmatched
    '''
    leftovers = {'dups': [], 'unmatched': []}

    ## loop through the pfr players and try to find match
    for idx, p in enumerate(pfr_players):
        years = pfr_players[idx].pop('source_player_years', None)
        pid = p.get('source_player_name')
        match = nflcom_players.get(pid)
        if match:
            if len(match) == 1:
                pfr_players[idx]['nflcom_player_id'] = match[0].get('player_id')
            else:
                leftovers['dups'].append(match)
        else:
            leftovers['unmatched'].append(p)

    ## add matches to player_xref
    for p in [pl for pl in pfr_players if pl.get('nflcom_player_id')]:
        db._insert_dict(p, 'extra.player_xref')

    return leftovers

if __name__ == '__main__':
    pass