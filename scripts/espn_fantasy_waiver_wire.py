# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division

import json
import logging
import os
import sys

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

for team in teams:                             
    for pos in ['qb', 'rb', 'wr', 'te', 'dst', 'k']:
        content = s.fantasy_waiver_wire(team_id=team.get('teamId'), league_id=team.get('leagueId'),
                                        season=team.get('seasonId'), position=pos)
        players = parser.fantasy_waiver_wire(content)
        for idx, pl in enumerate(players):
            players[idx]['source_league_id'] = team.get('leagueId')
            players[idx]['season_year'] = team.get('seasonId')
            players[idx]['source_league_size'] = team.get('leagueSize')
        db.insert_dicts(players, 'extra_fantasy.waiver_wire')

