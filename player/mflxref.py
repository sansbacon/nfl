'''
player/mflxref.py
Cross-reference functions for mfl players
'''

import logging

from nflfantasy.scrapers.mfl import MFLScraper
from nflfantasy.parsers.mfl import MFLParser

logging.getLogger(__name__).addHandler(logging.NullHandler())


def mfl_playerids_db(db):
    '''
    Gets all mfl player ids in the base.player table

    Args:
        db(NFLPostgres): instance

    Returns:
        list: of int

    '''
    q = """SELECT mfl_player_id FROM base.player
                WHERE mfl_player_id IS NOT NULL;"""

    return db.select_list(q)


def mfl_playerids_web(season_year, exclude=None):
    '''
    Gets all mfl player ids in the

    Args:
        db(NFLPostgres): instance

    Returns:
        list: of int

    '''
    mflp = mfl_players_web(season_year, exclude)
    return [int(p['id']) for p in mflp]


def mfl_players_db(db, exclude=None):
    '''
    Returns list of players in table with mfl player ids

    Args:
        db(NFLPostgres): instance
        excl(boolean): exclude players


    Returns:
        list of dict

    '''
    if not exclude:
        exclude = ['CB', 'Coach', 'DE', 'DT', 'LB', 'Off', 'PK',
                   'PN', 'S', 'ST', 'TMDB', 'TMDL', 'TMLB', 'TMPK',
                   'TMPN', 'TMQB', 'TMRB', 'TMTE', 'TMWR', 'WR']
    q = """SELECT * FROM base.player
                WHERE mfl_player_id IS NOT NULL;"""
    players = db.select_dict(q)
    if exclude:
        return [p for p in players if p['pos'] not in exclude]
    else:
        return players


def mfl_players_web(season_year, exclude=None):
    '''
    Returns list of players from myfantasyleague.com

    Args:
        season_year(int): NFL season
        excl(boolean): exclude players


    Returns:
        list of dict

    '''
    players = []
    if not exclude:
        exclude = ['CB', 'Coach', 'DE', 'DT', 'LB', 'Off', 'PK',
                   'PN', 'S', 'ST', 'TMDB', 'TMDL', 'TMLB', 'TMPK',
                   'TMPN', 'TMQB', 'TMRB', 'TMTE', 'TMWR']

    mfls = MFLScraper(cache_name='mfl')
    mflp = MFLParser()
    content = mfls.players(season_year)
    for p in mflp.players(content):
        if p['position'] in exclude:
            continue
        p['id'] = int(p['id'])
        players.append(p)
    return players


def mfl_playersd_db(db, exclude=None):
    '''
    Returns dict of players in table with mfl player ids

    Args:
        db(NFLPostgres): instance
        excl(boolean): exclude positions

    Returns:
        dict

    '''
    d = {}
    if not exclude:
        exclude = ['CB', 'Coach', 'DE', 'DT', 'LB', 'Off', 'PK',
                   'PN', 'S', 'ST', 'TMDB', 'TMDL', 'TMLB', 'TMPK',
                   'TMPN', 'TMQB', 'TMRB', 'TMTE', 'TMWR', 'WR']
    q = """SELECT * FROM base.player
                WHERE mfl_player_id IS NOT NULL;"""
    return {int(p['mfl_player_id']): p for p in db.select_dict(q)
            if p['pos'] not in exclude}


def mfl_playersd_web(season_year, exclude=None):
    '''
    Returns dict of players from web with mfl player ids

    Args:
        season_year(int): NFL season
        excl(boolean): exclude positions

    Returns:
        dict

    '''
    if not exclude:
        exclude = ['CB', 'Coach', 'DE', 'DT', 'LB', 'Off', 'PK',
                   'PN', 'S', 'ST', 'TMDB', 'TMDL', 'TMLB', 'TMPK',
                   'TMPN', 'TMQB', 'TMRB', 'TMTE', 'TMWR', 'WR']
    return {p['id']: p for p in mfl_players_web(season_year)
            if p['position'] not in exclude}


def mfl_playernamesd_web(season_year, exclude=None):
    '''
    Returns dict of players from web with mfl player ids

    Args:
        season_year(int): NFL season
        excl(boolean): exclude positions

    Returns:
        dict

    '''
    if not exclude:
        exclude = ['CB', 'Coach', 'DE', 'DT', 'LB', 'Off', 'PK',
                   'PN', 'S', 'ST', 'TMDB', 'TMDL', 'TMLB', 'TMPK',
                   'TMPN', 'TMQB', 'TMRB', 'TMTE', 'TMWR', 'WR']
    d = {}
    for p in mfl_players_web(season_year):
        if p['position'] in exclude:
            continue
        ln, fn = p['name'].split(', ')[0:2]
        d[fn + ' ' + ln] = p


def mfl_dk_xref(db, first='mfl'):
    '''
    Dict of mfl to dk playerids

    Args:
        db(NFLPostgres):
        first(str): 'mfl' or 'dk'

    Returns:
        dict

    '''
    q = """SELECT mfl_player_id, dk_player_id FROM dfs.dk_mfl_xref;"""
    if first == 'mfl':
        return {v['mfl_player_id']: v['dk_player_id'] for v in db.select_dict(q)}
    else:
        return {v['dk_player_id']: v['mfl_player_id'] for v in db.select_dict(q)}


def mfl_fd_xref(db, first='mfl'):
    '''
    Dict of mfl to fd playerids

    Args:
        db(NFLPostgres):
        first(str): 'mfl' or 'fd'

    Returns:
        dict

    '''
    q = """SELECT mfl_player_id, fd_player_id FROM dfs.fd_mfl_xref;"""
    try:
        if first == 'mfl':
            return {v['mfl_player_id']: v['dk_player_id'] for v in db.select_dict(q)}
        else:
            return {v['dk_player_id']: v['mfl_player_id'] for v in db.select_dict(q)}
    except:
        return {}


def mfl_not_in_db(mflp_db_ids, mflp_web_ids):
    '''
    Finds MFL players that are not in the player table

    Args:
        mflp_db_ids(list): of int
        mflp_web_ids(list): of int

    Returns:
        set of int

    '''
    return set(mflp_db_ids) - set(mflp_web_ids)


def mfl_player_audit(mfl_pld_web, mfl_pld_db):
    '''
    Reconciles players from web and in database

    Args:
        mfl_pld_web(dict): dict of MFL id: player dict
        mfl_pld_db(dict): dict of MFL id: player dict

    Returns:
        list: of dict

    '''
    # go through each player in database
    # find matching id from web
    # if ID matches, then look at name and position
    # fixed are the IDs that I've already taken care of
    # should get more elegant solution later on - read from file
    mismatched = []
    fixed = [13145, 13368, 13549, 13958, 4397, 7422, 10409,
             10838, 11154,11643, 11927, 13369, 13452, 13589, 12822]
    for pid, p in mfl_pld_db.items():
        # skip defense - they are all in the DB
        if p['pos'] in ['Def', 'DST', 'D']:
            continue
        elif pid in fixed:
            continue
        match = mfl_pld_web.get(pid)
        if match:
            ln, fn = match['name'].split(', ')[0:2]
            if fn == p['first_name'] and ln == p['last_name'] and p['pos'].upper() == match['position'].upper():
                logging.debug('match for {} - {}'.format(pid, type(pid)))
                continue
            else:
                logging.error('review {} - {}'.format(pid, p['full_name']))
                mismatched.append(p)
        else:
            logging.debug('no match for {} - {}'.format(pid, type(pid)))
    return mismatched


def mfl_player_missing(mfl_pld_web, mfl_pld_db):
    '''
    Shows players from web that are not in database

    Args:
        mfl_pld_web(dict): dict of MFL id: player dict
        mfl_pld_db(dict): dict of MFL id: player dict

    Returns:
        list: of dict

    '''
    # go through each player in database
    # find matching id from web
    # if ID matches, then look at name and position
    # fixed are the IDs that I've already taken care of
    # should get more elegant solution later on - read from file
    missing = []
    for pid, p in mfl_pld_web.items():
        # skip defense - they are all in the DB
        if p['position'] in ['Def', 'DST', 'D']:
            continue
        if pid not in mfl_pld_db:
            missing.append(p)
            logging.info('no match for {} - {}'.format(pid, p['name']))
    return missing


if __name__ == '__main__':
    pass
