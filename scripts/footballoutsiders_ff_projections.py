#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
footballoutsiders_ff_projections.py

Usage:
    footballoutsiders_ff_projections.py -i <projections_file>
    optional arguments:
        -h, --help  show this help message and exit
        --positions 'qb' 'wr' 'rb' 'te' 'd-st'
        --save_csv filename.csv
        --save_json filename.json
'''

import argparse
import csv
import json
import logging
import os
import pprint

from footballoutsiders_projections.FootballOutsidersNFLParser import FootballOutsidersNFLParser
from myfantasyleague_projections.MyFantasyLeagueNFLParser import MyFantasyLeagueNFLParser
import NameMatcher

def save_csv(fn, data):
    headers = ['espn_id', 'full_name', 'team', 'position', 'age', 'fantasy_points',
        'first_last', 'position_rank', 'risk', 'auction_value', 'bye']

    with open(fn, 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()
        
        for item in data:
            writer.writerow(item)

def save_json(fn, data):
    with open(fn, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--infile', help='Filename to save to', type=str, required=True)
    parser.add_argument('--save_csv', help='Filename to save to', required=False)
    parser.add_argument('--save_json', help='Filename to save to', required=False)
    parser.add_argument('-p', '--players', nargs='+', type=str)
    args = vars(parser.parse_args())

    logging.basicConfig(level=logging.INFO)
    p = FootballOutsidersNFLParser(projections_file = args['infile'])
    players = p.projections()

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

        players_match_from = {player['full_name']: player for player in mfl.players(positions=positions, fname=fname)}
        save_json(mfl_json, players_match_from)

    for i in xrange(len(players)):
        try:
            players[i] = NameMatcher.match_player(to_match=players[i], match_from=players_match_from, site_id_key='espn_id')
        except:
            pass

    # dump to stdout
    pprint.pprint(players, indent=4)

    # save to file if parameter set
    jsonfn = args.get('save_json', None)
    if jsonfn:
        save_json(jsonfn, players)

    csvfn = args.get('save_csv', None)
    if csvfn:
        save_csv(csvfn, players)