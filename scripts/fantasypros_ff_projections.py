#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
fantasypros_ff_projections.py

Usage:
    fantasypros_ff_projections.py
    optional arguments:
        -h, --help  show this help message and exit
        --save_csv filename.csv
        --save_json filename.json
'''

import argparse
import csv
import json
import logging
import os.path
import pprint

from fantasypros_projections.FantasyProsNFLParser import FantasyProsNFLParser
from fantasypros_projections.FantasyProsNFLScraper import FantasyProsNFLScraper


def save_csv(fn, data):
    '''

    :param fn:
    :param data:
    :return:
    '''
    headers = ['overall_rank', 'full_name', 'position', 'team', 'bye', 'best_rank', 'worst_rank', 'average_rank', 'stdev_rank', 'adp']

    with open(fn, 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()

        for item in data:
            writer.writerow(item)

def save_json(fn, data):
    '''

    :param fn:
    :param data:
    :return:
    '''
    with open(fn, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

if __name__ == '__main__':

    logging.basicConfig(level=logging.ERROR)

    parser = argparse.ArgumentParser()
    parser.add_argument('--save_csv', help='Filename to save to', required=False)
    parser.add_argument('--save_json', help='Filename to save to', required=False)
    args = vars(parser.parse_args())

    # can use this to test other methods
    #url = 'http://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php?export=xls'
    #fname = os.path.join(os.path.expanduser('~'), 'rankings.xls')

    # the basic script
    s = FantasyProsNFLScraper()
    p = FantasyProsNFLParser()
    players = p.projections(content=s.get_projections())
    print json.dumps(players)

    # options processing
    jsonfn = args.get('save_json', None)
    if jsonfn:
        save_json(jsonfn, players)

    csvfn = args.get('save_csv', None)
    if csvfn:
        save_csv(csvfn, players)
