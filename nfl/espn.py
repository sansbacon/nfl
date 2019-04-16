# -*- coding: utf-8 -*-

"""
# espn.py
# classes for scraping, parsing espn football data
"""


import logging
import re

from bs4 import BeautifulSoup, NavigableString, Tag
from sportscraper.scraper import RequestScraper


class Scraper(RequestScraper):
    """
    Scrape ESPN.com for football stats

    """

    @property
    def fantasy_team_codes(self):
        """
        Fantasy team codes

        Returns:
            int

        """
        return [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            33,
            34,
        ]

    @property
    def fantasy_teams(self):
        """
        Fantasy team codes and names

        Returns:
            dict

        """
        return {
            1: "Atl",
            2: "Buf",
            3: "Chi",
            4: "Cin",
            5: "Cle",
            6: "Dal",
            7: "Den",
            8: "Det",
            9: "GB",
            10: "Ten",
            11: "Ind",
            12: "KC",
            13: "Oak",
            14: "LAR",
            15: "Mia",
            16: "Min",
            17: "NE",
            18: "NO",
            19: "NYG",
            20: "NYJ",
            21: "Phi",
            22: "Ari",
            23: "Pit",
            24: "LAC",
            25: "SF",
            26: "Sea",
            27: "TB",
            28: "Wsh",
            29: "Car",
            30: "Jax",
            33: "Bal",
            34: "Hou",
        }

    @staticmethod
    def _check_pos(pos):
        """
        Makes sure pos is valid and uppercase

        Args:
            pos(str):

        Returns:
            str

        """
        if pos in [
            "qb",
            "rb",
            "wr",
            "te",
            "dst",
            "d/st",
            "k",
            "QB",
            "RB",
            "WR",
            "TE",
            "K",
            "D/ST",
            "DST",
        ]:
            if pos in ["DST", "dst"]:
                fixed = "D/ST"
            else:
                fixed = pos.upper()
        else:
            raise ValueError("invalid position: {}".format(pos))
        return fixed

    def adp(self, season_year):
        """
        Gets adp data

        Args:
            season_year(int): 2019, etc.

        Returns:
            dict: parsed JSON

        """
        url = (
            f"http://fantasy.espn.com/apis/v3/games/ffl/seasons/{season_year}/"
            f"segments/0/leaguedefaults/1?view=kona_player_info"
        )
        return self.get_json(url)

    def fantasy_players_team(self, team_id):
        """
        Gets page with fantasy players by team

        Args:
            team_id(int): 1, 2, etc.

        Returns:
            str: HTML

        """
        url = "http://games.espn.com/ffl/tools/projections?proTeamId={}"
        return self.get(url.format(team_id), encoding="latin1")

    def players_position(self, pos):
        """
        Gets page with all players by position

        Args:
            pos(str): qb, rb, wr, te, k, etc.

        Returns:
            str

        """
        url = "http://www.espn.com/nfl/players?position={}&league=nfl"
        return self.get(url.format(pos), encoding="latin1")

    def projections(self, pos, season_year=None, week=0, offset=0):
        """
        Gets page with projections by position

        Args:
            pos: str qb, rb, wr, te, k, etc.
            season_year: int 2017, 2016
            week: int 1, 2, 3
            offset: int 0, 40, 80, etc.

        Returns:
            HTML string
        """
        pos = pos.lower()
        slot_categories = {"qb": 0, "rb": 2, "wr": 4, "te": 6, "dst": 16, "k": 17}
        max_offset = {"qb": 120, "rb": 240, "wr": 360, "te": 160, "dst": 0, "k": 40}

        if pos not in slot_categories.keys():
            raise ValueError("invalid pos {}".format(pos))
        elif offset > max_offset.get(pos):
            raise ValueError("invalid offset {}".format(offset))
        elif offset % 40 > 0:
            raise ValueError("invalid offset {}".format(offset))

        url = "http://games.espn.com/ffl/tools/projections?"
        if season_year:
            params = {
                "slotCategoryId": slot_categories[pos],
                "startIndex": offset,
                "seasonId": season_year,
            }
        else:
            params = {"slotCategoryId": slot_categories[pos], "startIndex": offset}

        if week:
            params["scoringPeriodId"] = week
        else:
            params["seasonTotals"] = "true"

        return self.get(url, params=params, encoding="latin1")

    def team_roster(self, team_code):
        """
        Gets list of NFL players from ESPN.com

        Args:
            team_code: str 'DEN', 'BUF', etc.

        Returns:
            HTML string
        """
        url = f"http://www.espn.com/nfl/team/roster/_/name/{team_code}"
        return self.get(url, encoding="latin1")

    def weekly_scoring(self, season_year, week, position):
        """
        Gets weekly fantasy scoring page

        Args:
            season_year (int): 2017, 2016, etc.
            week (int): 1 through 17
            position (str): 'qb', 'wr', etc.

        Returns:
            str: HTML

        TODO: does not work out of season?
        """
        poscode = {"qb": 0, "rb": 2, "wr": 4, "te": 6, "dst": 16, "k": 17}
        if position.lower() not in poscode:
            raise ValueError("invalid position: {}".format(position))
        url = "http://games.espn.com/ffl/leaders?&"
        params = {
            "scoringPeriodId": week,
            "seasonId": season_year,
            "slotCategoryId": position,
        }
        return self.get(url, payload=params)


class Parser:
    """
    Parse ESPN.com for football stats

    """

    def __init__(self):
        """
        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    @property
    def fantasy_team_codes(self):
        """
        Fantasy team codes

        Returns:
            int

        """
        return [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            33,
            34,
        ]

    @property
    def fantasy_teams(self):
        """
        Fantasy team codes to names

        Returns:
            dict

        """
        return {
            1: "Atl",
            2: "Buf",
            3: "Chi",
            4: "Cin",
            5: "Cle",
            6: "Dal",
            7: "Den",
            8: "Det",
            9: "GB",
            10: "Ten",
            11: "Ind",
            12: "KC",
            13: "Oak",
            14: "LAR",
            15: "Mia",
            16: "Min",
            17: "NE",
            18: "NO",
            19: "NYG",
            20: "NYJ",
            21: "Phi",
            22: "Ari",
            23: "Pit",
            24: "LAC",
            25: "SF",
            26: "Sea",
            27: "TB",
            28: "Wsh",
            29: "Car",
            30: "Jax",
            33: "Bal",
            34: "Hou",
        }

    @staticmethod
    def _val(val):
        """
        Converts non-numeric value to numeric 0

        Args:
            val:

        Returns:
            number
        """
        if "--" in val:
            return 0
        return val

    @staticmethod
    def adp(content):
        """
        Parses season-long ADP

        Args:
            content:

        Returns:
            list of dict
        """
        vals = []
        for item in content["players"]:
            tl_wanted = [
                "defaultPositionId",
                "firstName",
                "id",
                "lastName",
                "proTeamId",
            ]
            api_player = {k: v for k, v in item["player"].items() if k in tl_wanted}
            for scoring_type in ["PPR", "STANDARD"]:
                for rank_type in ["rank", "auctionValue"]:
                    key = scoring_type.lower() + "_" + rank_type
                    try:
                        api_player[key] = item["player"]["draftRanksByRankType"][
                            scoring_type
                        ][rank_type]
                    except:
                        api_player[key] = None
            vals.append(api_player)
        return vals

    @staticmethod
    def fantasy_players_team(content):
        """
        Parses page of fantasy players

        Args:
            content: HTML string

        Returns:
            list of players
        """
        players = {}
        soup = BeautifulSoup(content, "lxml")
        for link in soup.find_all("a", {"class": "flexpop"}):
            pid = link.attrs.get("playerid")
            pname = link.text.strip()
            if pid and pname:
                players[pid] = pname
        return players

    @staticmethod
    def lovehate(season, week, lhdict):
        """

        Args:
            season(int):
            week(int):
            lhdict(dict): keys are position_love, position_hate

        Returns:
            list: of player dict

        """

        players = []
        if not season or week:
            raise ValueError("need season and week")

        for poslh, ratings in lhdict.items():
            pos = poslh.split("_")[0]
            label = ratings.get("label")
            sublabel = None

            if label in ("favorite", "bargain", "desparate"):
                sublabel = label
                label = "love"
                logging.info("%s", label)
            for link in ratings.get("links"):
                spid = {}
                url = link.split('"')[1]
                spid["site_player_id"], spid["site_player_stub"] = url.split("/")[7:9]
                spid["site_player_name"] = link.split(">")[1].split("<")[0]
                logging.info("%s %s %s", pos, sublabel, spid)
        return players

    def projections(self, content, pos):
        """
        Parses ESPN fantasy football season-long sortable projections page

        Args:
            content: HTML string

        Returns:
            list of dict
        """
        players = []
        soup = BeautifulSoup(content, "lxml")

        if pos.lower() in ["qb", "rb", "wr", "te", "flex"]:
            headers = [
                "pass_att",
                "pass_cmp",
                "pass_yds",
                "pass_td",
                "pass_int",
                "rush_att",
                "rush_yds",
                "rush_td",
                "rec",
                "rec_yds",
                "rec_td",
                "fantasy_points_ppr",
            ]

            for row in soup.findAll("tr", {"class": "pncPlayerRow"}):
                player = {"source": "espn"}

                tds = row.find_all("td")

                # tds[0]: rank
                player["source_position_rank"] = tds[0].text

                # tds[1]: name/team/pos
                link, navstr = list(tds[1].children)[0:2]
                player["source_player_name"] = link.text
                player["source_player_team"], player[
                    "source_player_position"
                ] = navstr.split()[-2:]
                player["source_player_id"] = link.attrs.get("playerid")

                # loop through stats
                # they have attempts/completions in one column so have to remove & split
                attcmp = tds[2].text
                vals = [self._val(td.text) for td in tds[3:]]
                for header, val in zip(headers, attcmp.split("/") + vals):
                    player[header] = val
                players.append(player)

        elif pos.lower() == "k":
            for row in soup.findAll("tr", {"class": "pncPlayerRow"}):
                player = {"source": "espn"}
                tds = row.find_all("td")

                # tds[0]: rank
                player["source_position_rank"] = tds[0].text

                # tds[1]: name/team/pos
                link, navstr = list(tds[1].children)[0:2]
                player["source_player_name"] = link.text
                player["source_player_team"], player[
                    "source_player_position"
                ] = navstr.split()[-2:]
                player["source_player_id"] = link.attrs.get("playerid")

                # loop through stats
                # they have attempts/completions in one column so have to remove & split
                player["fantasy_points_ppr"] = self._val(tds[-1].text)
                players.append(player)
        else:
            pass

        return players

    @staticmethod
    def players_position(content, pos):
        """
        Parses page of ESPN players by position

        Args:
            content:
            pos:

        Returns:
            list: of dict

        """
        players = []
        soup = BeautifulSoup(content, "lxml")

        for row in soup.find_all("tr"):
            class_matches = set(["oddrow", "evenrow"])
            classes = set(row.attrs.get("class", []))
            if class_matches.intersection(classes):
                player = {"source": "espn", "source_player_position": pos}
                tds = row.find_all("td")

                # tds[0]: <a href="http://www.espn.com/nfl/player/_/id/
                # 2574511/brandon-allen">Allen, Brandon</a>
                player["source_player_name"] = tds[0].text
                link = row.find("a", {"href": re.compile(r"/player/_/")})
                if link:
                    match = re.search(r"\/id\/([0-9]+)", link["href"])
                    if match:
                        player["source_player_id"] = match.group(1)

                # tds[1]: <td><a href="http://www.espn.com/nfl/team/_/
                # name/jax/jacksonville-jaguars">Jacksonville Jaguars</a></td>
                player["source_team_name"] = tds[1].text
                link = row.find("a", {"href": re.compile(r"/team/_/name")})
                if link:
                    match = re.search(r"name/(\w+)/", link["href"])
                    if match:
                        player["source_team_code"] = match.group(1)

                # tds[2]: <td>Arkansas</td>
                player["college"] = tds[2].text

                # add to list
                players.append(player)

        return players

    @staticmethod
    def team_roster(content):
        """
        Parses team roster page into list of player dict

        Args:
            content: HTML of espn nfl team roster page

        Returns:
            list of dict
        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        for row in soup.find_all("tr"):
            link = row.find("a", {"href": re.compile(r"/nfl/player/_/id/")})
            try:
                player = {"source": "espn"}
                tds = row.find_all("td")
                if len(tds) != 8:
                    continue
                player["source_player_position"] = tds[2].text
                player["source_player_name"] = link.text
                player["source_player_id"] = link["href"].split("/")[-2]
                players.append(player)
            except ValueError:
                pass
        return players

    @staticmethod
    def watson(content):
        """

        Args:
            content: list of dict - parsed JSON

        Returns:
            dict
        """
        wanted = [
            "PLAYERID",
            "EXECUTION_TIMESTAMP",
            "DISTRIBUTION_NAME",
            "SCORE_PROJECTION",
            "SCORE_DISTRIBUTION",
            "LOW_SCORE",
            "HIGH_SCORE",
            "OUTSIDE_PROJECTION",
            "SIMULATION_PROJECTION",
        ]

        # have multiple time-stamped projections
        # we want the most recent projection model only
        newest = content[-1]
        return {k.lower(): v for k, v in newest.items() if k in wanted}

    @staticmethod
    def watson_players(content, wanted=None):
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
    def weekly_scoring(content):
        """
        Parses weekly scoring page

        Args:
            content (str): HTML

        Returns:
            list: of dict

        """
        results = []
        headers = [
            "c_a",
            "pass_yds",
            "pass_td",
            "pass_int",
            "rush_att",
            "rush_yds",
            "rush_td",
            "rec_rec",
            "rec_yds",
            "rec_td",
            "rec_tar",
            "tpc",
            "fumble",
            "misc_td",
            "fpts",
        ]
        soup = BeautifulSoup(content, "lxml")
        tbl = soup.select("table#playertable_0")[0]
        for row in tbl.find_all("tr", {"id": re.compile(r"plyr")}):
            tds = [td.text for td in row.find_all("td", class_="playertableStat")]
            if tds:
                player = dict(zip(headers, tds))
                # name, team, position
                nametd = row.find("td", {"id": re.compile(r"playername")})
                for child in nametd.children:
                    if isinstance(child, NavigableString):
                        player["source_player_team"], player[
                            "source_player_position"
                        ] = child.string.split()[1:3]
                    elif isinstance(child, Tag):
                        player["source_player_name"] = child.string
                        player["source_player_id"] = child.attrs.get("playerid")
                results.append(player)
        return results

    @staticmethod
    def weekly_scoring_dst(content):
        """
        Parses weekly scoring page for dst

        Args:
            content(str): HTML

        Returns:
            list: of dict

        """
        # TODO: adapt for dst
        results = []
        headers = [
            "c_a",
            "pass_yds",
            "pass_td",
            "pass_int",
            "rush_att",
            "rush_yds",
            "rush_td",
            "rec_rec",
            "rec_yds",
            "rec_td",
            "rec_tar",
            "tpc",
            "fumble",
            "misc_td",
            "fpts",
        ]
        soup = BeautifulSoup(content, "lxml")
        tbl = soup.select("table#playertable_0")[0]
        for row in tbl.find_all("tr", {"id": re.compile(r"plyr")}):
            tds = [td.text for td in row.find_all("td", class_="playertableStat")]
            if tds:
                player = dict(zip(headers, tds))
                # name, team, position
                nametd = row.find("td", {"id": re.compile(r"playername")})
                for child in nametd.children:
                    if isinstance(child, NavigableString):
                        player["source_player_team"], player[
                            "source_player_position"
                        ] = child.string.split()[1:3]
                    elif isinstance(child, Tag):
                        player["source_player_name"] = child.string
                        player["source_player_id"] = child.attrs.get("playerid")
                results.append(player)
        return results

    @staticmethod
    def weekly_scoring_k(content):
        """
        Parses weekly scoring page for kickers

        Args:
            content (str): HTML

        Returns:
            list: of dict

        """
        # TODO: adapt for kicker
        results = []
        headers = [
            "c_a",
            "pass_yds",
            "pass_td",
            "pass_int",
            "rush_att",
            "rush_yds",
            "rush_td",
            "rec_rec",
            "rec_yds",
            "rec_td",
            "rec_tar",
            "tpc",
            "fumble",
            "misc_td",
            "fpts",
        ]
        soup = BeautifulSoup(content, "lxml")
        tbl = soup.select("table#playertable_0")[0]
        for row in tbl.find_all("tr", {"id": re.compile(r"plyr")}):
            tds = [td.text for td in row.find_all("td", class_="playertableStat")]
            if tds:
                player = dict(zip(headers, tds))
                # name, team, position
                nametd = row.find("td", {"id": re.compile(r"playername")})
                for child in nametd.children:
                    if isinstance(child, NavigableString):
                        player["source_player_team"], player[
                            "source_player_position"
                        ] = child.string.split()[1:3]
                    elif isinstance(child, Tag):
                        player["source_player_name"] = child.string
                        player["source_player_id"] = child.attrs.get("playerid")
                results.append(player)
        return results


if __name__ == "__main__":
    pass
