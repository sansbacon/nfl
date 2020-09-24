# -*- coding: utf-8 -*-
"""

# nflcom.py
# scraper and parser classes for nfl.com website

"""
from datetime import datetime
import logging
import re
from string import ascii_uppercase

import demjson
from bs4 import BeautifulSoup, Comment
import pendulum

try:
    from .db import setup
except ImportError:
    pass
from namematcher.name import first_last_pair
from sportscraper.dates import convert_format, today
from sportscraper.scraper import RequestScraper
from sportscraper.utility import digits, merge_two, save_csv
from sqlalchemy import text


NFL_STAT_CODES = {
 1: {'abbr': 'GP', 'name': 'Games Played', 'shortName': 'GP'},
 2: {'abbr': 'Att', 'name': 'Passing Attempts', 'shortName': 'Pass Att'},
 3: {'abbr': 'Comp', 'name': 'Passing Completions', 'shortName': 'Pass Comp'},
 4: {'abbr': 'Inc', 'name': 'Incomplete Passes', 'shortName': 'Pass Inc'},
 5: {'abbr': 'Yds', 'name': 'Passing Yards', 'shortName': 'Pass Yds'},
 6: {'abbr': 'TD', 'name': 'Passing Touchdowns', 'shortName': 'Pass TD'},
 7: {'abbr': 'Int', 'name': 'Interceptions Thrown', 'shortName': 'Pass Int'},
 8: {'abbr': 'Sacked', 'name': 'Every Time Sacked', 'shortName': 'Sacked'},
 9: {'abbr': '300-399',
      'name': '300-399 Passing Yards Bonus',
      'shortName': '300-399 Pass Yds'},
 10: {'abbr': '400+',
        'name': '400+ Passing Yards Bonus',
  'shortName': '400+ Pass Yds'},
 11: {'abbr': '40+ TD',
  'name': '40+ Passing Yard TD Bonus',
  'shortName': '40+ Pass TD'},
 12: {'abbr': '50+ TD',
  'name': '50+ Passing Yards TD Bonus',
  'shortName': '50+ Pass TD'},
 13: {'abbr': 'Att', 'name': 'Rushing Attempts', 'shortName': 'Rush Att'},
 14: {'abbr': 'Yds', 'name': 'Rushing Yards', 'shortName': 'Rush Yds'},
 15: {'abbr': 'TD', 'name': 'Rushing Touchdowns', 'shortName': 'Rush TD'},
 16: {'abbr': '40+ TD',
  'name': '40+ Rushing Yard TD Bonus',
  'shortName': '40+ Rush TD'},
 17: {'abbr': '50+ TD',
  'name': '50+ Rushing Yard TD Bonus',
  'shortName': '50+ Rush TD'},
 18: {'abbr': '100-199',
  'name': '100-199 Rushing Yards Bonus',
  'shortName': '100-199 Rush Yds'},
 19: {'abbr': '200+',
  'name': '200+ Rushing Yards Bonus',
  'shortName': '200+ Rush Yds'},
 20: {'abbr': 'Rect', 'name': 'Receptions', 'shortName': 'Receptions'},
 21: {'abbr': 'Yds', 'name': 'Receiving Yards', 'shortName': 'Rec Yds'},
 22: {'abbr': 'TD', 'name': 'Receiving Touchdowns', 'shortName': 'Rec TD'},
 23: {'abbr': '40+ TD',
  'name': '40+ Receiving Yard TD Bonus',
  'shortName': '40+ Rec TD'},
 24: {'abbr': '50+ TD',
  'name': '50+ Receiving Yard TD Bonus',
  'shortName': '50+ Rec TD'},
 25: {'abbr': '100-199',
  'name': '100-199 Receiving Yards Bonus',
  'shortName': '100-199 Rec Yds'},
 26: {'abbr': '200+',
  'name': '200+ Receiving Yards Bonus',
  'shortName': '200+ Rec Yds'},
 27: {'abbr': 'Yds',
  'name': 'Kickoff and Punt Return Yards',
  'shortName': 'Return Yds'},
 28: {'abbr': 'TD',
  'name': 'Kickoff and Punt Return Touchdowns',
  'shortName': 'Return TD'},
 29: {'abbr': 'Fum TD',
  'name': 'Fumble Recovered for TD',
  'shortName': 'Fum TD'},
 30: {'abbr': 'Lost', 'name': 'Fumbles Lost', 'shortName': 'Fum Lost'},
 31: {'abbr': 'Fum', 'name': 'Fumble', 'shortName': 'Fum'},
 32: {'abbr': '2PT', 'name': '2-Point Conversions', 'shortName': '2PT'},
 33: {'abbr': 'Made', 'name': 'PAT Made', 'shortName': 'PAT Made'},
 34: {'abbr': 'Miss', 'name': 'PAT Missed', 'shortName': 'PAT Miss'},
 35: {'abbr': '0-19', 'name': 'FG Made 0-19', 'shortName': 'FG 0-19'},
 36: {'abbr': '20-29', 'name': 'FG Made 20-29', 'shortName': 'FG 20-29'},
 37: {'abbr': '30-39', 'name': 'FG Made 30-39', 'shortName': 'FG 30-39'},
 38: {'abbr': '40-49', 'name': 'FG Made 40-49', 'shortName': 'FG 40-49'},
 39: {'abbr': '50+', 'name': 'FG Made 50+', 'shortName': 'FG 50+'},
 40: {'abbr': '0-19', 'name': 'FG Missed 0-19', 'shortName': 'FG Miss 0-19'},
 41: {'abbr': '20-29',
  'name': 'FG Missed 20-29',
  'shortName': 'FG Miss 20-29'},
 42: {'abbr': '30-39',
  'name': 'FG Missed 30-39',
  'shortName': 'FG Miss 30-39'},
 43: {'abbr': '40-49',
  'name': 'FG Missed 40-49',
  'shortName': 'FG Miss 40-49'},
 44: {'abbr': '50+', 'name': 'FG Missed 50+', 'shortName': 'FG Miss 50+'},
 45: {'abbr': 'Sack', 'name': 'Sacks', 'shortName': 'Sack'},
 46: {'abbr': 'Int', 'name': 'Interceptions', 'shortName': 'Int'},
 47: {'abbr': 'Fum Rec', 'name': 'Fumbles Recovered', 'shortName': 'Fum Rec'},
 48: {'abbr': 'Fum F', 'name': 'Fumbles Forced', 'shortName': 'Fum Forc'},
 49: {'abbr': 'Saf', 'name': 'Safeties', 'shortName': 'Saf'},
 50: {'abbr': 'TD', 'name': 'Touchdowns', 'shortName': 'TD'},
 51: {'abbr': 'Block', 'name': 'Blocked Kicks', 'shortName': 'Block'},
 52: {'abbr': 'Yds',
  'name': 'Kickoff and Punt Return Yards',
  'shortName': 'Return Yds'},
 53: {'abbr': 'TD',
  'name': 'Kickoff and Punt Return Touchdowns',
  'shortName': 'Return TD'},
 54: {'abbr': 'Pts Allow', 'name': 'Points Allowed', 'shortName': 'Pts Allow'},
 55: {'abbr': 'Pts Allow',
  'name': 'Points Allowed 0',
  'shortName': 'Pts Allow 0'},
 56: {'abbr': 'Pts Allow',
  'name': 'Points Allowed 1-6',
  'shortName': 'Pts Allow 1-6'},
 57: {'abbr': 'Pts Allow',
  'name': 'Points Allowed 7-13',
  'shortName': 'Pts Allow 7-13'},
 58: {'abbr': 'Pts Allow',
  'name': 'Points Allowed 14-20',
  'shortName': 'Pts Allow 14-20'},
 59: {'abbr': 'Pts Allow',
  'name': 'Points Allowed 21-27',
  'shortName': 'Pts Allow 21-27'},
 60: {'abbr': 'Pts Allow',
  'name': 'Points Allowed 28-34',
  'shortName': 'Pts Allow 28-34'},
 61: {'abbr': 'Pts Allowed',
  'name': 'Points Allowed 35+',
  'shortName': 'Pts Allowed 35+'},
 62: {'abbr': 'Yds Allow', 'name': 'Yards Allowed', 'shortName': 'Yds Allow'},
 63: {'abbr': '0-99 Yds',
  'name': 'Less than 100 Total Yards Allowed',
  'shortName': 'Less 100 Yds Allowed'},
 64: {'abbr': '100-199 Yds',
  'name': '100-199 Yards Allowed',
  'shortName': '100-199 Yds Allow'},
 65: {'abbr': '200-299 Yds',
  'name': '200-299 Yards Allowed',
  'shortName': '200-299 Yds Allow'},
 66: {'abbr': '300-399 Yds',
  'name': '300-399 Yards Allowed',
  'shortName': '300-399 Yds Allow'},
 67: {'abbr': '400-449 Yds',
  'name': '400-449 Yards Allowed',
  'shortName': '400-449 Yds Allow'},
 68: {'abbr': '450-499 Yds',
  'name': '450-499 Yards Allowed',
  'shortName': '450-499 Yds Allow'},
 69: {'abbr': '500+ Yds',
  'name': '500+ Yards Allowed',
  'shortName': '500+ Yds Allow'},
 70: {'abbr': 'Tot', 'name': 'Tackle', 'shortName': 'Tack'},
 71: {'abbr': 'Ast', 'name': 'Assisted Tackles', 'shortName': 'Ast'},
 72: {'abbr': 'Sck', 'name': 'Sack', 'shortName': 'Sack'},
 73: {'abbr': 'Int', 'name': 'Defense Interception', 'shortName': 'Int'},
 74: {'abbr': 'Frc Fum', 'name': 'Forced Fumble', 'shortName': 'Frc Fum'},
 75: {'abbr': 'Fum Rec', 'name': 'Fumbles Recovery', 'shortName': 'Fum Rec'},
 76: {'abbr': 'Int TD',
  'name': 'Touchdown (Interception return)',
  'shortName': 'Int TD'},
 77: {'abbr': 'Fum TD',
  'name': 'Touchdown (Fumble return)',
  'shortName': 'Fum TD'},
 78: {'abbr': 'Blk TD',
  'name': 'Touchdown (Blocked kick)',
  'shortName': 'Blk TD'},
 79: {'abbr': 'Blk',
  'name': 'Blocked Kick (punt, FG, PAT)',
  'shortName': 'Blk'},
 80: {'abbr': 'Saf', 'name': 'Safety', 'shortName': 'Saf'},
 81: {'abbr': 'PDef', 'name': 'Pass Defended', 'shortName': 'Pass Def'},
 82: {'abbr': 'Int Yds',
  'name': 'Interception Return Yards',
  'shortName': 'Int Yds'},
 83: {'abbr': 'Fum Yds',
  'name': 'Fumble Return Yards',
  'shortName': 'Fum Yds'},
 84: {'abbr': 'TFL', 'name': 'Tackles for Loss Bonus', 'shortName': 'TFL'},
 85: {'abbr': 'QB Hit', 'name': 'QB Hit', 'shortName': 'QB Hit'},
 86: {'abbr': 'Sck Yds', 'name': 'Sack Yards', 'shortName': 'Sck Yds'},
 87: {'abbr': '10+ Tackles',
  'name': '10+ Tackles Bonus',
  'shortName': '10+ Tack'},
 88: {'abbr': '2+ Sacks', 'name': '2+ Sacks Bonus', 'shortName': '2+ Sck'},
 89: {'abbr': '3+ Passes Defended',
  'name': '3+ Passes Defended Bonus',
  'shortName': '3+ Pas Def'},
 90: {'abbr': '50+ Yard INT Return TD',
  'name': '50+ Yard INT Return TD Bonus',
  'shortName': '50+ Yard INT TD'},
 91: {'abbr': '50+ Yard Fumble Return TD',
  'name': '50+ Yard Fumble Return TD Bonus',
  'shortName': '50+ Yard Fum Ret TD'},
 92: {'abbr': 'DP 2pt Ret',
  'name': 'Def 2-point Return',
  'shortName': 'Def Player 2pt Ret'},
 93: {'abbr': 'DST 2pt Ret',
  'name': 'Team Def 2-point Return',
  'shortName': 'Team Def 2pt Ret'},
 94: {'abbr': 'FGA', 'name': 'FG Attempts', 'shortName': 'FG Attempts'},
 95: {'abbr': 'PATA', 'name': 'PAT Attempts', 'shortName': 'PAT Attempts'}
}


class Scraper(RequestScraper):
    """
    Scrapes nfl.com resources

    """

    @property
    def nfl_teamd(self, team_code):
        """
        Dict of team_code: nfl_team_id

        """
        return {
            "BAL": 325,
            "CIN": 920,
            "CLE": 1050,
            "PIT": 3900,
            "BUF": 610,
            "MIA": 2700,
            "NE": 3200,
            "NYJ": 3430,
            "CHI": 810,
            "DET": 1540,
            "GB": 1800,
            "MIN": 3000,
            "DAL": 1200,
            "NYG": 3410,
            "PHI": 3700,
            "WAS": 5110,
            "HOU": 2120,
            "IND": 2200,
            "JAX": 2250,
            "TEN": 2100,
            "DEN": 1400,
            "KC": 2310,
            "LAC": 4400,
            "OAK": 2520,
            "ATL": 200,
            "CAR": 750,
            "NO": 3300,
            "TB": 4900,
            "ARI": 3800,
            "LA": 2510,
            "SF": 4500,
            "SEA": 4600,
        }

    def game(self, gsis_id):
        """
        Gets individual gamecenter page

        Args:
            gsis_id:

        Returns:
            str

        """
        url = "http://www.nfl.com/liveupdate/game-center/{0}/{0}_gtd.json"
        return self.get(url.format(gsis_id))

    def gamebook(self, season_year, week, gamekey):
        """
        Gets XML gamebook for individual game

        Args:
            season: int 2016, 2015
            week: int 1-17
            gamekey: int 56844, etc.

        Returns:
            HTML string

        """
        url = "http://www.nflgsis.com/{}/Reg/{}/{}/Gamebook.xml"
        if week < 10:
            week = "0{}".format(week)
        else:
            week = str(week)
        return self.get(url.format(season_year, week, gamekey))

    def injuries(self, week):
        """
        Parses a weekly page with reported player injuries

        Args:
            week: int 1, 2, 3, etc.

        Returns:
            str

        """
        url = "http://www.nfl.com/injuries?week={}"
        return self.get(url.format(week))

    def ol(self, season_year):
        """
        Parses a weekly page with offensive line information

        Args:
            week: int 1, 2, 3, etc.

        Returns:
            str

        """
        url = "http://www.nfl.com/stats/categorystats?"
        params = {
            "archive": "true",
            "conference": "null",
            "role": "TM",
            "offensiveStatisticCategory": "OFFENSIVE_LINE",
            "defensiveStatisticCategory": "null",
            "season": season_year,
            "seasonType": "REG",
            "tabSeq": "2",
            "qualified": "false",
            "Submit": "Go",
        }
        return self.get(url, params=params)

    def player_profile(self, profile_path=None, player_name=None, profile_id=None):
        """
        Gets nfl.com player profile

        Args:
            profile_path(str): 'adamvinatieri/2503471'
            player_name(str): 'adamvinatieri'
            profile_id(int): 2503471

        Returns:
            str

        """
        if profile_path:
            url = "http://www.nfl.com/player/{}/profile".format(profile_path)
        elif player_name and profile_id:
            url = "http://www.nfl.com/player/{}/{}/profile".format(
                player_name, profile_id
            )
        else:
            raise ValueError("must specify profile_path or player_name and profile_id")
        return self.get(url)

    def players(self, last_initial, player_type="current"):
        """

        Args:
            last_initial: A, B, C, etc.
            player_type: 'current' or 'all'

        Returns:
            response

        """
        try:
            last_initial = last_initial.upper()
            url = "http://www.nfl.com/players/search?"
            if last_initial in ascii_uppercase:
                params = {
                    "category": "lastName",
                    "filter": last_initial,
                    "playerType": player_type,
                }
                return self.session.get(url, params=params)
            else:
                raise ValueError("invalid last_initial")
        except ValueError as e:
            logging.exception(e)

    def player_search_name(self, player_name, player_type="current"):
        """
        Searches for player using NFL search engine

        Args:
            player_name(str): 'Jones, Bobby'
            player_type(str): 'current' or 'historical'

        Returns:
            str - page of search results

        """
        url = "http://www.nfl.com/players/search?"
        params = {"category": "name", "filter": player_name, "playerType": player_type}
        return self.get(url, params=params)

    def player_search_web(self, player_name):
        """
        Searches for player profile page using duckduckgo search engine

        Args:
            player_name(str): 'Jones, Bobby'

        Returns:
            str - URL for profile page

        """
        patt = re.compile(r"(^http://www.nfl.com/player/\w+/\d+/profile)")
        try:
            ln, fn = player_name.split(", ")
        except:
            fn, ln = player_name.split()
        term = fn + "+" + ln
        url = f"https://duckduckgo.com/?q=nfl.com+{term}&ia=web"
        response = self.session.get(url)
        response.html.render()
        for link in response.html.links:
            match = re.search(patt, link)
            if match:
                return match.group(1)
        return None

    def schedule_week(self, season, week):
        """
        Parses a weekly schedule page with links to individual gamecenters
        Similar to score_week, but does not have scores for each quarter

        Args:
            season: int 2017, 2016, etc.
            week: int 1, 2, 3, etc.

        Returns:
            str

        """
        url = f"http://www.nfl.com/schedules/{season}/REG{week}"
        return self.get(url, encoding="ISO-8859-1")

    def score_week(self, season, week):
        """
        Parses a weekly page with links to individual gamecenters
        Similar to schedule_week, but has scores for each quarter

        Args:
            season: int 2017, 2016, etc.
            week: int 1, 2, 3, etc.

        Returns:
            str

        """
        url = "http://www.nfl.com/scores/{0}/REG{1}"
        return self.get(url.format(season, week))

    def team_roster(self, team_code=None, nfl_team_id=None):
        """

        Args:
            team_code(str):
            nfl_team_id(int):

        Returns:
            Response

        """
        if team_code:
            nfl_team_id = self.nfl_teamd.get(team_code)
        if not nfl_team_id:
            raise ValueError("invalid team code or id: %s %s", team_code, nfl_team_id)
        base_url = "http://www.nfl.com/players/search?"
        params = {"category": "team", "playerType": "current", "filter": nfl_team_id}
        return self.get(base_url, params=params, return_object=True)


class Parser:
    """
    Used to parse NFL.com GameCenter pages,
    which are json documents with game and play-by-play stats

    """

    def __init__(self):
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def _gamecenter_team(self, team):
        """
        Parses home or away team into stats dictionary

        Args:
            team: dictionary representing home or away team

        Returns:
            dict

        """
        categories = [
            "passing",
            "rushing",
            "receiving",
            "fumbles",
            "kickret",
            "puntret",
            "defense",
        ]
        players = {}
        for category in categories:
            for player_id, player_stats in team[category].items():
                if not player_id in players:
                    players[player_id] = {"player_id": player_id}
                    players[player_id][category] = player_stats
        return players

    def esb_id(self, content):
        """
        Gets player esb_id

        Args:
            content(str):

        Returns:
            str

        """
        soup = BeautifulSoup(content, "lxml")
        # GSIS ID and ESB ID are buried in the comments
        for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
            if "GSIS" in c:
                parts = [part.strip() for part in c.split("\n")]
                return parts[2].split(":")[-1].strip()
        return None

    def gamecenter(self, parsed):
        """
        Parses gamecenter (json document)

        Args:
            content: parsed json document

        Returns:
            dict

        Misc:
            puntret: avg, lng, lngtd, name, ret, tds
            fumbles: lost, name, rcv, tot, trcv, yds
            defense: ast, ffum, int, name, sk, tkl
            rushing: att, lng.lngtd, name, tds, twopta, twoptm, yds
            receiving: lng, lngtd, name, rec, tds, twopta, twoptm, yds
            passing: att, cmp, ints, name, tds, twopta, twoptm, yds

        """
        game_id = parsed.keys()[0]
        home_team_stats = self._gamecenter_team(parsed[game_id]["home"]["stats"])
        away_team_stats = self._gamecenter_team(parsed[game_id]["away"]["stats"])
        return merge_two(home_team_stats, away_team_stats)

    def game_page(self, content):
        """
        Parses individual game page from NFL.com

        Args:
            content:

        Returns:
            list: of dict

        """
        games = []
        soup = BeautifulSoup(content, "lxml")

        for a in soup.findAll("a", {"class": "game-center-link"}):
            game = {}
            pattern = re.compile(
                r"/gamecenter/(\d+)/(\d+)/REG(\d+)/([a-zA-Z0-9]+[@]{1}[a-zA-Z0-9]+)"
            )
            match = re.search(pattern, a["href"])
            if match:
                game["gsis_id"], game["season_year"], game["week"], game[
                    "matchup"
                ] = match.groups()
                game["away"], game["home"] = game["matchup"].split("@")
                game["game_date"] = convert_format(game["gsis_id"][0:8], "nfl")
                game["url"] = "http://www.nfl.com{}" + a["href"]
            if game:
                games.append(game)
        return games

    def injuries(self, content, season, week):
        """
        Returns injured players from injruies page

        Args:
            str

        Returns:
            list: of player dict

        """
        players = []
        away_patt = re.compile(
            r"dataAway.*?(\[.*?\]);", re.MULTILINE | re.IGNORECASE | re.DOTALL
        )
        home_patt = re.compile(
            r"dataHome.*?(\[.*?\]);", re.MULTILINE | re.IGNORECASE | re.DOTALL
        )
        awayAbbr_patt = re.compile(r"awayAbbr\s+=\s+\'([A-Z]+)\'")
        homeAbbr_patt = re.compile(r"homeAbbr\s+=\s+\'([A-Z]+)\'")

        soup = BeautifulSoup(content, "lxml")

        # values are embedded in <script> tag
        # I am trying to scrape the homeAbbr and awayAbbr variables
        for script in soup.find_all("script"):
            try:
                # get away and home team codes
                match = re.search(awayAbbr_patt, script.text)
                if match:
                    away_team = match.group(1)

                match = re.search(homeAbbr_patt, script.text)
                if match:
                    home_team = match.group(1)

                # away team
                away_player = {
                    "team_code": away_team,
                    "season_year": season,
                    "week": week,
                }
                match = re.search(away_patt, script.text)
                if match:
                    for player in demjson.decode(match.group(1)):
                        context = away_player.copy()
                        context.update(player)
                        players.append(context)

                # home team
                home_player = {
                    "team_code": home_team,
                    "season_year": season,
                    "week": week,
                }
                match = re.search(home_patt, script.text)
                if match:
                    for player in demjson.decode(match.group(1)):
                        context = home_player.copy()
                        context.update(player)
                        players.append(context)
            except:
                pass

        return players

    def ol(self, content):
        """
        Parses offensive line stats page on nfl.com

        Args:
            content(str): HTML page

        Returns:
            list

        """
        soup = BeautifulSoup(content, "lxml")
        headers = [
            "rank",
            "team",
            "experience",
            "rush_att",
            "rush_yds",
            "rush_ypc",
            "rush_tds",
            "rush_fd_left",
            "rush_neg_left",
            "rush_pty_left",
            "rush_pwr_left",
            "rush_fd_center",
            "rush_neg_center",
            "rush_pty_center",
            "rush_pwr_center",
            "rush_fd_right",
            "rush_neg_right",
            "rush_pty_right",
            "rush_pwr_right",
            "sacks",
            "qb_hits",
        ]

        return [
            dict(zip(headers, [td.text.strip() for td in tr.find_all("td")]))
            for tr in soup.find("table", {"id": "result"}).find("tbody").find_all("tr")
        ]

    def players(self, response):
        """
        Returns alphabetical player page on nfl.com

        Args:
            response

        Returns:
            list of dict

        """
        patt = re.compile(r"/player/(\w+/\d+)/profile")
        players = []
        for tr in response.html.find("tr"):
            if tr.attrs.get("class") and tr.attrs.get("class")[0] in ["even", "odd"]:
                player = {}
                vals = [el.text for el in tr.find("td")]
                player["pos"] = vals[0]
                player["num"] = vals[1]
                player["plyr"] = vals[2]
                player["status"] = vals[3]
                player["team"] = vals[-1]

                # now add profile
                for link in tr.links:
                    match = re.search(patt, link)
                    if match:
                        player["profile_path"] = match.group(1)
                players.append(player)
        return players

    def player_page(self, content, profile_id):
        """
        Returns data from individual player page

        Args:
            content(str):
            profile_id(str):

        Returns:
            dict

        """
        soup = BeautifulSoup(content, "lxml")
        player = {"status": "Active"}

        # GSIS ID and ESB ID are buried in the comments
        for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
            if "GSIS" in c:
                parts = [part.strip() for part in c.split("\n")]
                esb_id = parts[2].split(":")[-1].strip()
                gsis_id = parts[3].split(":")[-1].strip()
                player["nflcom_player_id"] = gsis_id
                player["profile_id"] = profile_id
                if esb_id:
                    player["esb_id"] = esb_id
                break

        # Most player data is found in the player-profile div
        # Then have to loop through paragraphs in that div
        paras = soup.find("div", {"id": "player-profile"}).find_all("p")

        if not paras or len(paras) < 6:
            paras = soup.find("div", {"id": "player-info"}).find_all("p")

        if not paras or len(paras) < 6:
            return None

        try:
            # paras[0]: name and number
            spans = paras[0].find_all("span")
            name = spans[0].text.strip()
            player["full_name"] = name
            player["first_name"], player["last_name"] = first_last_pair(name)
            number, pos = spans[1].text.split()
            player["number"] = digits(number)
            player["position"] = pos

            # paras[1]: team
            player["team"] = paras[1].find("a")["href"].split("=")[-1]
        except (IndexError, ValueError) as e:
            logging.exception(e)
            return None

        try:
            # paras[2]: height, weight, age
            parts = paras[2].text.split()
            feet, inches = parts[1].split("-")
            player["height"] = int(digits(feet)) * 6 + int(digits(inches))
            player["weight"] = digits(parts[3])
            player["age"] = digits(parts[5])
        except (IndexError, ValueError) as e:
            logging.exception(e)

        try:
            # birthdate
            parts = paras[3].text.split()
            player["birthdate"] = parts[1].strip()
        except (IndexError, ValueError) as e:
            logging.exception(e)

        try:
            # college
            parts = paras[4].text.split()
            player["college"] = parts[1].strip()
        except (IndexError, ValueError) as e:
            logging.exception(e)

        try:
            # years pro
            parts = paras[5].text.split()
            ordinal = parts[1].strip()
            player["years_pro"] = "".join(ch for ch in ordinal if ch.isdigit())
        except (IndexError, ValueError) as e:
            logging.exception(e)

        return player

    def player_search_name(self, content):
        """
        Parses player search results

        Args:
            content(str): HTML page

        Returns:
            tuple - full_name, nfl_name, profile_id

        """
        vals = []
        soup = BeautifulSoup(content, "lxml")
        patt = re.compile(r"\/player.*?\d+\/profile", re.IGNORECASE | re.UNICODE)

        for a in soup.find_all("a", {"href": patt}):
            nfl_name, profile_id = a["href"].split("/")[-3:-1]
            vals.append((a.text, nfl_name, profile_id))
        return vals

    def position(self, content):
        """
        Returns player's position from his profile page on nfl.com

        Args:
            content(str): HTML page

        Returns:
            str: 'QB', 'RB', 'WR', 'TE', 'UNK'

        """
        allowed = [
            "C",
            "CB",
            "DB",
            "DE",
            "DL",
            "DT",
            "FB",
            "FS",
            "G",
            "ILB",
            "K",
            "LB",
            "LS",
            "MLB",
            "NT",
            "OG",
            "OL",
            "OLB",
            "OT",
            "P",
            "QB",
            "RB",
            "SAF",
            "SS",
            "T",
            "TE",
            "WR",
            "UNK",
            "DST",
        ]

        xref = {"ML": "LB", "IL": "LB", "SAF": "S"}
        patt = re.compile(r"[A-Z]{1}.*?,\s+([A-Z]{1,3})", re.IGNORECASE | re.UNICODE)
        soup = BeautifulSoup(content, "lxml")
        title = soup.title.text
        match = re.search(patt, title)
        try:
            pos = match.group(1)
            if pos in allowed:
                return pos
            return xref.get(pos, "UNK")
        except:
            return "UNK"

    def team_roster(self, response):
        """

        Args:
            response:

        Returns:

        """
        return self.players(response)

    def upcoming_week_page(self, content):
        """
        Parses upcoming week page (before games played)

        Args:
            content(str): HTML page

        Returns:
            list: of game dict

        """
        games = []
        etz = "America/New_York"
        soup = BeautifulSoup(content, "lxml")
        patt = re.compile(
            r"(game[.]+week.*?homeCityName:.*?[-]+[>]+)", re.MULTILINE | re.DOTALL
        )
        subpatt = re.compile(
            r"formattedDate: (.*?)\s+[-]+[>]+.*?formattedTime: (\d+:\d+ [AP]+M)",
            re.MULTILINE | re.DOTALL,
        )

        # get game data from comments
        start_times = []
        for match in re.finditer(patt, content):
            submatch = re.search(subpatt, match.group(1))
            dtstr = f"{submatch.group(1)} {submatch.group(2)}"
            parsed = pendulum.parse(dtstr, tz=etz)
            start_times.append((parsed.in_tz("UTC"), parsed.date().strftime("%A")))

        wanted = [
            "data-gameid",
            "data-away-abbr",
            "data-home-abbr",
            "data-localtime",
            "data-site",
        ]

        for start_time, div in zip(
            start_times, soup.select("div.schedules-list-content")
        ):
            game = {att: div[att].strip() for att in div.attrs if att in wanted}
            game["start_time"] = start_time[0]
            game["day_of_week"] = start_time[1]
            games.append(game)

        return games

    def week_page(self, content):
        """
        Parses weekly scoreboard page from NFL.com

        Args:
            content(str):

        Returns:
            dict: of gsis_id and dict

        """
        games = []
        soup = BeautifulSoup(content, "lxml")

        # weekly page will have links to individual games in format:
        # <a href="/gamecenter/2014090400/2014/REG1/packers@seahawks"
        # class="game-center-link" . . . </a>
        for a in soup.findAll("a", {"class": "game-center-link"}):
            game = {}
            pattern = re.compile(
                r"/gamecenter/(\d+)/(\d+)/REG(\d+)/([a-zA-Z0-9]+[@]{1}[a-zA-Z0-9]+)"
            )
            match = re.search(pattern, a["href"])
            if match:
                game["gsis_id"], game["season_year"], game["week"], game[
                    "matchup"
                ] = match.groups()
                game["away"], game["home"] = game["matchup"].split("@")
                game["game_date"] = convert_format(game["gsis_id"][0:8], "nfl")
                game["url"] = "http://www.nfl.com{}" + a["href"]
            if game:
                games.append(game)
        return games


class Agent:
    """
    Combines common scraping/parsing tasks

    """

    def __init__(self, scraper=None, parser=None, cache_name="nfl-agent"):
        """
        Creates Agent object

        Args:
            scraper: NFLComScraper object
            parser: NFLComParser object
            cache_name: string

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
        self.base, self.eng, self.session = setup(database="pg", schema="base")

    def team_roster_urls(self):
        """
        Gets URLs for nfl.com team roster pages

        Returns:
            list: of str

        """
        base_url = "http://www.nfl.com/players/search?"
        params = {"category": "team", "playerType": "current"}

        # team_roster_urls
        roster_urls = {}
        response = self._s.get(base_url, params=params, return_object=True)
        div = response.html.find("#playertabs_2", first=True)
        for tr in div.find("tr"):
            for td in tr.find("td"):
                for p in td.find("p"):
                    a = p.find("a", first=True)
                    if a:
                        roster_urls[p.text] = next(iter(a.absolute_links))
        return roster_urls

    def get_team_rosters(self):
        """
        Gets all 32 team rosters

        Returns:
            list: of dict

        """
        rosters = []
        for team_name, url in self.team_roster_urls().items():
            logging.info("starting %s: %s", team_name, url)
            response = self._s.get(url, return_object=True)
            roster = self._p.team_roster(response)
            logging.info(roster)
            rosters.append(roster)
        return [item for sublist in rosters for item in sublist]

    def get_player(self, player):
        """

        Args:
            player(dict):

        Returns:
            bool

        """
        PlayerXref = self.base.classes.player_xref
        return (
            self.session.query(PlayerXref)
            .filter(PlayerXref.source_player_code != None)
            .filter(PlayerXref.source_player_code == player.get("profile_path"))
            .filter(PlayerXref.source == "nflcom")
            .first()
        )

    def save_unmatched(self, unmatched, file_name="/tmp/unmatched.csv"):
        """
        Saves unmatched players to CSV file

        Args:
            unmatched(list): of dict
            file_name(str): default '/tmp/unmatched.csv'

        Returns:
            None

        """
        if unmatched and len(unmatched) > 0:
            save_csv(
                data=unmatched,
                csv_fname=file_name,
                fieldnames=sorted(list(unmatched[0].keys())),
            )

    def update_unmatched_xref(self, unmatched):
        """
        Adds unmatched player to player_xref

        Args:
            unmatched:

        Returns:

        """
        Player = self.base.classes.player
        PlayerXref = self.base.classes.player_xref

        for item in unmatched:
            profile_path = item.get("profile_path")
            if profile_path:
                profile_id = profile_path.split("/")[-1]
                try:
                    content = self._s.player_profile(profile_path=profile_path)
                    p = self._p.player_page(content, profile_id)
                    match = (
                        self.session.query(Player)
                        .filter(Player.full_name == p["full_name"])
                        .filter(Player.pos == p["position"])
                        .filter(Player.birthdate == p.get("birthdate", "1960-01-01"))
                        .first()
                    )
                    if match:
                        self.session.add(
                            PlayerXref(
                                player_id=match.player_id,
                                source="nflcom",
                                source_player_id=match.nflcom_player_id,
                                source_player_code=profile_id,
                                source_player_name=match.full_name,
                                source_player_position=match.position,
                            )
                        )

                except:
                    pass

        self.session.commit()

    def update_unmatched(self, unmatched):
        """

        Args:
            unmatched:

        Returns:

        """
        Player = self.base.classes.player

        for item in unmatched:
            profile_path = item.get("profile_path")
            if profile_path:
                profile_id = profile_path.split("/")[-1]
                try:
                    content = self._s.player_profile(profile_path=profile_path)
                    p = self._p.player_page(content, profile_id)
                    filt = text(f"nflcom_player_id='{p['nflcom_player_id']}'")
                    match = self.session.query(Player).filter(filt).first()

                    # if no match, add to player table and get autoincrement id
                    # if match, get existing player_id
                    if match:
                        logging.info("found match for %s", p["full_name"])
                    else:
                        logging.info("no match for %s", p["full_name"])
                        match = (
                            self.session.query(Player)
                            .filter(Player.first_name == p["first_name"])
                            .filter(Player.last_name == p["last_name"])
                            .filter(Player.pos == p["position"])
                            .filter(Player.birthdate == p.get("birthdate"))
                            .first()
                        )
                        if match:
                            match.nflcom_player_id = p["nflcom_player_id"]
                            if p.get("height"):
                                match.height = p["height"]
                            if p.get("weight"):
                                match.weight = p["weight"]
                            if p.get("college"):
                                match.college = p["college"]
                        else:
                            playerobj = Player(
                                nflcom_player_id=p["nflcom_player_id"],
                                first_name=p["first_name"],
                                last_name=p["last_name"],
                                pos=p["position"],
                                height=p.get("height", None),
                                weight=p.get("weight", None),
                                birthdate=p.get("birthdate", None),
                                college=p.get("college", None),
                            )
                            self.session.add(playerobj)
                        self.session.commit()
                except:
                    pass

    def update_team_rosters(self, rosters):
        """
        Adds team rosters to roster table

        Args:
            rosters(list): of dict

        Returns:
            None

        """
        unmatched = []
        matched = []
        Roster = self.base.classes.roster
        as_of = today()
        for item in rosters:
            # sample item
            # {'pos': 'WR',
            # 'num': '16',
            # 'plyr': 'Adeboyejo, Quincy',
            # 'status': 'ACT',
            # 'team': 'BAL',
            # 'profile_path': 'quincyadeboyejo/2557843'}

            # step one: see if player in table
            # if not in table, then add
            player = self.get_player(item)
            if not player:
                # add player
                unmatched.append(item)
                logging.info("no match for %s", item["plyr"])
                continue
            # step two: add player to roster table
            matched.append(
                {"as_of": as_of, "player_id": player.player_id, "team_id": item["team"]}
            )
            logging.info("added %s", item["plyr"])

        # add roster objects to database
        self.session.bulk_insert_mappings(Roster, matched)
        self.session.commit()

        return unmatched

    def upcoming_games(self, season, week):
        """
        Gets all games from weekly schedule page from NFL.com

        Args:
            season(int): 2018, etc.
            week(int): 1, etc.

        Returns:
            list of dict

        """
        content = self._s.schedule_week(season, week)
        return self._p.upcoming_week_page(content)

    def yearly_schedule(self, season):
        """

        Args:
            season(int): 2018, etc.

        Returns:
            list: of dict

        """
        Game = self.base.classes.game
        for week in range(1, 18):
            logging.info("starting week %s", week)
            content = self._s.schedule_week(season, week)
            utcnow = datetime.utcnow()
            gobjs = []
            for g in self._p.upcoming_week_page(content):
                gobj = Game(
                    gsis_id=g["data-gameid"],
                    start_time=g["start_time"],
                    week=week,
                    day_of_week=g["day_of_week"],
                    season_year=season,
                    season_type="Regular",
                    finished=False,
                    home_team=g["data-home-abbr"],
                    away_team=g["data-away-abbr"],
                    time_inserted=utcnow,
                    time_updated=utcnow,
                )
                gobjs.append(gobj)
            self.session.bulk_save_objects(gobjs)
            self.session.commit()


if __name__ == "__main__":
    pass
