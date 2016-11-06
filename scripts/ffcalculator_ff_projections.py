#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
fantasycalculator_ff_projections.py

Usage:
    fantasycalculator_ff_projections.py
    optional arguments:
        -h, --help  show this help message and exit
        --save_csv filename.csv
        --save_json filename.json
'''

import argparse
import csv
from ffcalculator_projections.FantasyFootballCalculatorParser import FantasyFootballCalculatorParser
from ffcalculator_projections.FantasyFootballCalculatorScraper import FantasyFootballCalculatorScraper
import json
import logging
import pprint

def save_csv(fn, data):
    headers = ['overall_rank', 'position', 'full_name', 'team', 'bye', 'fantasy_points_per_game']
    headers = headers + ['week%s_projection' % str(x) for x in range(1,18)]

    with open(fn, 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()

        for item in data:
            writer.writerow(item)

def save_json(fn, data):
    with open(fn, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    p = FantasyFootballCalculatorParser()
    s = FantasyFootballCalculatorScraper()

    parser = argparse.ArgumentParser()
    parser.add_argument('--save_csv', help='Filename to save to', required=False)
    parser.add_argument('--save_json', help='Filename to save to', required=False)
    args = vars(parser.parse_args())

    content = s.get_projections()

    players = p.projections(content)
    #logging.info(pprint.pformat(players))
    print json.dumps(players)

    jsonfn = args.get('save_json', None)
    if jsonfn:
        save_json(jsonfn, players)

    csvfn = args.get('save_csv', None)
    if csvfn:
        save_csv(csvfn, players)
