#!/usr/env python
# -*- coding: utf-8 -*-
# numberfire_ff_projections.py

import json
import logging
import memcache
import pprint
import re
from urllib2 import Request, urlopen, URLError, HTTPError

def get(url):

    mc = memcache.Client(['127.0.0.1:11211'], debug=0)
    content = mc.get(url)

    if not content:
        try:
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36'
            headers = { 'User-Agent' : user_agent }
            req = Request(url=url, data=None, headers=headers)
            response = urlopen(req)
            content = response.read()
            logging.debug('successfully got %s' % url)
            mc.set(url, content)
                
        except HTTPError as e:
            logging.error('Error code: ', e.code)

        except URLError as e:
            logging.error('Reason: ', e.reason)

        except Exception as e:
            logging.error(e)

    else:
        logging.debug("got %s from cache" % url)

    return content

def parse_page(content):
    
    # have to hack the NF_DATA javascript variable, which contains JSON within
    # structure is: (1) projections (1a) players (1b) projections (2) teams
    # the (1a) players and (1b) projections are dictionaries where the key is the player or team id [quick lookup]
    # probably want to add name, slug, other info from "players" into projections
    
    try:
        m = re.search(r'NF_DATA\s*=\s*.*?("projections":\{.*?\"\}\}\})', content)
        projections_dict = json.loads('{' + m.group(1))
        players = projections_dict['projections']['players']
        player_projections = projections_dict['projections']['projections']
        teams = projections_dict['teams']
        return {'players': players, 'player_projections': player_projections, 'teams': teams}

    except Exception as e:
        logging.error(e)
        return None
    
def save_to_file(fn, data):
    with open(fn, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

def urls():
    return ['http://www.numberfire.com/nfl/fantasy/remaining-projections']
    
if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    players = []

    for url in urls():

        content = get(url)
        nf_data = parse_page(content)

        if nf_data:
            logging.debug("got numberfire data")
        else:
            logging.error("no numberfire data")           
    
    save_to_file('numberfire_nfl_players.json', nf_data['players'])
    save_to_file('numberfire_nfl_player_projections.json', nf_data['player_projections'])   
    save_to_file('numberfire_nfl_teams.json', nf_data['teams'])
    
