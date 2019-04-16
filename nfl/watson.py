# -*- coding: utf-8 -*-

"""
# watson.py
# classes for scraping, parsing watson football data
"""

import json
import logging

import pendulum
from sportscraper.scraper import RequestScraper


class Scraper(RequestScraper):
    """
    Scrape Watson football projections

    """

    def players(self, season_year):
        """
        Gets watson players

        Args:
            season_year(int): 2018, etc.

        Returns:
            list: of dict

        """
        plurl = (
            f"http://ibm-fantasy-widget.espn.com/espnpartner/dallas/players/"
            f"players_ESPNFantasyFootball_{season_year}.json"
        )
        return self.get_json(plurl)

    def weekly_projection(self, season_year, pid):
        """
        Gets Watson projections for a player

        Args:
            season_year(int): 2018, etc.
            pid(int): player ID (10000, etc.)

        Returns:
            dict - parsed JSON

        """
        url = (
            f"http://ibm-fantasy-widget.espn.com/espnpartner/dallas/projections/"
            f"projections_{pid}_ESPNFantasyFootball_{season_year}.json"
        )
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


if __name__ == "__main__":
    pass
