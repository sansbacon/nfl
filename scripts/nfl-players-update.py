# nfl-player-update.py
# updates nflcom_player_id field in player table

"""
Examples:
    python ~/workspace/nfl/scripts/nfl-players-update.py \

"""

import logging
import json
import sys
from time import sleep

import click

from nfl.parsers.nflcom import NFLComParser
from nfl.scrapers.nflcom import NFLComScraper

from nfl.utility import getdb
from nfl.player.mflxref import *


def get_nfl_id(scraper, parser, mfl_player=None, name=None):
    '''
    Gets nflcom_player_id from mfl_player info

    Args:
        scraper(NFLComScraper)
        parser(NFLComParser)
        mfl_player(dict): default None
        name(str): default None

    Returns:
        str

    '''
    pid = None
    if mfl_player:
        content = scraper.player_profile(profile_path=p['nfl_id'])
        try:
            nflplayer = nflp.player_page(content, p['nfl_id'].split('/')[1])
            pid = nflplayer.get('player_id')
            logging.info('finished {}'.format(p['name']))
        except Exception as e:
            logging.exception(e, p)
    elif name:
        content = scraper.player_search_name(name)
        matches = parser.player_search_name(content)
        if matches and len(matches) == 1:
            # get the profile page from nfl.com using name and profile_id
            # can extract nflcom_player_id from that page
            try:
                nfl_name, nfl_profile_id = matches[0][1:]
                content = scraper.player_profile(player_name=nfl_name,
                                                 profile_id=nfl_profile_id)
                nflplayer = nflp.player_page(content, nfl_profile_id)
                pid = nflplayer.get('player_id')
            except Exception as e:
                logging.exception(e, name)
        else:
            logging.error(matches)
    else:
        raise ValueError('pass either mfl_player or name')
    return pid


def update_players(db, updated):
    '''
    TODO - this is just pasted from ipython session

    Returns:

    '''
    uq = """UPDATE base.player SET nflcom_player_id = '{}' WHERE mfl_player_id = {};"""
    nflq = """SELECT * FROM base.player WHERE nflcom_player_id = '{}'"""
    mflq = """SELECT * FROM base.player WHERE mfl_player_id = {}"""

    for p in updated:
        try:
            db.execute(uq.format(p[1]['player_id'], p[0]['id']))
        except:
            # try:
            #    nflp = db.select_dict(nflq.format(p[1]['player_id']))
            #    mflp = db.select_dict(mflq.format(p[0]['id']))
            #    logging.info(nflp[0])
            #    logging.info(mflp[0])
            # except:
            pass

    uq = """UPDATE base.player SET nflcom_player_id = '{}' WHERE mfl_player_id = {};"""
    nflq = """SELECT * FROM base.player WHERE nflcom_player_id = '{}'"""
    mflq = """SELECT * FROM base.player WHERE mfl_player_id = {}"""

    for p in updated:
        try:
            db.execute(uq.format(p[1]['player_id'], p[0]['id']))
        except:
            nflp = db.select_dict(nflq.format(p[1]['player_id']))
            mflp = db.select_dict(mflq.format(p[0]['id']))
            logging.info(nflp[0])
            logging.info(mflp[0])

    uq = """UPDATE base.player SET nflcom_player_id = '{}' WHERE mfl_player_id = {};"""
    nflq = """SELECT * FROM base.player WHERE nflcom_player_id = '{}'"""
    mflq = """SELECT * FROM base.player WHERE mfl_player_id = {}"""

    for p in updated:
        try:
            db.conn.execute(uq.format(p[1]['player_id'], p[0]['id']))
        except:
            nflp = db.select_dict(nflq.format(p[1]['player_id']))
            mflp = db.select_dict(mflq.format(p[0]['id']))
            logging.info(nflp[0])
            logging.info(mflp[0])

    uq = """UPDATE base.player SET nflcom_player_id = '{}' WHERE mfl_player_id = {};"""
    nflq = """SELECT * FROM base.player WHERE nflcom_player_id = '{}'"""
    mflq = """SELECT * FROM base.player WHERE mfl_player_id = {}"""

    for p in updated:
        try:
            db.conn.execute(uq.format(p[1]['player_id'], p[0]['id']))
        except:
            nflp = db.select_dict(nflq.format(p[1]['player_id']))
            mflp = db.select_dict(mflq.format(p[0]['id']))
            if nflp[0]['player_id'] != mflp[0]['player_id']:
                logging.info(nflp[0])
                logging.info(mflp[0])

    uq = """UPDATE base.player SET nflcom_player_id = '{}' WHERE mfl_player_id = {};"""
    nflq = """SELECT * FROM base.player WHERE nflcom_player_id = '{}'"""
    mflq = """SELECT * FROM base.player WHERE mfl_player_id = {}"""

    for p in updated:
        try:
            db.conn.execute(uq.format(p[1]['player_id'], p[0]['id']))
        except:
            nflp = db.select_dict(nflq.format(p[1]['player_id']))
            mflp = db.select_dict(mflq.format(p[0]['id']))
            if nflp[0]['player_id'] != mflp[0]['player_id']:
                logging.info(nflp[0])
                logging.info(mflp[0])


def get_missing_nflcom_ids(db, require_mfl=False):
    '''
    Gets players that are missing nflcom_player_ids
    Args:
        db(NFLPostgres):
        require_mfl(True): require player to have mflcom_player_id

    Returns:
        list: of dict

    '''
    if require_mfl:
        nflq = """SELECT * FROM base.player
                  WHERE nflcom_player_id IS NULL
                    AND mfl_player_id IS NOT NULL"""
        return {p['mfl_player_id']: p for p in db.select_dict(nflq)}
    else:
        nflq = """SELECT * FROM base.player
                  WHERE nflcom_player_id IS NULL"""
        return {p['mfl_player_id']: p for p in db.select_dict(nflq)}


@click.command()
@click.option('-f', '--filename', default=None, type=str, help='Filename to save')
@click.option('-v', '--verbose', default=False, type=bool, help='Show log on stdout')
@click.option('-p', '--polite', default=True, type=bool, help='Sleep between scrapes')
def run(filename, verbose, polite):
    '''
    Gets nflcom_player_id for players with mfl_player_ids

    Args:
        filename(str): save JSON file, default None
        verbose(bool): set logging level to INFO(True) or ERROR(False)

    Returns:
        None

    '''
    if verbose:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    updated = []
    db = getdb('nfl')
    if polite:
        nfls = NFLComScraper(delay=2)
    else:
        nfls = NFLComScraper(delay=.25)
    nflp = NFLComParser()

    # find players with mfl id that don't have nfl id
    missing_nflcom_ids = get_missing_nflcom_ids(db, require_mfl=True)

    # loop through players
    for p in mfl_players_web(2018):
        m = missing_nflcom_ids.get(int(p['id']))
        if m:
            logging.info('starting {}'.format(p['name']))
            # see if we have an nfl_id from mfl
            # if not, try to get by searching name on nfl website
            if p.get('nfl_id'):
                nflcom_player_id = get_nfl_id(nfls, nflp, mfl_player=p)
            else:
                nflcom_player_id = get_nfl_id(nfls, nflp, name=p['name'])
            if nflcom_player_id:
                # do update
                pass

    # save to file
    if filename:
        with open(filename, 'w') as outfile:
            json.dump(updated, outfile)

    logging.info('finished!')


if __name__ == '__main__':
    run()