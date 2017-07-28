'''
teams.py
Converts various team name formats to others
Different sites use different names for the same NFL teams
'''

import logging


t = {
'city_to_code': {
    'Arizona': 'ARI',
    'Atlanta': 'ATL',
    'Baltimore': 'BAL',
    'Buffalo': 'BUF',
    'Carolina': 'CAR',
    'Chicago': 'CHI',
    'Cincinnati': 'CIN',
    'Cleveland': 'CLE',
    'Dallas': 'DAL',
    'Denver': 'DEN',
    'Detroit': 'DET',
    'Green Bay': 'GB',
    'Houston': 'HOU',
    'Indianapolis': 'IND',
    'Jacksonville': 'JAC',
    'Kansas City': 'KC',
    'Los Angeles': 'LARM',
    'Miami': 'MIA',
    'Minnesota': 'MIN',
    'New England': 'NE',
    'New Orleans': 'NO',
    'New York Giants': 'NYG',
    'New York Jets': 'NYJ',
    'NY Giants': 'NYG',
    'NY Jets': 'NYJ',
    'Oakland': 'OAK',
    'Philadelphia': 'PHI',
    'Pittsburgh': 'PIT',
    'San Diego': 'SD',
    'San Francisco': 'SF',
    'Seattle': 'SEA',
    'St. Louis': 'STL',
    'Tampa Bay': 'TB',
    'Tampa': 'TB',
    'Tennessee': 'TEN',
    'Washington': 'WAS'
},

'long_to_code': {
    'Arizona Cardinals': 'ARI',
    'Atlanta Falcons': 'ATL',
    'Baltimore Ravens': 'BAL',
    'Buffalo Bills': 'BUF',
    'Carolina Panthers': 'CAR',
    'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN',
    'Cleveland Browns': 'CLE',
    'Dallas Cowboys': 'DAL',
    'Denver Broncos': 'DEN',
    'Detroit Lions': 'DET',
    'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU',
    'Indianapolis Colts': 'IND',
    'Jacksonville Jaguars': 'JAC',
    'Kansas City Chiefs': 'KC',
    'Los Angeles Rams': 'LARM',
    'Miami Dolphins': 'MIA',
    'Minnesota Vikings': 'MIN',
    'New England Patriots': 'NE',
    'New Orleans Saints': 'NO',
    'New York Giants': 'NYG',
    'New York Jets': 'NYJ',
    'Oakland Raiders': 'OAK',
    'Philadelphia Eagles': 'PHI',
    'Pittsburgh Steelers': 'PIT',
    'San Diego Chargers': 'SD',
    'San Francisco 49ers': 'SF',
    'Seattle Seahawks': 'SEA',
    'St. Louis Rams': 'STL',
    'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN',
    'Washington Redskins': 'WAS'
},

'nickname_to_code_2016': {
    'Cardinals': 'ARI',
    'Falcons': 'ATL',
    'Ravens': 'BAL',
    'Bills': 'BUF',
    'Panthers': 'CAR',
    'Bears': 'CHI',
    'Bengals': 'CIN',
    'Browns': 'CLE',
    'Cowboys': 'DAL',
    'Broncos': 'DEN',
    'Lions': 'DET',
    'Packers': 'GB',
    'Texans': 'HOU',
    'Colts': 'IND',
    'Jaguars': 'JAC',
    'Chiefs': 'KC',
    'Rams': 'LARM',
    'Dolphins': 'MIA',
    'Vikings': 'MIN',
    'Patriots': 'NE',
    'Saints': 'NO',
    'Giants': 'NYG',
    'Jets': 'NYJ',
    'Raiders': 'OAK',
    'Eagles': 'PHI',
    'Steelers': 'PIT',
    'Chargers': 'SD',
    '49ers': 'SF',
    'Seahawks': 'SEA',
    'Buccaneers': 'TB',
    'Titans': 'TEN',
    'Redskins': 'WAS'
},

'nickname_to_code_pre2016': {
    'Cardinals': 'ARI',
    'Falcons': 'ATL',
    'Ravens': 'BAL',
    'Bills': 'BUF',
    'Panthers': 'CAR',
    'Bears': 'CHI',
    'Bengals': 'CIN',
    'Browns': 'CLE',
    'Cowboys': 'DAL',
    'Broncos': 'DEN',
    'Lions': 'DET',
    'Packers': 'GB',
    'Texans': 'HOU',
    'Colts': 'IND',
    'Jaguars': 'JAC',
    'Chiefs': 'KC',
    'Rams': 'STL',
    'Dolphins': 'MIA',
    'Vikings': 'MIN',
    'Patriots': 'NE',
    'Saints': 'NO',
    'Giants': 'NYG',
    'Jets': 'NYJ',
    'Raiders': 'OAK',
    'Eagles': 'PHI',
    'Steelers': 'PIT',
    'Chargers': 'SD',
    '49ers': 'SF',
    'Seahawks': 'SEA',
    'Buccaneers': 'TB',
    'Titans': 'TEN',
    'Redskins': 'WAS'
}
}

_to_nfl = {
    'espn': {
        'ari': 'ARI', 'atl': 'ATL', 'bal': 'BAL', 'buf': 'BUF', 'car': 'CAR',
        'chi': 'CHI', 'cin': 'CIN', 'cle': 'CLE', 'dal': 'DAL', 'den': 'DEN',
        'det': 'DET', 'gb': 'GB', 'hou': 'HOU', 'ind': 'IND', 'jax': 'JAX',
        'kc': 'KC', 'lar': 'LA', 'lac': 'LAC', 'mia': 'MIA', 'min': 'MIN',
        'ne': 'NE', 'no': 'NO', 'nyg': 'NYG', 'nyj': 'NYJ', 'oak': 'OAK',
        'phi': 'PHI', 'pit': 'PIT', 'sd': 'SD', 'sea': 'SEA',
        'sf': 'SF', 'stl': 'STL', 'tb': 'TB', 'was': 'WAS'},
    'fo': {
        'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BUF': 'BUF', 'CAR': 'CAR', 'CHI': 'CHI',
        'CIN': 'CIN', 'CLE': 'CLE', 'DAL': 'DAL', 'DEN': 'DEN', 'DET': 'DET', 'GB': 'GB',
        'HOU': 'HOU', 'IND': 'IND', 'JAC': 'JAX', 'KC': 'KC', 'SD': 'LAC', 'LARM': 'LAR', 'MIA': 'MIA',
        'MIN': 'MIN', 'NE': 'NE', 'NO': 'NO', 'NYG': 'NYG', 'NYJ': 'NYJ', 'OAK': 'OAK',
        'PHI': 'PHI', 'PIT': 'PIT', 'SF': 'SF', 'SEA': 'SEA', 'TB': 'TB', 'TEN': 'TEN', 'WAS': 'WAS'
    },

    'pff': {
        'ARZ': 'ARI', 'ATL': 'ATL', 'BLT': 'BAL', 'BUF': 'BUF', 'CAR': 'CAR', 'CHI': 'CHI', 'CIN': 'CIN',
        'CLV': 'CLE', 'DAL': 'DAL', 'DEN': 'DEN', 'DET': 'DET', 'GB': 'GB', 'HST': 'HOU',
        'IND': 'IND', 'JAX': 'JAX', 'KC': 'KC', 'SD': 'LAC', 'LAR': 'LAR', 'MIA': 'MIA',
        'MIN': 'MIN', 'NE': 'NE', 'NO': 'NO', 'NYG': 'NYG', 'NYJ': 'NYJ', 'OAK': 'OAK',
        'PHI': 'PHI', 'PIT': 'PIT', 'SF': 'SF', 'SEA': 'SEA', 'TB': 'TB', 'TEN': 'TEN', 'WAS': 'WAS'
    },

    'pfr': {
        'crd': 'ARI', 'atl': 'ATL', 'rav': 'BAL', 'buf': 'BUF', 'car': 'CAR', 'chi': 'CHI',
        'cin': 'CIN', 'cle': 'CLE', 'dal': 'DAL', 'den': 'DEN', 'det': 'DET', 'gnb': 'GB',
        'htx': 'HOU', 'clt': 'IND', 'jax': 'JAX', 'kan': 'KC', 'sdg': 'LAC', 'ram': 'LAR',
        'mia': 'MIA', 'min': 'MIN', 'nwe': 'NE', 'nor': 'NO', 'nyg': 'NYG', 'nyj': 'NYJ',
        'rai': 'OAK', 'phi': 'PHI', 'pit': 'PIT', 'sfo': 'SF', 'oti': 'TEN', 'was': 'WAS'
    },

    'rg': {
        'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BUF': 'BUF', 'CAR': 'CAR', 'CHI': 'CHI', 'CIN': 'CIN', 'CLE': 'CLE',
        'DAL': 'DAL', 'DEN': 'DEN', 'DET': 'DET', 'GNB': 'GB', 'HOU': 'HOU', 'IND': 'IND',
        'JAX': 'JAX', 'KAN': 'KC', 'SDG': 'LAC', 'LAR': 'LAR', 'MIA': 'MIA', 'MIN': 'MIN',
        'NWE': 'NE', 'NOR': 'NO', 'NYG': 'NYG', 'NYJ': 'NYJ', 'OAK': 'OAK', 'PHI': 'PHI',
        'PIT': 'PIT', 'SFO': 'SF', 'SEA': 'SEA', 'TAM': 'TB', 'TEN': 'TEN', 'WAS': 'WAS'
    }
}

_from_nfl = {
    'pff': {'CHI': 'CHI', 'KC': 'KC', 'DET': 'DET', 'ATL': 'ATL', 'CLE': 'CLV', 'JAX': 'JAX', 'MIN': 'MIN', 'DEN': 'DEN',
           'ARI': 'ARZ', 'CIN': 'CIN', 'PIT': 'PIT', 'NYJ': 'NYJ', 'SF': 'SF', 'TB': 'TB', 'OAK': 'OAK', 'HOU': 'HST',
           'CAR': 'CAR', 'DAL': 'DAL', 'NO': 'NO', 'GB': 'GB', 'BAL': 'BLT', 'PHI': 'PHI', 'LAR': 'LAR', 'NE': 'NE',
           'NYG': 'NYG', 'WAS': 'WAS', 'SEA': 'SEA', 'TEN': 'TEN', 'BUF': 'BUF', 'LAC': 'SD', 'IND': 'IND', 'MIA': 'MIA'},
    'rg': {'CHI': 'CHI', 'KC': 'KAN', 'DET': 'DET', 'ATL': 'ATL', 'CLE': 'CLE', 'JAX': 'JAX', 'HOU': 'HOU', 'DEN': 'DEN',
           'ARI': 'ARI', 'CIN': 'CIN', 'PIT': 'PIT', 'NYJ': 'NYJ', 'SF': 'SFO', 'TB': 'TAM', 'OAK': 'OAK', 'BAL': 'BAL',
           'CAR': 'CAR', 'DAL': 'DAL', 'MIN': 'MIN', 'NO': 'NOR', 'GB': 'GNB', 'PHI': 'PHI', 'LAR': 'LAR', 'NE': 'NWE',
           'NYG': 'NYG', 'WAS': 'WAS', 'SEA': 'SEA', 'TEN': 'TEN', 'BUF': 'BUF', 'LAC': 'SDG', 'IND': 'IND', 'MIA': 'MIA'},
    'pfr': {'CHI': 'chi', 'KC': 'kan', 'DET': 'det', 'LAR': 'ram', 'CLE': 'cle', 'JAX': 'jax', 'HOU': 'htx', 'ARI': 'crd',
            'CIN': 'cin', 'PIT': 'pit', 'NYJ': 'nyj', 'SF': 'sfo', 'TB': 'tam', 'OAK': 'rai', 'MIN': 'min', 'CAR': 'car',
            'DAL': 'dal', 'NO': 'nor', 'WAS': 'was', 'BAL': 'rav', 'LAC': 'sdg', 'ATL': 'atl', 'NE': 'nwe', 'PHI': 'phi',
            'DEN': 'den', 'SEA': 'sea', 'GB': 'gnb', 'TEN': 'oti', 'BUF': 'buf', 'NYG': 'nyg', 'IND': 'clt', 'MIA': 'mia'},
    'fo': {'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BUF': 'BUF', 'CAR': 'CAR', 'CHI': 'CHI',
           'CIN': 'CIN', 'CLE': 'CLE', 'DAL': 'DAL', 'DEN': 'DEN', 'DET': 'DET', 'GB': 'GB', 'HOU': 'HOU',
           'IND': 'IND', 'JAX': 'JAC', 'KC': 'KC', 'LAC': 'SD', 'LAR': 'LARM', 'MIA': 'MIA', 'MIN': 'MIN',
           'NE': 'NE', 'NO': 'NO', 'NYG': 'NYG', 'NYJ': 'NYJ', 'OAK': 'OAK', 'PHI': 'PHI',
           'PIT': 'PIT', 'SEA': 'SEA', 'SF': 'SF', 'TB': 'TB', 'TEN': 'TEN', 'WAS': 'WAS'},
    'espn': {
            'ARI': 'ari', 'ATL': 'atl', 'BAL': 'bal', 'BUF': 'buf', 'CAR':
            'car', 'CHI': 'chi', 'CIN': 'cin', 'CLE': 'cle', 'DAL': 'dal',
            'DEN': 'den', 'DET': 'det', 'GB': 'gb',
            'HOU': 'hou', 'IND': 'ind', 'JAX': 'jax', 'KC': 'kc', 'LA': 'lar',
            'LAC': 'lac', 'MIA': 'mia', 'MIN': 'min', 'NE': 'ne', 'NO': 'no',
            'NYG': 'nyg', 'NYJ': 'nyj', 'OAK': 'oak', 'PHI': 'phi', 'PIT': 'pit',
            'SD': 'sd', 'SEA': 'sea', 'SF': 'sf', 'STL': 'stl', 'TB': 'tb'}
}

def city_to_code(name):
    return t['city_to_code'].get(name, None)

def football_outsiders_teams():
    return ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAC',
             'KC', 'MIA', 'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'OAK', 'PHI', 'PIT', 'SD', 'SEA', 'SF', 'STL', 'TB', 'TEN',
             'WAS']

def long_to_code(name):
    return t['long_to_code'].get(name, None)

def nickname_to_code(name, season_year):
    '''
    Converts nickname like steelers to PIT
    Args:
        name: steelers, broncos, etc.
        season_year: 2016, 2015, etc.

    Returns:
        team_code string PIT, DEN, etc.
    '''
    if name[0].isalpha():
        name = name.title()

    if season_year > 2015:
        return t['nickname_to_code_2016'].get(name, None)
    else:
        return t['nickname_to_code_pre2016'].get(name, None)


def from_nfl(team_code, site):
    '''
    Converts nfl team_code to specified site

    Args:
        team_code: 'CHI', 'ARZ', etc.
        site1: 'rg', 'pff', etc.

    Returns:
        str 'CHI', 'ARZ', etc. 
    '''
    sites = ['pff', 'fo', 'rg', 'pfr']
    if site in sites:
        return _from_nfl[site].get(team_code, None)
    else:
        raise ValueError('invalid site')

def to_nfl(team_code, site):
    '''
    Converts various team_codes to those used by nfl
    
    Args:
        team_code: 'CHI', 'ARZ', etc.
        site1: 'rg', 'pff', etc.
    
    Returns:
        str 'CHI', 'ARZ', etc. 
    '''
    sites = ['pff', 'fo', 'rg', 'pfr']
    if site in sites:
        return _to_nfl[site].get(team_code, None)
    else:
        raise ValueError('invalid site')

def espn_teams():
    '''
    Get all of the espn.com team codes ('ari', 'buf', etc.
    
    Returns:
        list
    '''
    return [t for t in _to_nfl['espn'].keys() if t != 'stl']

if __name__ == '__main__':
    pass
