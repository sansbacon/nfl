"""
teams.py
Converts various team name formats to standard format
Different sites use different names for the same NFL teams
"""
import logging

logger = logging.getLogger(__name__)


TEAM_CODES = {
    "ARI": ["ARI", "Arizona Cardinals", "Cardinals", "Arizona", "crd"],
    "ATL": ["ATL", "Atlanta Falcons", "Falcons", "Atlanta", "atl"],
    "BAL": ["BAL", "Baltimore Ravens", "Ravens", "Baltimore", "rav"],
    "BUF": ["BUF", "Buffalo Bills", "Bills", "Buffalo", "buf"],
    "CAR": ["CAR", "Carolina Panthers", "Panthers", "Carolina", "car"],
    "CHI": ["CHI", "Chicago Bears", "Bears", "Chicago", "chi"],
    "CIN": ["CIN", "Cincinnati Bengals", "Bengals", "Cincinnati", "cin"],
    "CLE": ["CLE", "Cleveland Browns", "Browns", "Cleveland", "cle"],
    "DAL": ["DAL", "Dallas Cowboys", "Cowboys", "Dallas", "dal"],
    "DEN": ["DEN", "Denver Broncos", "Broncos", "Denver", "den"],
    "DET": ["DET", "Detroit Lions", "Lions", "Detroit", "det"],
    "GB": ["GB", "Green Bay Packers", "Packers", "Green Bay", "GNB", "gnb"],
    "HOU": ["HOU", "Houston Texans", "Texans", "Houston", "htx"],
    "IND": ["IND", "Indianapolis Colts", "Colts", "Indianapolis", "clt"],
    "JAC": ["JAC", "Jacksonville Jaguars", "Jaguars", "Jacksonville", "jac", "jax"],
    "KC": ["KC", "Kansas City Chiefs", "Chiefs", "Kansas City", "kan", "KAN"],
    "LAC": [
        "LAC",
        "Los Angeles Chargers",
        "LA Chargers",
        "San Diego Chargers",
        "Chargers",
        "San Diego",
        "SD",
        "sdg",
        "SDG",
    ],
    "LAR": [
        "LAR",
        "LA",
        "Los Angeles Rams",
        "LA Rams",
        "St. Louis Rams",
        "Rams",
        "St. Louis",
        "ram",
    ],
    "MIA": ["MIA", "Miami Dolphins", "Dolphins", "Miami", "mia"],
    "MIN": ["MIN", "Minnesota Vikings", "Vikings", "Minnesota", "min"],
    "NE": [
        "NE",
        "New England Patriots",
        "Patriots",
        "New England",
        "NEP",
        "nwe",
        "NWE",
    ],
    "NO": ["NO", "New Orleans Saints", "Saints", "New Orleans", "NOS", "nor", "NOR"],
    "NYG": ["NYG", "New York Giants", "Giants", "nyg"],
    "NYJ": ["NYJ", "New York Jets", "Jets", "nyj"],
    "OAK": ["OAK", "Oakland Raiders", "Raiders", "Oakland", "rai"],
    "PHI": ["PHI", "Philadelphia Eagles", "Eagles", "Philadelphia", "phi"],
    "PIT": ["PIT", "Pittsburgh Steelers", "Steelers", "Pittsburgh", "pit"],
    "SF": ["SF", "San Francisco 49ers", "49ers", "SFO", "San Francisco", "sfo"],
    "SEA": ["SEA", "Seattle Seahawks", "Seahawks", "Seattle", "sea"],
    "TB": [
        "TB",
        "Tampa Bay Buccaneers",
        "Buccaneers",
        "TBO",
        "tam",
        "TAM",
        "Tampa",
        "Tampa Bay",
    ],
    "TEN": ["TEN", "Tennessee Titans", "Titans", "Tennessee", "oti"],
    "WAS": ["WAS", "Washington Redskins", "Redskins", "Washington", "was"],
}

ESPN_TEAMS = [
    {
        "source_team_city": "Indianapolis",
        "source_team_code": "Ind",
        "source_team_id": 11,
        "source_team_name": "Colts",
    },
    {
        "source_team_city": "Kansas City",
        "source_team_code": "KC",
        "source_team_id": 12,
        "source_team_name": "Chiefs",
    },
    {
        "source_team_city": "Oakland",
        "source_team_code": "Oak",
        "source_team_id": 13,
        "source_team_name": "Raiders",
    },
    {
        "source_team_city": "Los Angeles",
        "source_team_code": "LAR",
        "source_team_id": 14,
        "source_team_name": "Rams",
    },
    {
        "source_team_city": "Miami",
        "source_team_code": "Mia",
        "source_team_id": 15,
        "source_team_name": "Dolphins",
    },
    {
        "source_team_city": "Minnesota",
        "source_team_code": "Min",
        "source_team_id": 16,
        "source_team_name": "Vikings",
    },
    {
        "source_team_city": "New England",
        "source_team_code": "NE",
        "source_team_id": 17,
        "source_team_name": "Patriots",
    },
    {
        "source_team_city": "New Orleans",
        "source_team_code": "NO",
        "source_team_id": 18,
        "source_team_name": "Saints",
    },
    {
        "source_team_city": "New York",
        "source_team_code": "NYG",
        "source_team_id": 19,
        "source_team_name": "Giants",
    },
    {
        "source_team_city": "New York",
        "source_team_code": "NYJ",
        "source_team_id": 20,
        "source_team_name": "Jets",
    },
    {
        "source_team_city": "Philadelphia",
        "source_team_code": "Phi",
        "source_team_id": 21,
        "source_team_name": "Eagles",
    },
    {
        "source_team_city": "Arizona",
        "source_team_code": "Ari",
        "source_team_id": 22,
        "source_team_name": "Cardinals",
    },
    {
        "source_team_city": "Pittsburgh",
        "source_team_code": "Pit",
        "source_team_id": 23,
        "source_team_name": "Steelers",
    },
    {
        "source_team_city": "Los Angeles",
        "source_team_code": "LAC",
        "source_team_id": 24,
        "source_team_name": "Chargers",
    },
    {
        "source_team_city": "San Francisco",
        "source_team_code": "SF",
        "source_team_id": 25,
        "source_team_name": "49ers",
    },
    {
        "source_team_city": "Seattle",
        "source_team_code": "Sea",
        "source_team_id": 26,
        "source_team_name": "Seahawks",
    },
    {
        "source_team_city": "Tampa Bay",
        "source_team_code": "TB",
        "source_team_id": 27,
        "source_team_name": "Buccaneers",
    },
    {
        "source_team_city": "Washington",
        "source_team_code": "Wsh",
        "source_team_id": 28,
        "source_team_name": "Redskins",
    },
    {
        "source_team_city": "Carolina",
        "source_team_code": "Car",
        "source_team_id": 29,
        "source_team_name": "Panthers",
    },
    {
        "source_team_city": "Jacksonville",
        "source_team_code": "Jax",
        "source_team_id": 30,
        "source_team_name": "Jaguars",
    },
    {
        "source_team_city": "Baltimore",
        "source_team_code": "Bal",
        "source_team_id": 33,
        "source_team_name": "Ravens",
    },
    {
        "source_team_city": "Houston",
        "source_team_code": "Hou",
        "source_team_id": 34,
        "source_team_name": "Texans",
    },
    {
        "source_team_city": "",
        "source_team_code": "FA",
        "source_team_id": 0,
        "source_team_name": "FA",
    },
    {
        "source_team_city": "Atlanta",
        "source_team_code": "Atl",
        "source_team_id": 1,
        "source_team_name": "Falcons",
    },
    {
        "source_team_city": "Buffalo",
        "source_team_code": "Buf",
        "source_team_id": 2,
        "source_team_name": "Bills",
    },
    {
        "source_team_city": "Chicago",
        "source_team_code": "Chi",
        "source_team_id": 3,
        "source_team_name": "Bears",
    },
    {
        "source_team_city": "Cincinnati",
        "source_team_code": "Cin",
        "source_team_id": 4,
        "source_team_name": "Bengals",
    },
    {
        "source_team_city": "Cleveland",
        "source_team_code": "Cle",
        "source_team_id": 5,
        "source_team_name": "Browns",
    },
    {
        "source_team_city": "Dallas",
        "source_team_code": "Dal",
        "source_team_id": 6,
        "source_team_name": "Cowboys",
    },
    {
        "source_team_city": "Denver",
        "source_team_code": "Den",
        "source_team_id": 7,
        "source_team_name": "Broncos",
    },
    {
        "source_team_city": "Detroit",
        "source_team_code": "Det",
        "source_team_id": 8,
        "source_team_name": "Lions",
    },
    {
        "source_team_city": "Green Bay",
        "source_team_code": "GB",
        "source_team_id": 9,
        "source_team_name": "Packers",
    },
    {
        "source_team_city": "Tennessee",
        "source_team_code": "Ten",
        "source_team_id": 10,
        "source_team_name": "Titans",
    },
]


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
    matches = [
        (k, v)
        for k, v in TEAM_CODES.items()
        if (team in v or team.title() in v or team.lower() in v or team.upper() in v)
    ]
    if len(matches) == 1:
        return matches[0][0]
    raise ValueError(f"no match for {team}")


if __name__ == "__main__":
    pass
