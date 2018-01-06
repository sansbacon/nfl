'''
fprosxref.py
cross-reference fantasypros ids with nfl.player table ids
'''

import logging

from nfl.names import match_player
from nfl.player.playerxref import nflcom_players
from nfl.parsers.fantasypros import FantasyProsNFLParser
from nfl.scrapers.fantasypros import FantasyProsNFLScraper
from nfl.utility import getdb

def fpros_player_dict(fmt='ppr'):
    '''
    All ranked players for current week @ fantasypros

    Arguments:
        None

    Returns:
        dict
    '''
    fpros_players = []
    scraper = FantasyProsNFLScraper(cache_name='fpros-weekly')
    parser = FantasyProsNFLParser()
    for pos in ['qb', 'rb', 'wr', 'te', 'dst']:
        logging.info('starting {}'.format(pos))
        content = scraper.weekly_rankings(pos=pos, fmt=fmt)
        fpros_players += parser.weekly_rankings(content)
        logging.info('finished {}'.format(pos))
    return {'{}_{}'.format(p['source_player_name'], p['pos']): p
            for p in fpros_players}

def fpros_players(db):
    '''
    fantasypros players: nflcomid

    Arguments:
        db: NFLPostgres instance

    Returns:
        dict
    '''
    q = """
        select source_player_id, nflcom_player_id from extra_misc.player_xref
        where source = 'fantasypros'
    """
    return {p['source_player_id']: p['nflcom_player_id'] for p in db.select_dict(q)}


def fpros_xref(nflp, fpros_players):
    '''
    Cross reference fantasypros players with nfl.com players
    '''
    xref = {}
    multimatch = []
    nomatch = []

    # loop through fpros_players
    # also need to update as go through
    for k, v in fpros_players.items():
        if nflp.get(k):
            if len(nflp.get(k)) > 1:
                multimatch.append(v)
            else:
                fpros_id = v.get('source_player_id')
                xref[fpros_id] = nflp.get(k)[0].get('player_id')

        else:
            match = match_player(k, list(nflp.keys()), .85)
            if match:
                fpros_id = v.get('source_player_id')
                xref[fpros_id] = nflp.get(match)[0].get('player_id')
            else:
                nomatch.append(v)

    logging.info('match {}, multimatch {}, nomatch {}'.format(
        len(list(xref)), len(multimatch), len(nomatch)))

    return (xref, multimatch, nomatch)


if __name__ == '__main__':
    db = getdb
    logging.basicConfig(level=logging.INFO)
    nflp = nflcom_players(db)
    fpros_dict = fpros_player_dict()
    fpros_players = list(fpros_dict.values())
    fpros_idx = {item['source_player_id']: idx for idx, item in enumerate(fpros_players)}

    # add nflcom_player_id to fpros_players
    # then insert into extra_misc.player_xref
    wanted = ['nflcom_player_id', 'pos', 'source', 'source_player_id',
              'source_player_name', 'source_player_position']

    xref, multimatch, nomatch = fpros_xref(nflp, fpros_dict)
    for fpros_id, nflcom_id in xref.items():
        idx = fpros_idx.get(fpros_id)
        if idx:
            player = {k: v for k, v in fpros_players[idx].items() if k in wanted}
            player['nflcom_player_id'] = nflcom_id
            if player.get('pos'):
                player['source_player_position'] = player.get('pos')
                player.pop('pos', 0)
            db._insert_dict(player, 'extra_misc.player_xref')

