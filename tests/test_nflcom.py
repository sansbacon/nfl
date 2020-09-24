# -*- coding: utf-8 -*-

import logging
import pytest
import random
from string import ascii_uppercase

from requests import Response

import nfl.nflcom as nc

logging.basicConfig(level=logging.INFO)


@pytest.fixture
def gsis_id():
    vals = ["2015090365", "2009101809", "2013120103", "2016100904", "2015092712",
            "2009100410", "2014080705", "2012092311", "2011112800", "2012120906",
            "2011103009", "2010091906", "2013112407", "2013082404", "2014110902",
            "2012101100", "2016010307", "2009101111", "2014091402", "2016090151"]
    return random.choice(vals)


@pytest.fixture
def letter():
    x = None
    while not x:
        l = random.choice(ascii_uppercase)
        if l not in ['x', 'y', 'z', 'v']:
            x = l
    return x


@pytest.fixture
def profile_id():
    vals = ['2495143']
    return random.choice(vals)


@pytest.fixture
def season():
    return random.choice(range(2009, 2017))


@pytest.fixture
def week():
    return random.choice(range(1, 18))


@pytest.fixture
def scraper():
    return nc.Scraper(cache_name='test-nfldotcom-scraper')
        

@pytest.fixture
def parser():
    return nc.Parser()


@pytest.fixture
def agent(scraper, parser):
    return nc.Agent(scraper, parser)


def test_game(scraper, parser, gsis_id):
    content = scraper.game(gsis_id)
    assert content is not None
    game = parser.game_page(content)
    assert game is not None


def test_gamebook(scraper):
    content = scraper.gamebook(2016, 1, 56905)
    assert content is not None
    assert 'Gamebook' in content


def test_injuries(scraper, parser, season, week):
    content = scraper.injuries(week)
    assert content is not None
    injuries = parser.injuries(content, season, week)
    assert injuries is not None


def test_ol(scraper, parser, season):
    content = scraper.ol(season)
    assert content is not None
    ol = parser.ol(content)
    assert isinstance(ol, list)


def test_player_profile(scraper, parser):
    profile_path = 'andydalton/2495143'
    player_id, profile_id = profile_path.split('/')
    content = scraper.player_profile(profile_path=profile_path)
    assert profile_path in content
    player = parser.player_page(content, profile_id)
    assert isinstance(player, dict)


def test_player_search_name(scraper, parser):
    pname = 'Dalton, Andy'
    profile_path = 'andydalton/2495143'
    pid, prid = profile_path.split('/')
    search_result = scraper.player_search_name(pname)
    name, player_id, profile_id = parser.player_search_name(search_result)[0]
    assert name == pname
    assert pid == player_id
    assert prid == profile_id


def test_player_search_web(scraper, parser):
    name = 'Andy Dalton'
    profile_path = 'andydalton/2495143'
    player_id, profile_id = profile_path.split('/')
    search_result = scraper.player_search_web(name)
    assert profile_path in search_result
    content = scraper.get(search_result)
    player = parser.player_page(content, profile_id)
    assert isinstance(player, dict)


def test_players(scraper, parser, letter):
    response = scraper.players(letter)
    assert isinstance(response, Response)
    players = parser.players(response)
    assert isinstance(players, list)


def test_schedule_week(scraper, parser, season, week):
    assert scraper.schedule_week(season, week) is not None


def test_score_week(scraper, parser, season, week):
    assert scraper.score_week(season, week) is not None

