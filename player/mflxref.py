'''
mflxref.py
Cross-reference functions for mfl players
'''

import logging

from nfl.scrapers.mfl import MFLScraper
from nfl.parsers.mfl import MFLParser
from nfl.player.playerxref import nflcom_profiles

def mfl_players(season_year):
    '''
    Returns list of players from myfantasyleague.com

    Returns:
        list of dict
    '''
    s = MFLScraper()
    p = MFLParser()
    content = s.players(season_year)
    return p.players(content)

def mfl_espn_xref(season_year, db, espn_players):
    '''
    Returns list of players, xref between espn and nflcom, using mfl data

    Args:
        season_year: 2016, etc.
        db: NFLPostgres instance
        espn_players: list of dict

    Returns:
        list of dict
    '''
    mflplayers = mfl_nfl_xref(season_year, db)
    for idx, p in enumerate(espn_players):
        pid = p.get('source_player_id')
        matches = [pl for pl in mflplayers if pl.get('espn_id') == pid]
        if matches:
            espn_players[idx]['nflcom_player_id'] = matches[0].get('nflcom_player_id')
    return espn_players

def mfl_nfl_xref(season_year, db):
    '''
    Returns list of players from myfantasyleague.com that have an nfl.com id

    Args:
        season_year: 2016, etc.
        db: NFLPostgres instance

    Returns:
        list of dict
    '''
    # step one: get the mfl player list
    mflp = mfl_players(season_year)

    # step two: get the nflcom_profiles dict
    nflp = nflcom_profiles(db)

    # step three: try to match
    for idx, p in enumerate(mflp):
        pid = p.get('nfl_id')
        if pid:
            match = nflp.get(pid)
            if match:
                mflp[idx]['nflcom_player_id'] = match['player_id']

    return [p for p in mflp if p.get('nflcom_player_id')]
