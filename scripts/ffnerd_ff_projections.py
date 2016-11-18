#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
ffnerd_ff_projections.py

Usage:
    ffnerd_ff_projections.py
    optional arguments:
        -h, --help  show this help message and exit
        --save_csv filename.csv
        --save_json filename.json
'''

import argparse
import csv
import json
import logging
import os

from ffnerd_projections.FFNerdNFLParser import FFNerdNFLParser
from ffnerd_projections.FFNerdNFLScraper import FFNerdNFLScraper

from myfantasyleague_projections.MyFantasyLeagueNFLParser import MyFantasyLeagueNFLParser
import NameMatcher

def save_csv(fn, data):

    headers = ['ffnerd_id', 'ffnerd_rank', 'overall_rank', 'position_rank', 'position',
                   'full_name', 'fname', 'lname', 'team', 'bye', 'stdev_rank']

    with open(fn, 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()

        for item in data:
            writer.writerow(item)

def save_json(fn, data):
    with open(fn, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    s = FFNerdNFLScraper(os.environ.get('FFNERD_API_KEY'))
    p = FFNerdNFLParser(overall_rank_max=400)

    parser = argparse.ArgumentParser()
    parser.add_argument('--save_csv', help='Filename to save to', required=False)
    parser.add_argument('--save_json', help='Filename to save to', required=False)
    args = vars(parser.parse_args())

    projections, rankings = s.get_projections()
    players = p.projections(projections=projections, rankings=rankings)

    # do name matching
    # save parsing time
    mfl_json = 'mfl_players.json'
    if os.path.exists(mfl_json):
        with open(mfl_json) as data_file:
            players_match_from = json.load(data_file)
    else:
        mfl = MyFantasyLeagueNFLParser()

        # MyFantasyLeagueNFLParser.players returns a list of dictionaries
        # Easier to do name matching if transform to dictionary where full_name is key, player is value
        fname = 'myfantasyleague_projections/players.xml'
        positions = ['QB', 'RB', 'WR', 'TE']

        players_match_from = {p['full_name']: p for p in mfl.players(positions=positions, fname=fname)}
        save_json(mfl_json, players_match_from)

    for i in xrange(len(players)):
        try:
            players[i] = NameMatcher.match_player(to_match=players[i], match_from=players_match_from, site_id_key='espn_id')
        except:
            pass

    print json.dumps(players, indent=4, sort_keys=True)

    jsonfn = args.get('save_json', None)
    if jsonfn:
        save_json(jsonfn, players)

    csvfn = args.get('save_csv', None)
    if csvfn:
        save_csv(csvfn, players)