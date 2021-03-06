# pfr.py
# classes to scrape and parse pro-football-reference.com

import copy
import json
import logging
import re
from pathlib import Path
from string import ascii_uppercase

from bs4 import BeautifulSoup
from sportscraper.scraper import RequestScraper


class Scraper(RequestScraper):
    @property
    def pgl_finder_url(self):
        """
        Base URL for player gamelog finder

        Returns:
            str

        """
        return "https://www.pro-football-reference.com/play-index/pgl_finder.cgi?"

    @property
    def tgl_finder_url(self):
        """
        Base URL for team gamelog finder

        Returns:
            str

        """
        return "https://www.pro-football-reference.com/play-index/tgl_finder.cgi?"

    @property
    def pgl_params(self):
        """
        Basic parameters for player gamelog finder

        Args:
            None

        Returns:
            dict

        """
        return {
            "c1comp": "gt",
            "c1stat": "targets",
            "c1val": "0",
            "c2comp": "gt",
            "c2stat": "draftkings_points",
            "c2val": "0",
            "c5val": "1.0",
            "career_game_num_max": "400",
            "career_game_num_min": "1",
            "game_num_max": "99",
            "game_num_min": "0",
            "game_type": "R",
            "match": "game",
            "opp_id": "",
            "order_by": "game_date",
            "order_by_asc": "Y",
            "pos[]": "",
            "request": "1",
            "season_end": "-1",
            "season_start": "1",
            "week_num_max": "99",
            "week_num_min": "0",
            "year_max": "2018",
            "year_min": "2018",
        }

    @property
    def params(self):
        """
        Basic parameters for search

        Returns:
            dict

        """
        return {
            "request": 1,
            "match": "game",
            "year_min": 2018,
            "year_max": 2018,
            "season_start": 1,
            "season_end": -1,
            "age_min": 0,
            "age_max": 0,
            "pos": "",
            "game_type": "R",
            "career_game_num_min": 0,
            "career_game_num_max": 499,
            "game_num_min": 0,
            "game_num_max": 99,
            "week_num_min": 1,
            "week_num_max": 20,
            "c1stat": "fantasy_points",
            "c1comp": "gt",
            "c1val": -5,
            "c5val": 1.0,
            "c2stat": -1,
            "c2stat": "targets",
            "c2comp": "gt",
            "c3stat": "choose",
            "c3comp": "gt",
            "c4stat": "choose",
            "c4comp": "gt",
            "c5comp": "choose",
            "c5gtlt": "lt",
            "c6mult": 1.0,
            "c6comp": "choose",
            "offset": 0,
            "order_by": "game_date",
            "order_by_asc": "Y",
        }

    def _merge_params(self, params):
        """
        Creates merged set of params, where params overwrites defaults

        Args:
            params: dict

        Returns:
            dict

        """
        context = self.params.copy()
        context.update(params)
        return context

    def draft(self, season_year):
        """
        Gets entire draft page for single season

        Args:
            season_year: int 2016, 2017, etc.

        Returns:
            content(str): of that year's draft page
        """
        url = f"http://www.pro-football-reference.com/years/{season_year}/draft.htm"
        return self.get(url)

    def player_game_finder(self, params):
        """
        Gets matching player games

        Args:
            params(dict):

        Returns:
            str

        """
        return self.get(self.pgl_finder_url, params=self._merge_params(params))

    def player_gamelogs(self,
                        source_player_name,
                        source_player_id,
                        year_min,
                        year_max
                        ):
        """
        Gets fantasy gamelog for individual player

        """
        extra_params = {
            'request': '1',
            'match': 'game',
            'player_id_hint': source_player_name,
            'player_id_select': source_player_name,
            'player_id': source_player_id,
            'idx': 'players',
            'year_min': year_min,
            'year_max': year_max,
            'season_start': '1',
            'season_end': '-1',
            'pos[]': ['QB', 'WR', 'RB', 'TE', 'OL', 'DL', 'LB', 'DB'],
            'c1stat': 'draftkings_points',
            'c1comp': 'gt',
            'c1val': '0',
            'c2stat': 'targets',
            'c2comp': 'gt',
            'c2val': '0',
            'c5val': '1.0',
            'order_by': 'game_date',
            'order_by_asc': 'Y'
        }
        return self.get(self.pgl_finder_url, params=self._merge_params(extra_params))

    def playerstats_fantasy_weekly(self, season_year, week, pos=None, offset=0):
        """
        Gets 100 rows of fantasy results for specific season and week

        Args:
            season_year: 2016, 2015, etc.
            week: 1, 2, 3, etc.
            pos: 'qb', 'wr', etc.
            offset: 0, 100, 200, etc.

        Returns:
            str
        """
        extra_params = {
            "year_min": season_year,
            "year_max": season_year,
            "offset": offset,
            "week_num_min": week,
            "week_num_max": week,
        }
        if pos:
            extra_params["pos"] = pos
        params = self._merge_params(extra_params)
        return self.get(self.pgl_finder_url, params=params)

    def playerstats_fantasy_yearly(self, season_year, pos=None, offset=0):
        """
        Gets 100 rows of fantasy results for specific season

        Args:
            season_year: 2016, 2015, etc.
            pos: 'qb', 'wr', etc.
            offset: 0, 100, 200, etc.

        Returns:
            str
        """
        extra_params = {
            "year_min": season_year,
            "year_max": season_year,
            "offset": offset,
        }
        if pos:
            extra_params["pos"] = pos
        params = self._merge_params(extra_params)
        return self.get(self.pgl_finder_url, params=params)

    def player_fantasy_season(self, season_year, player_id):
        """
        Gets fantasy page for individual player

        Args:
            player_id:

        Returns:
            str
        """
        # https://www.pro-football-reference.com/players/{R}/{RyanMa00}/fantasy/{2016}
        first_letter = player_id[0]
        url = (
            f"https://www.pro-football-reference.com/players/"
            f"{first_letter}/{player_id}/fantasy/{season_year}"
        )
        return self.get(url)

    def playerstats_offense_weekly(self, season_year, week, pos="0", offset=0):
        """
        Gets 100 rows of offense results for specific season and week

        Args:
            season_year (int): 2016, 2015, etc.
            week (int): 1, 2, 3, etc.
            pos (str): '0' (for all) or 'QB', etc.
            offset (int): 0, 100, 200, etc.

        Returns:
            str

        """
        extra_params = {
            "year_min": season_year,
            "year_max": season_year,
            "offset": offset,
            "match": "game",
            "pos": pos,
            "c2stat": "targets",
            "c2comp": "gt",
            "c2val": "-1",
        }
        if week > 0:
            extra_params["week_num_min"] = week
            extra_params["week_num_max"] = week
        params = self._merge_params(extra_params)
        return self.get(self.pgl_finder_url, params=params)

    def playerstats_offense_yearly(self, season_year, pos="0", offset=0):
        """
        Gets 100 rows of offense results for specific season

        Args:
            season_year (int): 2016, 2015, etc.
            pos (str): '0' or 'QB', etc.
            offset (int): 0, 100, 200, etc.

        Returns:
            str: HTML page

        """
        extra_params = {
            "year_min": season_year,
            "year_max": season_year,
            "offset": offset,
            "match": "game",
            "pos": pos,
            "c2stat": "targets",
            "c2comp": "gt",
            "c2val": "-1",
        }
        params = self._merge_params(extra_params)
        return self.get(self.pgl_finder_url, params=params)

    def playerstats_passing_weekly(self, season_year, week, offset=0):
        """
        Gets 100 rows of offense results for specific season and week

        Args:
            season_year: 2016, 2015, etc.
            week: 1, 2, 3, etc.
            offset: 0, 100, 200, etc.

        Returns:
            str

        """
        extra_params = {
            "year_min": season_year,
            "year_max": season_year,
            "offset": offset,
            "match": "game",
            "c1stat": "pass_att",
            "c1val": "1",
            "c2stat": "targets",
            "c2comp": "gt",
            "c2val": "-1",
        }
        if week > 0:
            extra_params["week_num_min"] = week
            extra_params["week_num_max"] = week
        params = self._merge_params(extra_params)
        return self.get(self.pgl_finder_url, params=params)

    def playerstats_passing_yearly(self, season_year, offset=0):
        """
        Gets passing results for specific season

        Args:
            season_year: 2016, 2015, etc.

        Returns:
            str

        """
        url = (
            f"https://www.pro-football-reference.com/years/"
            f"{season_year}/passing.htm"
        )
        return self.get(url)

    def playerstats_receiving_weekly(self, season_year, week, offset=0):
        """
        Gets 100 rows of receiving results for specific season and week

        Args:
            season_year: 2016, 2015, etc.
            week: 1, 2, 3, etc.
            offset: 0, 100, 200, etc.

        Returns:
            str
        """
        extra_params = {
            "year_min": season_year,
            "year_max": season_year,
            "offset": offset,
            "match": "game",
            "c2stat": "targets",
            "c2comp": "gt",
            "c2val": "-1",
        }
        if week > 0:
            extra_params["week_num_min"] = week
            extra_params["week_num_max"] = week
        params = self._merge_params(extra_params)
        return self.get(self.pgl_finder_url, params=params)

    def playerstats_receiving_yearly(self, season_year, offset=0):
        """
        Gets rushing/receiving results for specific season

        Args:
            season_year: 2016, 2015, etc.

        Returns:
            str
        """
        url = (
            f"https://www.pro-football-reference.com/years/"
            f"{season_year}/receiving.htm"
        )
        return self.get(url)

    def playerstats_rushing_weekly(self, season_year, week, offset=0):
        """
        Gets 100 rows of offense results for specific season and week

        Args:
            season_year: 2016, 2015, etc.
            week: 1, 2, 3, etc.
            offset: 0, 100, 200, etc.

        Returns:
            str
        """
        extra_params = {
            "year_min": season_year,
            "year_max": season_year,
            "offset": offset,
            "match": "game",
            "c1stat": "rush_att",
            "c1val": "1",
        }
        if week > 0:
            extra_params["week_num_min"] = week
            extra_params["week_num_max"] = week
        params = self._merge_params(extra_params)
        return self.get(self.pgl_finder_url, params=params)

    def playerstats_rushing_yearly(self, season_year, offset=0):
        """
        Gets rushing/receiving results for specific season

        Args:
            season_year: 2016, 2015, etc.

        Returns:
            str
        """
        url = (
            f"https://www.pro-football-reference.com/years/"
            f"{season_year}/rushing.htm"
        )
        return self.get(url)

    def players(self, last_initial):
        """
        Gets player page for last initial, such as A, B, C

        Args:
            last_initial(str): A, B, C

        Returns:
            str
        """
        last_initial = last_initial.upper()
        url = f"https://www.pro-football-reference.com/players/{last_initial}/"
        return self.get(url)

    def team_plays_query(self, season_start, season_end, offset):
        """
        Gets game-by-game play counts for teams

        Args:
            season_start: int 2016, 2017, etc.
            season_end: int 2016, 2017, etc.
            offset: int 0, 100, 200, etc.

        Returns:
            content(str): of 100 entries
        """
        extra_params = {
            "request": "1",
            "match": "game",
            "year_min": "2009",
            "year_max": "2016",
            "game_type": "R",
            "game_num_min": "0",
            "game_num_max": "99",
            "week_num_min": "0",
            "week_num_max": "99",
            "temperature_gtlt": "lt",
            "c1stat": "plays_offense",
            "c1comp": "gt",
            "c1val": "0",
            "c5val": "1.0",
            "order_by": "game_date",
            "order_by_asc": "Y",
        }
        return self.get(self.tgl_finder_url, params=extra_params)

    def team_passing_weekly(self, season_start, season_end, week):
        """
        Gets game-by-game passing stats for teams

        Args:
            season_start: int 2016, 2017, etc.
            season_end: int 2016, 2017, etc.
            week: int 1, 2, etc.

        Returns:
            content(str):
        """
        extra_params = {
            "request": "1",
            "match": "game",
            "year_min": season_start,
            "year_max": season_end,
            "game_type": "R",
            "game_num_min": "0",
            "game_num_max": "99",
            "week_num_min": week,
            "week_num_max": week,
            "temperature_gtlt": "lt",
            "c1stat": "pass_cmp",
            "c1comp": "gt",
            "c1val": "0",
            "c5val": "1.0",
            "order_by": "pass_td",
        }
        return self.get(self.tgl_finder_url, params=extra_params)

    def team_defense_yearly(self, season_year):
        """
        Gets total team defense stats for specific season_year

        Args:
            season_year: 2016, etc.

        Returns:
            list of dict
        """
        url = f"https://www.pro-football-reference.com/years/{season_year}/opp.htm"
        return self.get(url)

    def team_defense_weekly(self, season_start, season_end, week):
        """
        Gets game-by-game defense stats for teams

        Args:
            season_start: int 2016, 2017, etc.
            season_end: int 2016, 2017, etc.
            week: int 1, 2, etc.

        Returns:
            content(str):
        """
        extra_params = {
            "request": "1",
            "match": "game",
            "year_min": season_start,
            "year_max": season_end,
            "game_type": "R",
            "game_num_min": "0",
            "game_num_max": "99",
            "week_num_min": week,
            "week_num_max": week,
            "temperature_gtlt": "lt",
            "c1stat": "plays_defense",
            "c1comp": "gt",
            "c1val": "0",
            "c2stat": "pass_cmp_opp",
            "c2comp": "gt",
            "c2val": "0",
            "c3stat": "rush_att_opp",
            "c3comp": "gt",
            "c3val": "0",
            "c4stat": "pass_sacked_opp",
            "c4comp": "gt",
            "c4val": "0",
            "c5val": "1.0",
            "order_by": "game_date",
            "order_by_asc": "Y",
        }
        return self.get(self.tgl_finder_url, params=extra_params)

    def team_offense_yearly(self, season_year):
        """
        Gets total team offense stats for specific season_year

        Args:
            season_year: 2016, etc.

        Returns:
            response

        """
        url = f"https://www.pro-football-reference.com/years/{season_year}"
        return self.get(url, return_object=True)

    def team_offense_weekly(self, season_start, season_end, week):
        """
        Gets game-by-game offense stats for teams

        Args:
            season_start: int 2016, 2017, etc.
            season_end: int 2016, 2017, etc.
            week: int 1, 2, etc.

        Returns:
            content(str):
        """
        extra_params = {
            "request": "1",
            "match": "game",
            "year_min": season_start,
            "year_max": season_end,
            "game_type": "R",
            "game_num_min": "0",
            "game_num_max": "99",
            "week_num_min": week,
            "week_num_max": week,
            "temperature_gtlt": "lt",
            "c1stat": "rush_att",
            "c1comp": "gt",
            "c1val": "0",
            "c5val": "1.0",
            "order_by": "pass_td",
        }
        return self.get(self.tgl_finder_url, params=extra_params)

    def team_fantasy_weekly(self, team_id, week, year):
        """
        Gets one week of fantasy gamelogs for single team

        Args:
            team_id(str):
            week(int):
            year(int):

        Returns:
            str

        """
        extra_params = {
            "c1comp": "gt",
            "c1stat": "fantasy_points",
            "c1val": "-5",
            "c2comp": "gt",
            "c2stat": "targets",
            "c2val": "0",
            "c5val": "1.0",
            "career_game_num_max": "400",
            "career_game_num_min": "1",
            "game_num_max": "99",
            "game_num_min": "0",
            "game_type": "R",
            "match": "game",
            "order_by": "game_date",
            "order_by_asc": "Y",
            "pos": "0",
            "request": "1",
            "season_end": "-1",
            "season_start": "1",
            "team_id": team_id,
            "week_num_max": week,
            "week_num_min": week,
            "year_max": year,
            "year_min": year,
        }
        return self.get(self.pgl_finder_url, params=extra_params)


class Parser(object):
    """
    """

    def __init__(self, **kwargs):
        """

        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def _merge_team_tables(self, offense, passing, rushing):
        """
        Takes 3 dictionaries (offense, passing, rushing), returns merged dictionary

        """
        teams = copy.deepcopy(offense)
        for t in offense:
            p = passing.get(t)
        for k, v in p.items():
            teams[t][k] = v
            r = rushing.get(t)
        for k, v in r.items():
            teams[t][k] = v
        return teams

    def draft(self, content, season_year):
        """
        Parses page of draft results for single season

        Args:
            content(str): of draft page
            season_year: int 2017, 2016, etc.

        Returns:
            players: list of dict

        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        t = soup.find("table", {"id": "drafts"})
        for tr in t.find_all("tr"):
            p = {"draft_year": season_year, "source": "pfr"}

            # removes header rows for each draft round
            if tr.has_attr("class") and "thead" in tr["class"]:
                continue
            else:
                th = tr.find("th")
                p[th["data-stat"]] = th.text
            tds = tr.find_all("td")
            if tds:
                p[tds[0]["data-stat"]] = tds[0].text
                p[tds[1]["data-stat"]] = tds[1].text
                p[tds[2]["data-stat"]] = tds[2].text
                p[tds[3]["data-stat"]] = tds[3].text
                p[tds[-2]["data-stat"]] = tds[-2].text
                try:
                    # <td class="left " data-append-csv="RamcRy00"
                    # data-stat="player" csk="Ramczyk,
                    # Ryan"><a href="/players/R/RamcRy00.htm">Ryan Ramczyk</a></td>
                    p[tds[2]["data-stat"]] = tds[2]["csk"]
                    p["source_player_id"] = tds[2]["data-append-csv"]
                except:
                    try:
                        # /players/C/CarrDa00.htm
                        a = tr.find("a", {"href": re.compile(r"/players/")})
                        pid = a["href"].split(".htm")[0].split("/")[-1]
                        p["source_player_id"] = pid
                    except:
                        pass
            if p.get("source_player_id"):
                players.append(p)
            else:
                logging.error("missing id: {}".format(p))

        return players

    def player_fantasy_season(self, content, season_year=None):
        """
        Parses player fantasy page for season

        Args:
            content(str):
            season_year: 2016, etc.

        Returns:
            list of dict
        """
        players = []
        soup = BeautifulSoup(content, "lxml")

        try:
            for tr in (
                soup.find("table", {"id": "player_fantasy"})
                .find("tbody")
                .find_all("tr")
            ):
                player = {td["data-stat"]: td.text for td in tr.find_all("td")}
                if season_year:
                    player["season_year"] = season_year
                players.append(player)
        except Exception as e:
            logging.exception(e)
        return players

    def player_game_finder(self, content):
        """
        Parses player game finder search results

        Args:
            content(str):

        Returns:
            list of dict

        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        for tr in soup.find("table", {"id": "results"}).find("tbody").find_all("tr"):
            tds = tr.find_all("td")
            if tds:
                player = {td["data-stat"]: td.text for td in tds}
                if tds[0].has_attr("data-append-csv"):
                    player["source_player_id"] = tds[0].attrs.get("data-append-csv")
            players.append(player)
        return players

    def player_page(self, content, pid):
        """
        Parses player page

        Args:
            content(str):

        Returns:
            dict: source, source_player_id, source_player_name,
                  source_player_position, source_player_dob
        """
        player = {"source": "pfr", "source_player_id": pid}
        soup = BeautifulSoup(content, "lxml")

        # source_player_name
        h1 = soup.find("h1", {"itemprop": "name"})
        if h1:
            player["source_player_name"] = h1.text

        # source_player_position
        try:
            meta = soup.find("meta", {"name": "Description"})
            metac = meta.attrs.get("content")
            player["source_player_position"] = metac.split(",")[0].split(": ")[-1]
        except:
            pass

        # college
        for p in soup.find_all("p"):
            if p.find("strong") and p.find("a", {"href": re.compile(r"/schools/")}):
                player["college"] = p.find("a").text

        # spans: height and weight and dob
        for sp in soup.find_all("span"):
            if sp.attrs.get("itemprop") == "height":
                try:
                    ft, inch = [float(v) for v in sp.string.split("-")][0:2]
                    player["height"] = 12.0 * ft + inch
                except Exception as e:
                    print(e)
            elif sp.attrs.get("itemprop") == "weight":
                try:
                    player["weight"] = float(sp.string.split("lb")[0])
                except Exception as e:
                    print(e)
            elif sp.attrs.get("itemprop") == "birthDate":
                player["source_player_dob"] = sp.attrs.get("data-birth")

        return player

    def players(self, content):
        """
        Parses page of players with same last initial (A, B, C, etc.)

        Args:
            content(str):

        Returns:
            list of dict

        """
        results = []
        soup = BeautifulSoup(content, "lxml")
        for p in soup.select("div#div_players p"):
            try:
                player = {"source": "pfr"}
                name, posyears = p.text.split("(")
                pos, years = posyears.split(")")
                player["source_player_name"] = name.strip()
                player["source_player_position"] = pos.strip()
                player["source_player_years"] = years.strip()
                a = p.find("a")
                if a:
                    id = a["href"].split("/")[-1].split(".htm")[0]
                    player["source_player_id"] = id.strip()
                results.append(player)
            except:
                pass

        return results

    def playerstats_fantasy_weekly(self, content, season_year=None, pos=None):
        """
        Takes HTML of 100 rows of weekly results, returns list of players
        Use next_page parameter to indicate whether another

        Args:
            content(str):

        Returns:
            (players: list of player dict, next_page: boolean)
        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        tbl = soup.find("table", {"id": "results"})
        if tbl:
            for tr in tbl.find("tbody").findAll("tr", class_=None):
                player = {td["data-stat"]: td.text for td in tr.find_all("td")}
                if pos:
                    player["source_player_position"] = pos
                if season_year:
                    player["season_year"] = season_year

                a = tr.find("a", {"href": re.compile(r"/players/")})
                if a:
                    try:
                        pid = a["href"].split("/")[-1].split(".htm")[0]
                        player["source_player_id"] = pid
                    except:
                        pass
                players.append(player)
        return players

    def playerstats_fantasy_yearly(self, content):
        """
        Takes HTML of rows of yearly results, returns list of players

        Args:
            content (str): HTML

        Returns:
            list: of player dict

        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        for tr in (
            soup.find("table", {"id": "fantasy"})
            .find("tbody")
            .findAll("tr", class_=None)
        ):
            player = {td["data-stat"]: td.text for td in tr.find_all("td")[1:]}
            a = tr.find("a", {"href": re.compile(r"/players/")})
            pid = a["href"].split("/")[-1].split(".htm")[0]
            player["source_player_id"] = pid
            player["source_player_name"] = a.text
            player["season_year"] = soup.find("h1").find("span").text
            players.append(player)
        return players

    def playerstats_offense_weekly(self, content):
        """
        Takes HTML of rows of weekly results, returns list of players

        Args:
            content (str): HTML

        Returns:
            list: of player dict

        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        for tr in (
            soup.find("table", {"id": "results"})
            .find("tbody")
            .findAll("tr", class_=None)
        ):
            player = {td["data-stat"]: td.text for td in tr.find_all("td")[1:]}
            a = tr.find("a", {"href": re.compile(r"/players/")})
            pid = a["href"].split("/")[-1].split(".htm")[0]
            player["source_player_id"] = pid
            player["source_player_name"] = a.text
            player["season_year"] = (
                soup.find("div", {"id": "form_description"})
                .text.split(", ")[1]
                .split()[1]
            )
            players.append(player)
        return players

    def playerstats_offense_yearly(self, content):
        """
        Takes HTML of rows of yearly results, returns list of players

        Args:
            content (str): HTML

        Returns:
            list: of player dict

        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        for tr in (
            soup.find("table", {"id": "results"})
            .find("tbody")
            .findAll("tr", class_=None)
        ):
            player = {td["data-stat"]: td.text for td in tr.find_all("td")[1:]}
            a = tr.find("a", {"href": re.compile(r"/players/")})
            pid = a["href"].split("/")[-1].split(".htm")[0]
            player["source_player_id"] = pid
            player["source_player_name"] = a.text
            player["season_year"] = (
                soup.find("div", {"id": "form_description"})
                .text.split(", ")[1]
                .split()[1]
            )
            players.append(player)
        return players

    def playerstats_passing_yearly(self, content):
        """
        Takes HTML of rows of yearly results, returns list of players

        Args:
            content (str): HTML

        Returns:
            list: of player dict

        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        for tr in (
            soup.find("table", {"id": "passing"})
            .find("tbody")
            .findAll("tr", class_=None)
        ):
            player = {td["data-stat"]: td.text for td in tr.find_all("td")[1:]}
            a = tr.find("a", {"href": re.compile(r"/players/")})
            pid = a["href"].split("/")[-1].split(".htm")[0]
            player["source_player_id"] = pid
            player["source_player_name"] = a.text
            player["season_year"] = soup.find("h1").text.split()[0]
            players.append(player)
        return players

    def playerstats_receiving_yearly(self, content):
        """
        Takes HTML of rows of yearly results, returns list of players

        Args:
            content (str): HTML

        Returns:
            list: of player dict

        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        for tr in (
            soup.find("table", {"id": "receiving"})
            .find("tbody")
            .findAll("tr", class_=None)
        ):
            player = {td["data-stat"]: td.text for td in tr.find_all("td")[1:]}
            a = tr.find("a", {"href": re.compile(r"/players/")})
            pid = a["href"].split("/")[-1].split(".htm")[0]
            player["source_player_id"] = pid
            player["source_player_name"] = a.text
            player["season_year"] = soup.find("h1").text.split()[0]
            players.append(player)
        return players

    def playerstats_rushing_yearly(self, content):
        """
        Takes HTML of rows of yearly results, returns list of players

        Args:
            content (str): HTML

        Returns:
            list: of player dict

        """
        players = []
        soup = BeautifulSoup(content, "lxml")
        for tr in (
            soup.find("table", {"id": "rushing"})
            .find("tbody")
            .findAll("tr", class_=None)
        ):
            player = {td["data-stat"]: td.text for td in tr.find_all("td")[1:]}
            a = tr.find("a", {"href": re.compile(r"/players/")})
            pid = a["href"].split("/")[-1].split(".htm")[0]
            player["source_player_id"] = pid
            player["source_player_name"] = a.text
            player["season_year"] = soup.find("h1").text.split()[0]
            players.append(player)
        return players

    def team_plays(self, content):
        """
        Takes HTML of 100 rows of team plays, returns list of team_plays

        Args:
            content(str):

        Returns:
            teams: list of team dict
        """
        teams = []
        headers = [
            "team",
            "season_year",
            "game_date",
            "opp_team",
            "week",
            "game_number",
            "is_win",
            "is_ot",
            "off_plays",
            "def_plays",
            "top",
        ]

        soup = BeautifulSoup(content, "lxml")
        tbl = soup.find("table", {"id": "results"})
        if tbl:
            for tr in tbl.find("tbody").findAll("tr", class_=None):
                teams.append({td["data-stat"]: td.text for td in tr.find_all("td")})

        else:
            for tbl in soup.find_all("table"):
                logging.info(tbl.attrs)

        return teams

    def team_defense_weekly(self, content):
        """
        Team defense stats for single week

        Args:
            content(str):

        Returns:
            teams: list of dict
        """
        teams = []
        soup = BeautifulSoup(content, "lxml")
        defense = soup.find("table", {"id": "results"}).find("tbody")
        for tr in defense.findAll("tr"):
            teams.append({td["data-stat"]: td.text for td in tr.find_all("td")})
        return teams

    def team_defense_yearly(self, content, season_year=None):
        """
        Team defense stats for total season

        Args:
            content(str):

        Returns:
            teams: list of dict
        """
        teams = []
        soup = BeautifulSoup(content, "lxml")
        defense = soup.find("table", {"id": "team_stats"}).find("tbody")
        for tr in defense.findAll("tr"):
            team = {td["data-stat"]: td.text for td in tr.find_all("td")}
            if season_year:
                team["season_year"] = season_year
            teams.append(team)
        return teams

    def team_offense_weekly(self, content):
        """

        Args:
            content(str):

        Returns:
            teams: list of dict
        """
        teams = []
        soup = BeautifulSoup(content, "lxml")
        offense = soup.find("table", {"id": "results"}).find("tbody")
        for tr in offense.findAll("tr"):
            teams.append({td["data-stat"]: td.text for td in tr.find_all("td")})
        return teams

    def team_offense_yearly(self, response):
        """
        Team offense stats for total season

        Args:
            response

        Returns:
            list of dict

        """
        teams = []
        response.html.render()
        off = response.html.find("#team_stats", first=True)
        season_year = response.html.find("h1", first=True).text.split()[0]
        for tr in off.find("tr"):
            team = {td.attrs.get("data-stat"): td.text for td in tr.find("td")}
            team["source"] = "pfr"
            if not team.get("team"):
                continue
            elif team.get("team") in ["Avg Team", "League Total", "Avg Tm/G"]:
                continue
            else:
                team["source_team_code"] = team.pop("team")
            team["season_year"] = season_year
            teams.append(team)
        return teams

    def team_fantasy_weekly(self, content):
        """
        Takes HTML of team weekly results, returns list of players

        Args:
            content(str):

        Returns:
            list: of dict

        """
        players = []

        soup = BeautifulSoup(content, "lxml")
        tbl = soup.find("table", {"id": "results_clone"})
        if tbl:
            for tr in tbl.find("tbody").findAll("tr", class_=None):
                player = {td["data-stat"]: td.text for td in tr.find_all("td")}
                a = tr.find("a", {"href": re.compile(r"/players/")})
                if a:
                    try:
                        pid = a["href"].split("/")[-1].split(".htm")[0]
                        player["source_player_id"] = pid
                    except:
                        pass
                players.append(player)

        return players

    def team_season(self, content, season):
        """
        Takes HTML file of team stats during single season
        Returns dict, key is team_season, value is team
        """

        soup = BeautifulSoup(content, "lxml")
        teams = {}

        offense = soup.find("table", {"id": "team_stats"}).find("tbody")
        for tr in offense.findAll("tr"):
            team = {"season": season}

            for td in tr.findAll("td"):
                val = td.text

                # fix team name - has newline and extra space
                if "\n" in val:
                    val = " ".join(val.split("\n"))
                    val = " ".join(val.split())

                # column headers on page are duplicates (yds, td, etc.)
                # data-stat attribute has accurate column name (rush_yds)
                team[td["data-stat"]] = val

            k = team["team"] + "_" + season
            teams[k] = team
        return teams


class Agent(object):
    def __init__(self, scraper=None, parser=None):
        """

        Args:
            scraper: PfrScraper object
            parser: PfrParser object
            cache_name(str):
            cj: cookiejar object
        """

        logging.getLogger(__name__).addHandler(logging.NullHandler())

        if scraper:
            self._s = scraper
        else:
            self._s = Scraper(cache_name="pfr", delay=1.5)

        if parser:
            self._p = parser
        else:
            self._p = Parser()

    def players(self, savefile=None):
        """
        Gets all of the players from pfr

        Returns:
            list of dict
        """
        results = []

        for letter in ascii_uppercase:
            content = self._s.players(letter)
            results += self._p.players(content)
            logging.info("completed players {}".format(letter))

        if savefile:
            with open(savefile, "w") as outfile:
                json.dump(results, outfile)
            logging.info("wrote results to {}".format(savefile))

        return results

    def playerstats_offense_yearly(self):
        """
        TODO: fully implement this
        Returns:

        """
        # import json
        # from pathlib import Path
        # from nfl.scrapers.pfr import PfrNFLScraper
        # from nfl.parsers.pfr import PfrNFLParser

        pfrs = Scraper(cache_name="pfrscraper")
        pfrp = Parser()

        results = []
        for offset in range(0, 700, 100):
            content = pfrs.playerstats_offense_yearly(2017, offset)
            results += pfrp.playerstats_offense_yearly(content)
            print("finished offset {}".format(offset))

        pth = Path.home() / "playerstats_offense_yearly_2017.json"
        with pth.open("w") as f:
            json.dump(results, f)


if __name__ == "__main__":
    # pass
    s = Scraper(cache_name="pfr")
    p = Parser()
    content = s.team_offense_yearly(season_year=2008)
    # with open('/home/sansbacon/to.htm', 'w') as f:
    #    f.write(content)
    print(p.team_offense_yearly(content, 2008))
