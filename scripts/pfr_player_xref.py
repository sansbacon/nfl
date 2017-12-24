'''
pfr_player_xref
updates cross-reference between nflcom players and pfr players

arguments:
    --dryrun: don't try to update database (default True)
    --minseason: exclude players whose last season is before this date (default current season)
    
usage:
    python pfr_fantasy_weekly.py --dryrun=False --minseason=2016
'''

import json
import logging
import os
import pprint
import string

import click
from fuzzywuzzy import process

from nfl.parsers.pfr import PfrNFLParser
from nfl.player.playerxref import nflcom_players
from nfl.player.pfrxref import pfr_nfl_xref
from nfl.scrapers.pfr import PfrNFLScraper
from nfl.seasons import current_season_year
from nfl.utility import getdb, flatten_list


@click.command()
@click.option('--insertdb', default=True)
@click.option('--minseason', default=current_season_year())
@click.option('--savepfr', default=True)
@click.option('--savepfr_fn', default=os.path.join(os.path.expanduser('~'), 'pfr_players.json'))
def run(insertdb, minseason, savepfr, savepfr_fn):

    # check if already scraped pfr and have file
    # if not, then need to scrape pfr player pages from A-Z
    pfr_players = []
    try:
        with open(savepfr_fn, 'r') as infile:
            pfr_players = json.load(infile)
    except:
        parser = PfrNFLParser()
        scraper = PfrNFLScraper(cache_name='pfr-players', delay=1)
        for p in flatten_list([parser.players(scraper.players(letter)) for letter in string.ascii_uppercase]):
            startyear, endyear = [int(val) for val in p.get('source_player_years', '0-0').split('-')]
            if endyear >= minseason:
                pfr_players.append(p)
                logging.debug('added {}'.format(pprint.pformat(p)))

        if savepfr:
            with open(savepfr_fn, 'w') as outfile:
                json.dump(pfr_players, outfile)

    # get existing pfr_xref
    db = getdb()
    pfr_nflcom = pfr_nfl_xref(db)

    # now do comparison with nflcom players
    # key is name_position, value is list of dict
    # if value has length of 1, no dups
    # if value > 1, then issue with dups
    nflp = nflcom_players(db)

    for idx, p in enumerate(pfr_players):
        # first try existing pfr xref table for the id
        match = pfr_nflcom.get(p['source_player_id'])
        if match:
            pfr_players[idx]['nflcom_player_id'] = match

        # if not in current table, then have to try to match it
        # can try direct match, if that fails, then do fuzzy match
        else:
            key = '{}_{}'.format(p['source_player_name'], p['source_player_position'])
            match = nflp.get(key)

            # try direct match first
            if match:
                if len(match) == 1:
                    pfr_players[idx]['nflcom_player_id'] = match[0].get('player_id')
                elif len(match) > 1:
                    logging.warning('need to address dups: {}'.format(pprint.pformat(p)))
            else:
                match, confidence = process.extractOne(key, list(nflp.keys()))
                if confidence >= 80:
                    nflpmatch = nflp.get(match)
                    if len(nflpmatch) == 1:
                        pfr_players[idx]['nflcom_player_id'] = nflpmatch[0].get('player_id')
                    else:
                        logging.warning('need to address {}'.format(key))
                else:
                    logging.warning('no match for {} at {} -- {}'.format(key, confidence, match))

    if insertdb:
        for p in [pl for pl in pfr_players if p.get('nflcom_player_id')]:
            p.pop('source_player_years')
            db._insert_dict(p, 'extra_misc.player_xref')
            logging.info('inserted {}'.format(p))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()