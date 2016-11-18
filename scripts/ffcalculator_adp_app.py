#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
fantasycalculator_adp_app.py

Usage:
    fantasycalculator_adp_app.py --league_size 12 --draft_position 3 --rounds 15
    optional arguments:
        -h, --help  show this help message and exit
        -l --league_size 8, 10, 12, etc.
        -d --draft_position 1, 2, 3, etc.
        -r --rounds 10, 11, 12, etc.
'''

import argparse
import collections
import logging

from ffcalculator_projections.FantasyFootballCalculatorParser import FantasyFootballCalculatorParser
from ffcalculator_projections.FantasyFootballCalculatorScraper import FantasyFootballCalculatorScraper


def all_picks(draft_position, league_size, rounds):
    picks = []
    
    # http://math.stackexchange.com/questions/298973/formula-for-snake-draft-pick-numbers
    for round in range(1, rounds + 1):
        if (round % 2 == 1):
            picks.append((round-1)*league_size+draft_position)
        else:
            picks.append(round*league_size-draft_position+1)

    return picks    

def sort_by_position(players):

    sorted_players = collections.OrderedDict()
    sorted_players['QB'] = []
    sorted_players['RB'] = []
    sorted_players['WR'] = []
    sorted_players['TE'] = []
    sorted_players['DEF'] = []

    for player in players:
        position = player['position'].upper()
        sorted_players[position].append(player)

    return sorted_players

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    p = FantasyFootballCalculatorParser()
    s = FantasyFootballCalculatorScraper()

    parser = argparse.ArgumentParser()
    parser.add_argument('--league_size', help='Number of team in league', required=True, type=int)
    parser.add_argument('--draft_position', help='Your pick number', required=True, type=int)
    parser.add_argument('--rounds', help='Number of rounds in draft', required=True, type=int)
    args = vars(parser.parse_args())

    # get the XML and parse into player dictionaries
    content = s.get_adp()
    players = p.adp(content, args['league_size'])
    players = sort_by_position(players)

    for pick in all_picks(args['draft_position'], args['league_size'], args['rounds']):
        print 'Pick %d' % pick
        print "------------------------"

        for position, players_at_position in players.iteritems():
            header = '%s: ' % position

            # get lower and upper bounds, confine to zero and rounds * teams
            lower_bound = pick - 6
            if lower_bound < 0:
                lower_bound = 0

            upper_bound = pick + 6
            if upper_bound > args['league_size'] * args['rounds']:
                upper_bound = args['league_size'] * args['rounds']

            available = filter(lambda x: x['overall_pick'] >= lower_bound and x['overall_pick'] <= upper_bound, players_at_position)
            available_names = [x['full_name'] for x in available]
            print header, (", ".join(available_names))

        print "------------------------"
