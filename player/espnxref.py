from collections import defaultdict

from nfl.names import first_last
from nfl.scrapers.espn import ESPNNFLScraper
from nfl.parsers.espn import ESPNNFLParser

scraper = ESPNNFLScraper()
parser = ESPNNFLParser()
players = []

for pos in ['qb', 'rb', 'wr', 'te', 'k']:
    players += parser.players_position(scraper.players_position(pos), pos)
    print('finished {}'.format(pos))

# nflcom players
nflq = """SELECT * FROM player WHERE position != 'UNK' AND position IS NOT NULL"""
nflcom_players = {'{}_{}'.format(p['full_name'], p['position']): p 
                  for p in db.select_dict(nflq)}

# check for duplicates
# count player keys 
dupcheck_espn_xref = defaultdict(int)
for p in db.select_dict(q):
    name = first_last(p['source_player_name'])
    pos = p['source_player_position']    
    key = '{}_{}'.format(name, pos)
    dupcheck_espn_xref[key] += 1

dupcheck_espn_players = defaultdict(int)
for p in players:
    name = first_last(p['source_player_name'])
    pos = p['source_player_position']    
    key = '{}_{}'.format(name, pos)
    dupcheck_espn_players[key] += 1

# if keys > 1, then need to address duplicates
dups_espn_xref = [{k:v} for k,v in dupcheck_espn_xref.items() if v > 1]
dups_espn_players = [{k:v} for k,v in dupcheck_espn_players.items() if v > 1]

if dups_espn or dups_espn_players:
    print(dups_espn_xref)
    print(dups_espn_players)
    raise ValueError('must address duplicates')

dups = ['Michael Thomas']

# if no duplicates, then compare existing xref to players
# from the website 
espn_xref = {}
for p in db.select_dict(q):
    name = first_last(p['source_player_name'])
    if name in dups:
        pass
    else:
        pos = p['source_player_position']    
        key = '{}_{}'.format(name, pos)
        espn_xref[key] = p
    
espn_players = {}
for p in players:
    name = first_last(p['source_player_name'])
    if name in dups:
        pass
    else:
        pos = p['source_player_position']    
        key = '{}_{}'.format(name, pos.upper())
        espn_players[key] = p

to_add = []
for k,v in espn_players.items():
    match = espn_xref.get(k)
    if match:
        if v['source_player_id'] != match['source_player_id']:
            print(v['source_player_name'])
    else:
        match = nflcom_players.get(k)
        if match:
            pl = v
            pl['source_player_position'] = pl['source_player_position'].upper()
            pl['nflcom_player_id'] = match['player_id']
            pl.pop('college', None)
            pl.pop('source_team_code', None)
            pl.pop('source_team_name', None)
            to_add.append(pl)
            
db.insert_dict(to_add, 'extra_misc.player_xref')
