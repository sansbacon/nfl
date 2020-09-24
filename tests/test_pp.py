"""

tests/test_pp.py

"""

import logging
import pytest
import random

from nflmisc.nflpg import getdb
from nfl.pp import Scraper, Parser, Agent, Xref
from namematcher import Site


logging.basicConfig(level=logging.INFO)


@pytest.fixture
def scraper():
    return Scraper()

@pytest.fixture
def parser():
    return Parser()


def test_player_page(scraper, parser):
    content = scraper.player_page('TT-0500')
    assert content is not None
    data = content['data']['Player']
    assert isinstance(data, dict)
    mh = parser.player_medical_history(data)
    assert isinstance(mh, list)
    gl = parser.player_game_logs(data)
    assert isinstance(gl, list)


def test_players(scraper):
    data = scraper.players()
    assert data is not None
    assert isinstance(data, dict)


def test_rankings(scraper):
    data = scraper.rankings()
    assert data is not None
    logging.info(data)
    assert isinstance(data, dict)

