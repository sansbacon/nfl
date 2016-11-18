#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
footballscientist_projections.py

Usage:
    footballscientist_projections.py -i <projections_file>
    optional arguments:
        -h, --help  show this help message and exit
        --positions 'qb' 'wr' 'rb' 'te' 'd-st'
        --save_csv filename.csv
        --save_json filename.json
'''

import argparse
import csv
from footballscientist_projections.FootballScientistParser import FootballScientistParser
import json
import logging
import pprint

def save_csv(fn, data):
    #headers = ['id', 'name', 'team', 'position', 'fpts']
    # need to document these headers

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

    logging.basicConfig(level=logging.DEBUG)
    p = FootballScientistParser(projections_file = args['infile'])
    players = p.projections()
    logging.debug(pprint.pformat(players))

    jsonfn = args.get('save_json', None)
    if jsonfn:
        save_json(jsonfn, players)

    csvfn = args.get('save_csv', None)
    if csvfn:
        save_csv(csvfn, players)
