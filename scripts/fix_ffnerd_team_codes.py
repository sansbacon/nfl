# fix_ffnerd_team_codes.py

import json

convert = {
 'FA*': 'FA',
 'GBP': 'GB',
 'KAN': 'KC',
 'KCC': 'KC',
 'NEP': 'NE',
 'NOS': 'NO',
 'SDC': 'SD',
 'SFO': 'SF',
 'TBB': 'TB'
}

for idx, p in enumerate(cp):
    if p.has_key('team'):
        team_code = p['team']
        if convert.has_key(team_code):
            cp[idx]['team'] = convert[team_code]

for p in cp:
    if p.has_key('team') and convert.has_key(p['team']):
        print 'error: %s not converted' % p['team']

with open('canonical_players_2.json', 'w') as outfile:
    json.dump(cp, outfile, indent=4, sort_keys=True)
    
