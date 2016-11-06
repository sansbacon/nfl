#!/usr/bin/env python

import csv
import json
import logging
import os
import pprint


from myfantasyleague_projections.MyFantasyLeagueNFLParser import MyFantasyLeagueNFLParser

logging.basicConfig(filename='combine_projections.log', level=logging.ERROR)

def load_players(jsonfn):

    if os.path.isfile(jsonfn):
        with open(jsonfn) as data_file:
            return json.load(data_file)

    else:
        return None

def save_csv(fn, data):

    headers = ['espn_id', 'full_name', 'team', 'position', 'age', 'fantasy_points',
        'stdev_rank', 'injury', 'risk', 'bye']

    clean_data = []

    for item in data:
        player = {header: item.get(header, None) for header in headers}

    with open(fn, 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()

        for clean_item in clean_data:
            try:
                writer.writerow(clean_item)
            except Exception as e:
                print 'could not write %s' % pprint.pformat(e.message)

def save_json(fn, data):
    with open(fn, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

def main():

    p = MyFantasyLeagueNFLParser()

    # dictionary of dictionaries: key is espn_id, value is player dictionary
    combined = {}

    # now get players from other sites
    for site in ['espn', 'ffnerd', 'fboutsiders']: #, 'ffcalculator', 'fftoday', 'fboutsiders']:

        #using espn_id as the key, so this is first
        if site == 'espn':
            jsonfn = '/home/sansbacon/workspace/python-nfl-projections/combined/espn-projections.json'
            players = load_players(jsonfn)

            for player in players:
                fantasy_points = player.get('fantasy_points')
                player['fantasy_points'] = [fantasy_points]
                combined[player.get('espn_id')] = player


        # now i need to update the existing item with other data
        elif site == 'fboutsiders':
            jsonfn = '/home/sansbacon/workspace/python-nfl-projections/combined/fboutsiders-projections.json'
            players = load_players(jsonfn)

            # if player already exists, update with fboutsiders data
            # if not, then add fboutsiders player to combined
            for player in players:
                combined_player = combined.get(player.get('espn_id'))
                if combined_player:
                    combined_player['risk'] = player.get('risk')
                    combined_player['bye'] = player.get('bye')
                    combined_player['age'] = player.get('age')
                    combined_player['fantasy_points'].append(player.get('fantasy_points'))
                    combined[player.get('espn_id')] = combined_player

                else:
                    fantasy_points = player.get('fantasy_points')
                    player['fantasy_points'] = [fantasy_points]
                    combined[player.get('espn_id')] = player


        elif site == 'ffnerd':
            players = load_players('/home/sansbacon/workspace/python-nfl-projections/combined/ffnerd-projections.json')

            # if player already exists, update with ffnerd data
            # if not, then add ffnerd player to combined
            for player in players:
                combined_player = combined.get(player.get('espn_id'))

                if combined_player:
                    combined_player['stdev_rank'] = player.get('stdev_rank')
                    combined_player['fantasy_points'].append(player.get('fantasy_points'))
                    combined[player.get('espn_id')] = combined_player

                else:
                    fantasy_points = player.get('fantasy_points')
                    player['fantasy_points'] = [fantasy_points]
                    combined[player.get('espn_id')] = player

    for espn_id, player in combined.items():

        sum_fpts = 0.0

        for fpts in player.get('fantasy_points', None):

            try:
                sum_fpts += float(fpts)

            except:
                pass

        if sum_fpts > 0:
            try:
                avg_fpts = sum_fpts / float(len(fpts))
                player['fantasy_points'] = avg_fpts
                combined['espn_id'] = player

            except:
                pass

    print json.dumps(combined, indent=4, sort_keys=True)
    save_json('combined.json', combined.values())
    save_csv('combined.csv', combined.values())

if __name__ == '__main__':
    main()
