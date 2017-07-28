'''
playerxref.py
Common cross-reference functions
'''

from collections import defaultdict


def nflcom_players(db):
    '''
    Creates dictionary of players from player (NFL.com) table    

    Args:
        db: NFLPostgres object (or subclass)

    Returns:
        dict
    '''
    cp = defaultdict(list)
    q = """SELECT player_id, full_name, position FROM player
           WHERE full_name IS NOT NULL"""
    for p in db.select_dict(q):

        # use position in table, otherwise list as 'UNK'
        pos = p.get('position')
        if not pos:
            pos = 'UNK'
        pid = p.get('full_name') + '_' + pos
        cp[pid].append(p)

    return cp

def nflcom_profiles(db):
    '''
    Dictionary of nflcom_profile and nflcom_player. For use with myfantasyleague.
    
    Args:
        db: 

    Returns:
        dict
    '''
    q = """SELECT player_id, full_name, profile_url 
           FROM player 
           WHERE full_name IS NOT NULL AND profile_url IS NOT NULL"""

    nflplayers = {}
    for p in db.select_dict(q):
        parts = p.get('profile_url').split('/')
        key = (parts[4] + '/' + parts[5])
        nflplayers[key] = p
    return nflplayers