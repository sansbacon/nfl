"""
teams.py
Converts various team name formats to standard format
Different sites use different names for the same NFL teams
"""
import logging

logger = logging.getLogger(__name__)


TEAM_CODES = {
    'ARI': ['ARI', 'Arizona Cardinals', 'Cardinals', 'Arizona', 'crd'],
    'ATL': ['ATL', 'Atlanta Falcons', 'Falcons', 'Atlanta', 'atl'],
    'BAL': ['BAL', 'Baltimore Ravens', 'Ravens', 'Baltimore', 'rav'],
    'BUF': ['BUF', 'Buffalo Bills', 'Bills', 'Buffalo', 'buf'],
    'CAR': ['CAR', 'Carolina Panthers', 'Panthers', 'Carolina', 'car'],
    'CHI': ['CHI', 'Chicago Bears', 'Bears', 'Chicago', 'chi'],
    'CIN': ['CIN', 'Cincinnati Bengals', 'Bengals', 'Cincinnati', 'cin'],
    'CLE': ['CLE', 'Cleveland Browns', 'Browns', 'Cleveland', 'cle'],
    'DAL': ['DAL', 'Dallas Cowboys', 'Cowboys', 'Dallas', 'dal'],
    'DEN': ['DEN', 'Denver Broncos', 'Broncos', 'Denver', 'den'],
    'DET': ['DET', 'Detroit Lions', 'Lions', 'Detroit', 'det'],
    'GB': ['GB', 'Green Bay Packers', 'Packers', 'Green Bay', 'GNB', 'gnb'],
    'HOU': ['HOU', 'Houston Texans', 'Texans', 'Houston', 'htx'],
    'IND': ['IND', 'Indianapolis Colts', 'Colts', 'Indianapolis', 'clt'],
    'JAC': ['JAC', 'Jacksonville Jaguars', 'Jaguars', 'Jacksonville', 'jac', 'jax'],
    'KC': ['KC', 'Kansas City Chiefs', 'Chiefs', 'Kansas City', 'kan', 'KAN'],
    'LAC': ['LAC', 'Los Angeles Chargers', 'LA Chargers', 'San Diego Chargers', 'Chargers', 'San Diego', 'SD', 'sdg', 'SDG'],
    'LAR': ['LAR', 'LA', 'Los Angeles Rams', 'LA Rams', 'St. Louis Rams', 'Rams', 'St. Louis', 'ram'],
    'MIA': ['MIA', 'Miami Dolphins', 'Dolphins', 'Miami', 'mia'],
    'MIN': ['MIN', 'Minnesota Vikings', 'Vikings', 'Minnesota', 'min'],
    'NE': ['NE', 'New England Patriots', 'Patriots', 'New England', 'NEP', 'nwe', 'NWE'],
    'NO': ['NO', 'New Orleans Saints', 'Saints', 'New Orleans', 'NOS', 'nor', 'NOR'],
    'NYG': ['NYG', 'New York Giants', 'Giants', 'nyg'],
    'NYJ': ['NYJ', 'New York Jets', 'Jets', 'nyj'],
    'OAK': ['OAK', 'Oakland Raiders', 'Raiders', 'Oakland', 'rai'],
    'PHI': ['PHI', 'Philadelphia Eagles', 'Eagles', 'Philadelphia', 'phi'],
    'PIT': ['PIT', 'Pittsburgh Steelers', 'Steelers', 'Pittsburgh', 'pit'],
    'SF': ['SF', 'San Francisco 49ers', '49ers', 'SFO', 'San Francisco', 'sfo'],
    'SEA': ['SEA', 'Seattle Seahawks', 'Seahawks', 'Seattle', 'sea'],
    'TB': ['TB', 'Tampa Bay Buccaneers', 'Buccaneers', 'TBO', 'tam', 'TAM', 'Tampa', 'Tampa Bay'],
    'TEN': ['TEN', 'Tennessee Titans', 'Titans', 'Tennessee', 'oti'],
    'WAS': ['WAS', 'Washington Redskins', 'Redskins', 'Washington', 'was']
}


def get_team_code(team):
    """Standardizes team code across sites

    Args:
        team (str): the code or team name

    Returns:
        str: 2-3 letter team code, ATL, BAL, etc.

    Examples:
        >>>team_code('Ravens')
        'BAL'

        >>>team_code('JAC')
        'JAX'
    """
    if team in TEAM_CODES:
        return team
    matches = [(k, v) for k, v in TEAM_CODES.items()
               if (team in v or
                   team.title() in v or
                   team.lower() in v or
                   team.upper() in v)
               ]
    if len(matches) == 1:
        return matches[0][0]
    raise ValueError(f'no match for {team}')


if __name__ == "__main__":
    pass
