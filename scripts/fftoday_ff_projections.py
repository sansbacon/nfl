#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
fftoday_projections.py

Usage:
    fftoday_projections.py 
    optional arguments:
        -h, --help  show this help message and exit
        --positions 'qb' 'wr' 'rb'
        --save_csv filename.csv
        --save_json filename.json
'''

import argparse
import csv
from fftoday_projections.FFTodayParser import FFTodayParser
from fftoday_projections.FFTodayScraper import FFTodayScraper
import json
import logging
import pprint

def save_csv(fn, data):
    headers = ['fftoday_id', 'full_name', 'team', 'position', 'fantasy_points', 'bye']

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
    parser.add_argument('--save_csv', help='Filename to save to', required=False)
    parser.add_argument('--save_json', help='Filename to save to', required=False)
    parser.add_argument('-p', '--players', nargs='+', type=str)
    args = vars(parser.parse_args())

    logging.basicConfig(level=logging.ERROR)
    s = FFTodayScraper()
    p = FFTodayParser()

    if args.has_key('players'):
        pages = s.get_projections(positions=args['players'])
    else:
        pages = s.get_projections()

    players = p.projections(pages)
    logging.info(pprint.pformat(players))

    jsonfn = args.get('save_json', None)
    if jsonfn:
        save_json(jsonfn, players)

    csvfn = args.get('save_csv', None)
    if csvfn:
        save_csv(csvfn, players)
