'''
fboxref.py
cross-reference football outsiders identifiers with nfl.player table ids
'''

import logging

from nfl.names import match_player
from nfl.player.playerxref import nflcom_players


def fbo_gsis_players(db):
    '''
    footballoutsiders players: nflcomid ('82-J.Witten': '00-0022127')

    Arguments:
        db: NFLPostgres instance

    Returns:
        dict
        
    '''
    q = """
        select source_player_id, nflcom_player_id from extra_misc.player_xref
        where source = 'fbo_gsis'
    """
    return {p['source_player_id']: p['nflcom_player_id'] for p in db.select_dict(q)}


def fbo_gsis_xref(nfl_players, source_players):
    '''
    Cross reference fbo_gsis players with nfl.com players

    Args:
        nfl_players (dict): '82-J.Witten': '00-0022127'
        source_players(list): of dict
        
    '''
    xref = {}
    multimatch = []
    nomatch = []

    # loop through players
    for k, v in source_players.items():
        # try direct match first
        # if more than one result, address manually
        if nfl_players.get(k):
            if len(nfl_players.get(k)) > 1:
                multimatch.append(v)
            else:
                source_id = v.get('source_player_id')
                xref[source_id] = nfl_players.get(k)[0].get('player_id')

        # if direct match fails, use fuzzy match in match_player
        else:
            match = match_player(k, list(nfl_players.keys()), .85)
            if match:
                source_id = v.get('source_player_id')
                xref[source_id] = nfl_players.get(match)[0].get('player_id')
            else:
                nomatch.append(v)

    logging.info('match {}, multimatch {}, nomatch {}'.format(
        len(list(xref)), len(multimatch), len(nomatch)))

    """
    cpkeys = list(cp.keys())
    for gsis_id in set(unmatched):
        gsis_name = gsis_id.split('-')[-1]
        match = match_player(gsis_id, cpkeys, threshold=90)
        if match:
            try:
                jersey1, gsis1 = gsis_id.split('-')
                jersey2, gsis2 = match.split('-')
                if jersey1 == jersey2:
                    if gsis1[0] == gsis2[0]:
                        print(gsis_id, match)
            except:
                pass
    """
    return (xref, multimatch, nomatch)


if __name__ == '__main__':
    pass