# -*- coding: utf-8 -*-
# fo.py
# classes to scrape and parse footballoutsiders.com

import logging
import time

from bs4 import BeautifulSoup
from sportscraper.scraper import RequestScraper
from sportscraper.utility import merge_two


class Scraper(RequestScraper):
    def dl(self, season=""):
        """
        Gets DL stats page

        Returns:
            HTML string
        """
        url = "http://www.footballoutsiders.com/stats/dl{}"
        return self.get(url.format(season))

    def drive(self, offdef, season=""):
        """
        Gets drivestats page

        Returns:
            HTML string
        """
        if offdef == "off":
            url = "http://www.footballoutsiders.com/stats/drivestatsoff{}"
        elif offdef == "def":
            url = "http://www.footballoutsiders.com/stats/drivestatsdef{}"
        else:
            raise ValueError("invalid value for offdef: {}".format(offdef))
        return self.get(url.format(season))

    def ol(self, season_year):
        """
        Gets OL stats page

        Args:
            season_year(int): 2018, etc.

        Returns:
            response

        """
        url = f"http://www.footballoutsiders.com/stats/ol{season_year}"
        return self.get(url, return_object=True)

    def qb(self, season=""):
        """
        Gets QB stats page

        Returns:
            HTML string
        """
        url = "http://www.footballoutsiders.com/stats/qb{}"
        return self.get(url.format(season))

    def rb(self, season=""):
        """
        Gets RB stats page

        Returns:
            HTML string
        """
        url = "http://www.footballoutsiders.com/stats/rb{}"
        return self.get(url.format(season))

    def snapcounts(self, season_year, week, pos):
        """

        Args:
            season:
            week:
            pos:

        Returns:
            str: HTML page

        """
        url = "https://www.footballoutsiders.com/stats/snapcounts"
        params = {
            "team": "ALL",
            "week": week,
            "pos": pos,
            "year": season_year,
            "Submit": "Submit",
        }
        return self.post(url, params)

    def te(self, season=""):
        """
        Gets TE stats page

        Returns:
            HTML string
        """
        url = "http://www.footballoutsiders.com/stats/te{}"
        return self.get(url.format(season))

    def wr(self, season=""):
        """
        Gets WR stats page

        Returns:
            HTML string
        """
        url = "http://www.footballoutsiders.com/stats/wr{}"
        return self.get(url.format(season))

    def snap_counts(self, year, week):
        """
        Gets weekly snapcounts

        Args:
            year: 2017, 2016, etc.
            week: 1, 2, etc.

        Returns:
            HTML string
        """
        url = "http://www.footballoutsiders.com/stats/snapcounts"
        payload = {
            "team": "ALL",
            "week": week,
            "pos": "ALL",
            "year": year,
            "Submit": "Submit",
        }
        return self.post(url, payload)

    def team_defense(self, season=""):
        """
        Gets defense DVOA page

        Returns:
            HTML string
        """
        url = "http://www.footballoutsiders.com/stats/teamdef{}"
        return self.get(url.format(season))

    def team_offense(self, season=""):
        """
        Gets offense DVOA page

        Returns:
            HTML string
        """
        url = "http://www.footballoutsiders.com/stats/teamoff{}"
        return self.get(url.format(season))

    def team_efficiency(self, season=""):
        """
        Gets team DVOA page

        Returns:
            HTML string
        """
        url = "http://www.footballoutsiders.com/stats/teameff{}"
        return self.get(url.format(season))


class APIScraper(RequestScraper):
    def __init__(self, cache_name="fo-api", **kwargs):
        """
        Scrape FO API

        Args:
            cache_name: should be full path

        """
        super().__init__(self, cache_name=cache_name, **kwargs)

        if not kwargs.get("headers"):
            headers = {"Referer": "http://www.footballoutsiders.com/premium/index.php"}
            self.headers.update(headers)

    def dvoa_week(self, season, week):
        """
        Gets DVOA for specific week in season

        Returns:
            HTML string
        """
        url = (
            "http://www.footballoutsiders.com/premium/weekTeamSeasonDvoa.php?"
            "od=O&year={}&team=ARI&week={}"
        )
        return self.get(url.format(season, week))

    def team_season(self, season, team):
        """
        Gets team DVOA for specific season

        Returns:
            HTML string
        """
        url = "https://www.footballoutsiders.com/premium/weekByTeam.php?od=O&year={}&team={}&week=1"
        return self.get(url.format(season, team))

    def team_week(self, season, week):
        """
        Gets team DVOA for specific week

        Returns:
            HTML string
        """
        url = "https://www.footballoutsiders.com/premium/weekTeamSeasonDvoa.php?od=O&year={}&team=ARI&week={}"
        return self.get(url.format(season, week))


class Parser(object):
    """

    """

    def dl(self, content, season_year):
        # there can be 2 teams listed on one row b/c pass and rush usually not the same team

        rush_headers = [
            "rush_rank",
            "team",
            "adj_line_yards",
            "rb_yards",
            "power_success",
            "power_rank",
            "stuffed",
            "stuffed_rank",
            "sec_level_yards",
            "sec_level_rank",
            "open_field_yards",
            "open_field_rank",
        ]
        pass_headers = ["team", "pass_rank", "sacks", "adj_sack_rate"]

        soup = BeautifulSoup(content, "lxml")
        t = soup.find("table", {"class": "stats"})
        teams = {}

        # skip first two lines - double headers
        for tr in t.find_all("tr")[2:]:
            tds = tr.find_all("td")
            if len(tds) != len(rush_headers) + len(pass_headers):
                continue

            # rushing
            rvals = [str(td.string).replace("%", "").strip() for td in tds[0:12]]
            team = rvals[1]
            if teams.get(team):
                for idx, h in enumerate(rush_headers):
                    if h == "team":
                        continue
                    else:
                        teams[team][h] = rvals[idx]
            else:
                teams[team] = dict(zip(rush_headers, rvals))

            # passing
            pvals = [str(td.string).replace("%", "").strip() for td in tds[12:]]
            team = pvals[0]
            if teams.get(team):
                for idx, h in enumerate(pass_headers):
                    if h == "team":
                        continue
                    else:
                        teams[team][h] = pvals[idx]
            else:
                teams[team] = dict(zip(pass_headers, pvals))

            teams[team]["season_year"] = season_year

        return teams.values()

    def drive(self, content, offdef):
        """

        Args:
            content:

        Returns:

        """
        teams = {}
        soup = BeautifulSoup(content, "lxml")

        if offdef == "off":
            # headers = ['team', 'team_net', 'yds_dr_net', 'pts_dr_net', 'dsr_off', 'yds_dr_off',
            #           'yds_dr_off', 'pts_dr_off', 'dsr_def', 'yds_dr_def', 'pts_dr_def', 'dsr']
            headers = [
                [
                    "team",
                    "drives",
                    "yds_dr",
                    "pts_dr",
                    "tov_dr",
                    "int_dr",
                    "fum_dr",
                    "los_dr",
                    "plays_dr",
                    "top_dr",
                    "dsr",
                ],
                [
                    "team",
                    "drives",
                    "tds_dr",
                    "fg_dr",
                    "punts_dr",
                    "tao_dr",
                    "los_ko",
                    "td_fg",
                    "pts_rz",
                    "tds_rz",
                    "avg_lead",
                ],
            ]
        elif offdef == "def":
            headers = []
        else:
            raise ValueError("invalid value for offdef: {}".format(offdef))

        # get the first table and skip header lines
        for t, h in zip(soup.select("table.stats"), headers):
            for tr in t.find_all("tr"):
                if tr.find("td").text == "Team":
                    continue
                else:
                    vals = [td.text.split()[0] for td in tr.find_all("td")]
                    if len(vals) == len(h):
                        context = teams.get(vals[0], {})
                        context.update(dict(zip(h, vals)))
                        teams[vals[0]] = context
                    else:
                        raise ValueError("too many values: {}".format(vals))
        return teams

    def ol(self, response):
        """

        Args:
            response:

        Returns:

        """
        season_year = int(response.html.find("#page-title", first=True).text.split()[0])

        # rushing and passing stats now on same row for same team starting in 2018
        # no need to match up disparate rows
        if season_year > 2017:
            teams = []
            rush_headers = [
                "rush_rank",
                "team",
                "adj_line_yards",
                "rb_yards",
                "power_success",
                "power_rank",
                "stuffed",
                "stuffed_rank",
                "sec_level_yards",
                "sec_level_rank",
                "open_field_yards",
                "open_field_rank",
            ]
            pass_headers = ["pass_rank", "sacks", "adj_sack_rate"]
            for tr in response.html.find("tbody", first=True).find("tr"):
                tds = tr.find("td")
                if len(tds) != len(rush_headers) + len(pass_headers):
                    continue
                # rushing
                rvals = [str(td.text).replace("%", "").strip() for td in tds[0:12]]
                team = dict(zip(rush_headers, rvals))
                team["season_year"] = season_year
                # passing
                pvals = [str(td.text).replace("%", "").strip() for td in tds[12:]]
                teams.append(merge_two(team, dict(zip(pass_headers, pvals))))
            return teams
        else:
            teams = {}
            rush_headers = [
                "rush_rank",
                "team",
                "adj_line_yards",
                "rb_yards",
                "power_success",
                "power_rank",
                "stuffed",
                "stuffed_rank",
                "sec_level_yards",
                "sec_level_rank",
                "open_field_yards",
                "open_field_rank",
            ]
            pass_headers = ["team", "pass_rank", "sacks", "adj_sack_rate"]
            t = response.html.find("table.stats", first=True)
            for tr in t.find("tr")[2:]:
                tds = tr.find("td")
                if len(tds) != len(rush_headers) + len(pass_headers):
                    continue
                # rushing
                rvals = [str(td.text).replace("%", "").strip() for td in tds[0:12]]
                team = rvals[1]
                if teams.get(team):
                    for idx, h in enumerate(rush_headers):
                        if h == "team":
                            continue
                        else:
                            teams[team][h] = rvals[idx]
                else:
                    teams[team] = dict(zip(rush_headers, rvals))
                # passing
                pvals = [str(td.text).replace("%", "").strip() for td in tds[12:]]
                team = pvals[0]
                if teams.get(team):
                    for idx, h in enumerate(pass_headers):
                        if h == "team":
                            continue
                        else:
                            teams[team][h] = pvals[idx]
                else:
                    teams[team] = dict(zip(pass_headers, pvals))
                teams[team]["season_year"] = season_year
            return list(teams.values())

    def qb(self, content):
        """
        TODO: fix headers
        Args:
            content:

        Returns:

        """
        teams = []
        soup = BeautifulSoup(content, "lxml")
        headers = [
            "team",
            "team_net",
            "yds_dr_net",
            "pts_dr_net",
            "dsr_off",
            "yds_dr_off",
            "yds_dr_off",
            "pts_dr_off",
            "dsr_def",
            "yds_dr_def",
            "pts_dr_def",
            "dsr",
        ]

        # skip first line
        for tr in soup.select("table.stats tr")[1:]:
            pass
            # Player	Team	DYAR	Rk	YAR	Rk	DVOA	Rk	VOA	QBR	Rk	Pass	Yards	EYds	TD	FK	FL	INT
            # C%	DPI	ALEX

    def snapcounts(self, content, season_year=None, week=None):
        """

        Args:
            content (str): HTML from snapcounts page
            season_year (int): 2017, etc.
            week (int): 1, 2, etc.

        Returns:
            list: of dict

        """
        results = []
        doc = HTML(html=content)
        t = doc.html.find("#dataTable")[0]
        hdrs = [th.text.lower().strip().replace(" ", "_") for th in t.find("th")]
        for tr in t.find("tbody")[0].find("tr"):
            item = dict(zip(hdrs, [td.text.strip() for td in tr.find("td")]))
            if season_year:
                item["season_year"] = season_year
            if week:
                item["week"] = week
            results.append(item)
        return results


class Agent(object):
    """
    Usage:

    """

    def __init__(self, wb=False):
        self._s = Scraper(cache_name="foagent-cache")
        self._p = Parser()

    def snap_counts(self, seasons, weeks):
        players = []

        for season in seasons:
            for week in weeks:
                content = self._s.snap_counts(season, week)
                players += self._p.snap_counts(content, season, week)
                time.sleep(1)
        return players


if __name__ == "__main__":
    # pass
    import json

    logging.basicConfig(level=logging.INFO)
    s = Scraper(cache_name="fo")
    p = Parser()
    all_ols = []
    for y in range(2009, 2019):
        logging.info(f"starting {y}")
        response = s.ol(y)
        ols = p.ol(response)
        for idx, ol in enumerate(ols):
            if ol["team"] in ["LAR", "STL"]:
                ols[idx]["team"] = "LA"
            elif ol["team"] in ["SD", "SDC"]:
                ols[idx]["team"] = "LAC"
        all_ols.append(ols)

    with open("/home/sansbacon/ol.json", "w") as f:
        json.dump([i for s in all_ols for i in s], f)
