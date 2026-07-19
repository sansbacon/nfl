"""
soh.py
classes for scraping, parsing sportsoddshistory.com

from time import sleep
from prettyprinter import pprint
from sportscraper.utility import save_csv

all_win_totals = []
s = Scraper()
p = Parser()

for y in range(2009, 2019):
    print('starting %s', y)
    response = s.win_totals(y)
    all_win_totals.append(p.win_totals(response))
    sleep(3)

fname = '/home/sansbacon/win_totals.csv'
save_csv([item for sublist in all_win_totals for item in sublist], fname)
"""

import logging


from sportscraper.scraper import RequestScraper


class Scraper(RequestScraper):
    """
    Scrape sportsoddshistory

    """

    def win_totals(self, season_year):
        """
        Gets vegas season win totals

        Args:
            season_year (int): 2017, 2016, etc.

        Returns:
            response

        """
        url = "https://www.sportsoddshistory.com/nfl-win/?"
        params = {"y": season_year, "sa": "nfl", "t": "win", "o": "t"}

        return self.get(url, params=params, return_object=True)


class Parser:
    """
    Parse ESPN.com for football stats

    """

    def __init__(self):
        """
        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def win_totals(self, response):
        """
        Parses vegas win totals

        Args:
            response(requests_html.Response()):

        Returns:
            list: of dict

        """
        vals = []
        h1 = response.html.find("div.entry_content > h1", first=True)
        season_year = int(h1.text.split()[0])
        tbl = response.html.find("table.soh1", first=True)
        tbody = tbl.find("tbody", first=True)
        for tr in tbody.find("tr"):
            tdvals = [td.text for td in tr.find("td")]
            val = {
                "season_year": season_year,
                "team": tdvals[0],
                "win_total": tdvals[1],
                "over_odds": tdvals[2],
                "under_odds": tdvals[3],
            }

            for k in ["over_odds", "under_odds"]:
                try:
                    val[k] = int(val[k])
                except ValueError:
                    try:
                        val[k] = int(val[k].replace("+", ""))
                    except ValueError:
                        val[k] = 0
            vals.append(val)
        return vals


if __name__ == "__main__":
    pass
