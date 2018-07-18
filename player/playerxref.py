'''
playerxref.py
Common cross-reference functions
'''

from collections import defaultdict
import logging

from fuzzywuzzy import process

logging.getLogger(__name__).addHandler(logging.NullHandler())


def player_dict(db):
    '''
    Creates dict of key: id from player table

    Args:
        db: NFLPostgres object (or subclass)

    Returns:
        dict

    '''
    q = """SELECT player_id AS pid, CONCAT_WS('_', full_name, pos) AS k 
           FROM base.player
           WHERE full_name != '' AND full_name IS NOT NULL
                 AND pos !='' AND pos IS NOT NULL"""
    cp = defaultdict(list)
    for p in db.select_dict(q):
        cp[p['k']].append(p)
    return cp


def player_draft(db):
    '''
    Creates dict of draft_player_id: player_id from player table

    Args:
        db: NFLPostgres object (or subclass)

    Returns:
        dict

    '''
    q = """SELECT player_id, source_player_id::int
           FROM base.player_xref
           WHERE source = 'draft'"""
    return {p['source_player_id']: p['player_id'] for p in db.select_dict(q)}



def player_list(db):
    '''
    Creates list from player table

    Args:
        db: NFLPostgres object (or subclass)

    Returns:
        list: of dict

    '''
    q = """SELECT * 
           FROM base.player
           WHERE full_name IS NOT NULL AND pos IS NOT NULL"""
    return db.select_dict(q)


def player_match_fuzzy(to_match, match_from):
    '''
    Matches player with fuzzy match

    Args:
        to_match (str): player name to match
        match_from (list): list of player names to match against

    Returns:
        match(str): matched name from match_from list
        confidence(int): confidence of match

    Example:
        name, conf = match_player(player, players)

    '''
    return process.extractOne(to_match, match_from)


def player_match_interactive(to_match, match_from, choices=5):
    '''
    Matches player with fuzzy match, interactive confirmation

    Args:
        to_match (str): player name to match
        match_from (list): list of player names to match against

    Returns:
        match(str): matched name from match_from list
        confidence(int): confidence of match

    '''
    for match in process.extract(to_match, match_from, limit=choices):
        resp = input('Matched {} to {} with conf {}: '.format(to_match, match[0], match[1]))
        if resp:
            return match[0]

    return None


def player_pfr(db):
    '''
    Creates dict of pfr_player_id: player_id from player table

    Args:
        db: NFLPostgres object (or subclass)

    Returns:
        dict

    '''
    q = """SELECT pfr_player_id as p1, player_id as p2
           FROM base.player
           WHERE pfr_player_id IS NOT NULL"""
    return {p['p1']: p['p2'] for p in db.select_dict(q)}


def player_pfr_pos(db):
    '''
    Creates dict of pfr_player_id: pos from player table

    Args:
        db: NFLPostgres object (or subclass)

    Returns:
        dict

    '''
    q = """SELECT pfr_player_id as id, pos
           FROM base.player
           WHERE pfr_player_id IS NOT NULL AND pos IS NOT NULL"""
    return {p['id']: p['pos'] for p in db.select_dict(q)}


if __name__ == '__main__':
    pass
