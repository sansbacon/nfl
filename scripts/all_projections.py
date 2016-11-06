#!/usr/bin/env python

import json
import logging
import pprint
from subprocess import STDOUT, check_call
from tempfile import NamedTemporaryFile

from myfantasyleague_projections.MyFantasyLeagueNFLParser import MyFantasyLeagueNFLParser
import NameMatcher

logging.basicConfig(filename='all_projections.log', level=logging.INFO)

commands = {
    'espn': 'espn-nfl-projections',
    'fpros': 'fantasypros-nfl-projections',
    #'ffcalc': 'ffcalculator-projections',
    'ffnerd': 'ffnerd-projections',
    'fboutsiders': 'footballoutsiders-projections',
    #'fftoday': 'fftoday-projections',
    #'ffcalc': 'ffcalculator-projections',
}

def run_command(command):
    '''

    :param command (str): the command you want to run
    :return result (str): the output of the command you ran
    '''
    # http://stackoverflow.com/questions/13835055/python-subprocess-check-output-much-slower-then-call
    with NamedTemporaryFile() as f:
        check_call([command], stdout=f, stderr=STDOUT)
        f.seek(0)
        result = f.read()

    return result

def main():

    p = MyFantasyLeagueNFLParser()
    matched_players = []
    unmatched_players = []

    # MyFantasyLeagueNFLParser.players returns a list of dictionaries
    # Easier to do name matching if transform to dictionary where full_name is key, player is value
    fname = 'myfantasyleague_projections/players.xml'
    positions = ['QB', 'RB', 'WR', 'TE']
    players_match_from = {player['full_name']: player for player in p.players(positions=positions, fname=fname)}

    # now get players from other sites
    for site, command in commands.items():

        result = run_command(command)

        try:
            players_to_match = json.loads(result)

            for player in players_to_match:

                try:
                    full_name, first_last = NameMatcher.fix_name(player['full_name'])
                    player['full_name'] = full_name
                    player['first_last'] = first_last
                    player = NameMatcher.match_player(to_match=player, match_from=players_match_from, site_id_key='espn_id')

                    if player.get('espn_id') is not None:
                        matched_players.append(player)
                    else:
                        unmatched_players.append(player)

                except Exception as ie:
                    logging.exception('%s: threw inner exception' % player['full_name'])

        except Exception as e:
            logging.exception('%s: threw outer exception')

    print json.dumps(matched_players, indent=4, sort_keys=True)

if __name__ == '__main__':
    main()
