#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Usage:
    espn_ff_projections.py 
    optional arguments:
        -h, --help  show this help message and exit
        --save_csv filename.csv
        --save_json filename.json
'''

import argparse
import csv
from espn_projections.ESPNNFLParser import ESPNNFLParser
from espn_projections.ESPNNFLScraper import ESPNNFLScraper
import json
import logging
import pprint

def save_csv(fn, data):
    headers = ['espn_id', 'full_name', 'team', 'position', 'injury', 'fantasy_points']

    with open(fn, 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()
        
        for item in data:
            writer.writerow(item)

def save_json(fn, data):
    with open(fn, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

if __name__ == '__main__':

    # parse arguments into args dictionary
    parser = argparse.ArgumentParser()
    parser.add_argument('--save_csv', help='Filename to save to', required=False)
    parser.add_argument('--save_json', help='Filename to save to', required=False)
    args = vars(parser.parse_args())

    # main variables
    #logging.basicConfig(level=logging.ERROR)
    s = ESPNNFLScraper()
    p = ESPNNFLParser()
    players = []

    # script loop
    pages = s.get_projections()
    
    for page in pages:
        players = players + p.projections(page)

    # let's see it (or not)
    #logging.info(pprint.pprint(players))
    print json.dumps(players)

    # save to json
    jsonfn = args.get('save_json', None)
    if jsonfn:
        save_json(jsonfn, players)

    # save to csv
    csvfn = args.get('save_csv', None)
    if csvfn:
        save_csv(csvfn, players)
