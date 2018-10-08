'''
player/yahooxref.py
Cross-reference functions for yahoo players
'''

import logging

from nflfantasy.scrapers.yahoo import YahooFantasyScraper
from nflfantasy.parsers.yahoo import YahooNBAParser


logging.getLogger(__name__).addHandler(logging.NullHandler())


def yahoo_playerids_db(db):
    '''
    Gets all yahoo player ids in the base.player table

    Args:
        db(NFLPostgres): instance

    Returns:
        list: of int

    '''
    q = """SELECT source_player_id as yahoo_player_id
           FROM base.player_xref
           WHERE source = 'yahoo';"""
    return db.select_list(q)


def yahoo_playerkeys_db(db):
    '''
    Gets all yahoo player keys in the base.player table

    Args:
        db(NFLPostgres): instance

    Returns:
        list: of str

    '''
    q = """SELECT source_player_code as yahoo_player_key
           FROM base.player_xref
           WHERE source = 'yahoo';"""
    return db.select_list(q)


def yahoo_playerids_web(authfn):
    '''
    Gets all yahoo player ids from the web

    Args:
        authfn(str): yahoo credentials file

    Returns:
        list: of int

    TODO: implement this
    '''
    pass


def yahoo_playerkeys_web(authfn):
    '''
    Gets all yahoo player keys from the web

    Args:
        authfn(str): yahoo credentials file

    Returns:
        list: of str

    TODO: implement this
    '''
    pass


def yahoo_players_db(db):
    '''
    Returns list of players in xref table with yahoo ids

    Args:
        db(NFLPostgres): instance

    Returns:
        list: of dict

    '''
    q = """SELECT * FROM base.player_xref WHERE source='yahoo';"""
    return db.select_dict(q)


def yahoo_players_web(authfn):
    '''
    Returns list of players from yahoo.com

    Args:
        authfn(str): yahoo credentials file

    Returns:
        list: of dict

    TODO: implement this
    '''
    pass


def yahoo_playersd_db(db):
    '''
    Returns dict of players in xref table with yahoo player ids

    Args:
        db(NFLPostgres): instance

    Returns:
        dict

    '''
    q = """SELECT * FROM base.player_xref WHERE source = 'yahoo';"""
    return {(p['source_player_code']): p for p in db.select_dict(q)}


def yahoo_playersd_web(authfn):
    '''
    Returns dict of players from web with mfl player ids

    Args:
        authfn(str): yahoo credentials file

    Returns:
        dict

    '''
    return {p['id']: p for p in yahoo_players_web(authfn)}


def yahoo_mfl_xref(db, first='mfl'):
    '''
    Dict of yahoo to mfl playerids

    Args:
        db(NFLPostgres):
        first(str): 'mfl' or 'yahoo'

    Returns:
        dict

    '''
    vals = db.select_dict("SELECT * FROM dfs.yahoo_mfl_xref")
    if first == 'yahoo':
        return {p['yahoo_player_id']: p['mfl_player_id'] for p in vals}
    else:
        return {p['mfl_player_id']: p['yahoo_player_id'] for p in vals}


if __name__ == '__main__':
    pass
