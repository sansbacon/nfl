import logging
import pytest

import nfl.watson as nw


logging.basicConfig(level=logging.INFO)


@pytest.fixture
def season():
    return 2019


@pytest.fixture
def scraper():
    return nw.Scraper(cache_name='test-watson-scraper')


@pytest.fixture
def parser():
    return nw.Parser()


def test_players(scraper, parser, season):
    content = scraper.players(season_year=season)
    players = parser.players(content)
    assert len(players) > 0
    logging.info(players[0])


def test_weekly_projection(scraper, parser, season):
    pid = 13216
    content = scraper.weekly_projection(season_year=season, pid=pid)
    projection = parser.weekly_projection(content)
    assert isinstance(projection, list)
    assert isinstance(projection[0], dict)


