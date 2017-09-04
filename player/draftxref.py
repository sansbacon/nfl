# draftxref.py

from fuzzywuzzy import process
from nfl.player.playerxref import nflcom_players

def draft_xref(players):
    '''
    Cross-reference DRAFT and nfl.com players
    Args:
        players: 

    Returns:

    '''
    leftovers = []
    nflp = nflcom_players(db)
    dpls = list(players.values())

    for idx, dpl in enumerate(dpls):
        k = dpl['source_player_name'] + '_' + dpl['source_player_position']
        match = nflp.get(k)
        if match and len(match) == 1:
            dpls[idx]['nflcom_player_id'] = nflp[k][0]['player_id']
        elif match and len(match) > 1:
            print('duplicate for {}'.format(k))
        else:
            fuzzy, confidence = process.extractOne(k, list(nflp.keys()))
            if confidence > .85:
                match = nflp.get(fuzzy)
                pieces = ['draft', str(dpl['source_player_id']), dpl['source_player_name'], dpl['source_player_position'],
                          match[0]['player_id'], match[0]['full_name']]
                print(', '.join(pieces))
                try:
                    resp = input()
                except:
                    resp = raw_input()
                if resp == 'x' or resp == 'n':
                    leftovers.append(', '.join(pieces))
                else:
                    dpls[idx]['nflcom_player_id'] = match[0]['player_id']
            else:
                print('could not match {}'.format(k))

    return leftovers

def xref_update_db(db, dpls):
    '''
    TODO: this should be moved to agent?
    Updates database with items that have nflcom_player_id
    '''
    for dpl in dpls:
        if dpl.get('nflcom_player_id'):
            wanted = ['source', 'source_player_id', 'source_player_name', 'source_player_position', 'nflcom_player_id']
            pl = {k:v for k,v in dpl.items if k in wanted}
            db._insert_dict(pl, 'extra_misc.player_xref')
