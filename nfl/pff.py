# -*- coding: utf-8 -*-
# pff.py
# classes to scrape and parse profootballfocus.com

import logging
import time

from nflmisc.browser import BrowserScraper


class Scraper(BrowserScraper):
    """
    This only works for subscribers. You may have to manually login in the browser before using the library.

    """

    def depth_charts(self, team_id):
        """
        Gets pff depth charts

        Args:
            team_id: int 1, 2, etc.

        Returns:
            dict

        """
        url = "https://grades.profootballfocus.com/api/offenses/depth_charts?team_id={}"
        _ = self.get("https://grades.profootballfocus.com/api/teams")
        time.sleep(0.5)
        return self.get_json(url.format(team_id))[0]

    def player_grades_career(self, player_id):
        """
        Gets pff grades for player each season

        Args:
            player_id: int

        Returns:
            dict

        """
        url = "https://grades.profootballfocus.com/api/players/{}/grades_by_season"
        _ = self.get("https://grades.profootballfocus.com/api/teams")
        time.sleep(0.5)
        return self.get_json(url.format(player_id))

    def player_grades_week(self, player_id):
        """
        Gets pff grades for player each season

        Args:
            player_id: int

        Returns:
            dict

        """
        url = "https://grades.profootballfocus.com/api/players/{}/grades_by_week"
        _ = self.get("https://grades.profootballfocus.com/api/teams")
        time.sleep(0.5)
        return self.get_json(url.format(player_id))

    def player_snaps_season(self, player_id):
        """
        Gets pff snap counts for most recent season

        Args:
            player_id: int

        Returns:
            dict

        """
        url = "https://grades.profootballfocus.com/api/players/{}/snaps_by_week"
        _ = self.get("https://grades.profootballfocus.com/api/teams")
        time.sleep(0.5)
        return self.get_json(url.format(player_id))

    def players(self, team_id):
        """
        Gets profootballfocus players for team

        Args:
            team_id: int 1, 2, etc.

        Returns:
            dict

        """
        return self.get_json(
            "https://grades.profootballfocus.com/api/players?team_id={}".format(team_id)
        )

    def position_grades(self, pos):
        """
        Gets pff grades

        Args:
            pos: 'QB', 'WR', 'TE', 'HB', etc.

        Returns:
            dict

        """
        # pff uses HB instead of rb
        if pos == "RB":
            pos == "HB"
        url = "https://grades.profootballfocus.com/api/players?position={}"
        _ = self.get("https://grades.profootballfocus.com/api/teams")
        time.sleep(0.5)
        return self.get_json(url.format(pos))

    def teams(self):
        """
        Gets profootballfocus teams

        Returns:
            dict

        """
        return self.get_json("https://grades.profootballfocus.com/api/teams")


class Parser(object):
    def __init__(self):
        """

        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def position_grades(self, content):
        """
        Parses season-ending grades for

        Args:
            content: dict with keys teams, rosters

        Returns:
            players

        """
        players = []
        keys = ["first_name", "last_name", "franchise_id", "gsis_id"]
        snap_exclude = ["player_id", "season", "week"]

        for item in content["rosters"]:
            player = {k: v for k, v in item.items() if k in keys}
            if item.get("grade", None):
                player.update(item["grade"])
            if item.get("snapCount", None):
                player.update(
                    {
                        k: v
                        for k, v in item["snapCount"].items()
                        if k not in snap_exclude
                    }
                )
            players.append(player)
        return players

    def depth_charts(self, content, exclude_positions=None):
        """
        Parses pff depth charts

        Args:
            content(dict): parsed JSON
            exclude_positions(iterable): positions to exclude

        Returns:
            list

        """
        players = []
        # positions = ('te', 'swr', 'rwr', 'rt', 'rg', 'qb', 'lwr'
        #             'lt', 'lg', 'hb', 'c')
        for k, v in content["positions"].items():
            players += v
        return players

    def player_grades_career(self, content):
        """
        Parses pff grades for player each season

        Args:
            content(list): parsed JSON

        Returns:
            list

        """
        return content

    def player_grades_week(self, content):
        """
        Parses pff grades for player each season

        Args:
            content(list): parsed JSON

        Returns:
            list

        """
        return content

    def player_snaps_season(self, content):
        """
        Parses pff snap counts for most recent season

        Args:
            content(list): parsed JSON

        Returns:
            list

        """
        return content

    def players(self, content):
        """
        Parses profootballfocus players for team

        Args:
            content(dict): parsed JSON

        Returns:
            list

        """
        pl = []
        team_id = content["teams"][0]["id"]
        team_abbrev = content["teams"][0]["abbreviation"]
        for p in content["rosters"]:
            p["source_team_id"] = team_id
            p["source_team_code"] = team_abbrev
            pl.append(p)
        return pl

    def teams(self, content):
        """
        Parses profootballfocus teams

        Args:
            content(dict): parsed JSON

        Returns:
            list

        """
        return content["teams"]


if __name__ == "__main__":
    pass
