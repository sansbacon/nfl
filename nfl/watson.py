# -*- coding: utf-8 -*-

"""
# watson.py
# classes for scraping, parsing watson football data

Usage:
    logging.basicConfig(level=logging.INFO)
    s = Scraper()
    p = Parser()
    for player in p.players(s.players(2019)):
        player_id = player['playerid']
        logging.info('starting %s', player)
        content = s.weekly_projection(2019, player_id)
        print(p.weekly_projection(content))

"""

import json
import logging

import pendulum

from nfl.espn_api import ID_TEAM_DICT
from sportscraper.scraper import RequestScraper


class Scraper(RequestScraper):
    """
    Scrape Watson football projections

    """
    @property
    def base_url(self):
        """
        Base watson url

        Returns:
            str

        """
        return 'http://watsonfantasyfootball.espn.com/espnpartner/dallas'

    def players(self, season_year):
        """
        Gets watson players

        Args:
            season_year(int): 2018, etc.

        Returns:
            list: of dict

        """
        url = f"{self.base_url}/players/players_ESPNFantasyFootball_{season_year}.json"
        return self.get_json(url)

    def weekly_projection(self, season_year, pid):
        """
        Gets Watson projections for a player

        Args:
            season_year(int): 2018, etc.
            pid(int): player ID (10000, etc.)

        Returns:
            dict - parsed JSON

        """
        url = f"{self.base_url}/projections/projections_{pid}_ESPNFantasyFootball_{season_year}.json"
        return self.get_json(url)


class Parser:
    """
    Parse watson for football stats

    """

    def __init__(self):
        """
        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    @staticmethod
    def players(content, wanted=None):
        """
        Parses list of dict into player

        Args:
            content: dict - parsed JSON

        Returns:
            list of player dict
        """
        if not wanted:
            wanted = ["FULL_NAME", "FANTASY_PLAYER_ID", "PLAYERID", "POSITION", "TEAM"]
        return [{k.lower(): v for k, v in p.items() if k in wanted} for p in content]

    @staticmethod
    def weekly_projection(content, most_recent_only=True):
        """
        Parses weekly projection

        Args:
            content(list): parsed JSON
            most_recent_only(bool)

        Returns:
            list

        """
        vals = []

        # have multiple time-stamped projections
        if most_recent_only:
            projections = [content[-1]]
        else:
            projections = content

        for projection in projections:
            d = {k.lower(): v for k, v in projection.items()}
            if (
                projection.get("SCORE_DISTRIBUTION")
                and len(projection.get("SCORE_DISTRIBUTION")) > 5
            ):
                try:
                    d["score_distribution"] = json.loads(
                        projection["SCORE_DISTRIBUTION"]
                    )
                except json.decoder.JSONDecodeError as je:
                    logging.exception(je)
            d["execution_timestamp"] = pendulum.parse(
                d["execution_timestamp"], tz="America/Chicago"
            )
            d["data_timestamp"] = pendulum.parse(
                d["data_timestamp"], tz="America/Chicago"
            )
            vals.append(d)
        return vals


class Agent:
    """
    Combines common scraping/parsing tasks

    Usage:
        a = Agent()


    """

    def __init__(self, scraper=None, parser=None, cache_name="espn-agent"):
        """
        Creates Agent object

        Args:
            scraper(espn.Scraper): default None
            parser(espn.Parser): default None
            cache_name(str): default 'espn-agent'

        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        if scraper:
            self._s = scraper
        else:
            self._s = Scraper(cache_name=cache_name)
        if parser:
            self._p = parser
        else:
            self._p = Parser()

    def weekly_projections(self,
                           season_year,
                           week,
                           inactives=None,
                           get_distributions=True):
        """
        Gets weekly watson projections

        Args:
            season_year(int): e.g. 2019
            week(int): 1-17
            inactives(list): of str

        Returns:
            list: of dict

        """
        projections = []
        logging.info('getting projections for %s Week %s', season_year, week)
        players = {item['playerid']: item for item in
                   self._p.players(self._s.players(season_year))
                   if item['position'] != 'K' and item['full_name'] not in inactives}

        for player_id, player in players.items():
            plyr = player['full_name']
            pos = player['position']
            team = ID_TEAM_DICT.get(int(player['team']))
            logging.info('starting %s', plyr)
            content = self._s.weekly_projection(season_year, player_id)
            projection = self._p.weekly_projection(content, most_recent_only=True)[0]
            projection_wanted = ['simulation_projection', 'outside_projection',
                                 'score_projection', 'playerid', 'score_distribution']
            if not get_distributions:
                projection_wanted = projection_wanted[:-1]
            merged_projection = {k: v for k, v in projection.items()
                                 if k in projection_wanted}
            merged_projection['plyr'] = plyr
            merged_projection['pos'] = pos
            merged_projection['team'] = team
            projections.append(merged_projection)
        if isinstance(projections[0], list):
            return [item for sublist in projections for item in sublist]
        else:
            return projections


if __name__ == "__main__":
    #pass
    import json
    logging.basicConfig(level=logging.INFO)
    a = Agent()

    inactives = ['AJ Green', 'Alec Ingold', 'Alex Armah', 'Alex Ellis', 'Alex McGough',
                'Alex Tanney', 'Andre Patton', 'Andrew Beck', 'Beau Brinkley',
                'Ben Roethlisberger', 'CJ Board', 'Cedrick Wilson', 'Cethan Carter',
                'Chris Hogan', 'Chris Manhertz', 'Clark Harris',
                'Cullen Gillaspia', 'Damion Willis', 'Danny Vitale',
                'David Fluellen', 'Davion Davis', 'Deonte Harris',
                'Derrius Guice', 'Devlin Hodges', 'Diontae Spencer', 'Dontrelle Inman',
                'Drew Brees', 'Easton Stick', 'Evan Baylis', 'Fred Brown',
                'Garrett Dickerson', 'Gunner Olszewski', 'Hunter Henry',
                'Isaiah Crowell', 'JP Holtz', 'Jaeden Graham', 'Jake Dolegala',
                'Jakob Johnson', 'Jalin Marshall', 'Jamaal Williams', 'James Develin',
                'Jerell Adams', 'Jerome Cunningham', 'John Ross', 'Jordan Reed',
                'Josh Dobbs', 'Josh Oliver', 'Justin Jackson', 'Kaden Smith',
                'LilJordan Humphrey', 'Matt Orzech', 'Matthew Slater',
                'NKeal Harry', 'Nick Foles', 'Olamide Zaccheaus',
                'Patrick Scales', 'Reggie Bonnafon', 'Robert Davis',
                'Roc Thomas', 'Scotty Miller', 'Sean Culkin', 'Steven Sims',
                'TJ Jones', 'Tanner Hudson', 'Trace McSorley', 'Tyler Kroft', 'Vyncint Smith']
    projections = a.weekly_projections(2019, 8, inactives=inactives)
    with open('/home/sansbacon/watson-w8.json', 'w') as f:
        json.dump(projections, f)
