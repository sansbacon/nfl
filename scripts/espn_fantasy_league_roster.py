# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import json
import os
import random

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

from nfl.scrapers.espn_fantasy import ESPNFantasyScraper
from nfl.parsers.espn_fantasy import ESPNFantasyParser

profile = '/home/sansbacon/.mozilla/firefox/6h98gbaj.default'
config = configparser.ConfigParser()
config.read(os.path.join(os.path.expanduser('~'), '.fantasy'))
s = ESPNFantasyScraper(config=config, profile=profile)
parser = ESPNFantasyParser() 

with open('/home/sansbacon/espnteams.json', 'r') as infile:
    teams = json.load(infile)

all_players = []

# waiting for OFL draft - can delete afterwards
for team in teams[1:]:
    content = s.fantasy_league_rosters(team['leagueId'])
    players = parser.fantasy_league_rosters(content)

    if players:
        for idx, pl in enumerate(players):
            players[idx]['source_league_size'] = team.get('leagueSize')
        print(random.choice(players))
        db.insert_dicts(players, 'extra_fantasy.league_roster')
        all_players += players
        print('finished {}'.format(team['leagueName']))
    else:
        print('could not get players for {}'.format(team['leagueName']))

with open('/home/sansbacon/espn_rosters.json', 'w') as outfile:
    json.dump(all_players, outfile)