"""

tests/test_pp.py

"""

import logging
import random
import pytest

from nfl.soh import Scraper, Parser


logging.basicConfig(level=logging.INFO)


@pytest.fixture
def scraper():
    return Scraper()


@pytest.fixture
def parser():
    return Parser()

@pytest.fixture()
def season():
    return random.choice(list(range(2013, 2019)))


def test_win_totals(scraper, parser, season):
    response = scraper.win_totals(season)
    win_totals = parser.win_totals(response)
    assert response.status_code == 200
    assert isinstance(win_totals, list)
    win_total = random.choice(win_totals)
    assert isinstance(win_total, dict)
    assert bool(win_total)
    assert 'team' in win_total.keys()
    assert isinstance(win_total['season_year'], int)
    assert isinstance(win_total['over_odds'], int)
    assert isinstance(win_total['under_odds'], int)
    logging.info(win_total)
