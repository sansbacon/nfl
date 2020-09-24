# -*- coding: utf-8 -*-
import logging
import pytest
import random
from string import ascii_uppercase

import nfl.pfr as pfr
import re


logging.basicConfig(level=logging.INFO)


@pytest.fixture
def last_initial():
    return random.choice(ascii_uppercase)

@pytest.fixture
def offset():
    return random.choice(range(0, 100, 200))

@pytest.fixture
def player():
    ids = ['PalmCa00', 'BreeDr00', 'RodgAa00', 'CousKi00', 'StafMa00', 'RivePh00',
           'TaylTy00', 'CarrDe02', 'SmitAl03', 'BrowAn04', 'DaltAn00', 'FreeDe00',
           'JoneJu02', 'RyanMa00', 'RoetBe00', 'PeteAd01', 'MarsBr00']
    return random.choice(ids)

@pytest.fixture
def seas():
    return random.choice(range(2002, 2017))

@pytest.fixture
def week():
    return random.choice(range(1, 18))


@pytest.fixture
def scraper():
    return pfr.Scraper(cache_name='pfr-plays-query')

@pytest.fixture
def parser():
    return pfr.Parser()


def test_player_game_finder(scraper, parser):
    params = {'opp_id': 'car', 'pos[]': 'RB'}
    content = scraper.player_game_finder(params)
    players = parser.player_game_finder(content)
    assert len(players) > 0, 'should have some players'


def test_team_plays_query(scraper, parser):
    content = scraper.team_plays_query(season_start=2016, season_end=2016, offset=0)
    assert '404 error' not in content
    assert re.search(r'html', content)


def test_draft(scraper, parser, seas):
    content = scraper.draft(seas)
    assert '404 error' not in content
    players = parser.draft(content, seas)
    assert players is not None
    player = random.choice(players)
    assert 'draft_year' in player.keys()


def test_players(scraper, parser, last_initial):
    content = scraper.players(last_initial)
    assert len(parser.players(content)) > 0
    assert '404 error' not in content


def test_player_fantasy_season(scraper, parser, seas, player):
    content = scraper.player_fantasy_season(seas, player)
    assert parser.player_fantasy_season(content) is not None
    assert '404 error' not in content


def test_playerstats_fantasy_weekly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_fantasy_weekly(seas, week, offset)
    assert content is not None
    assert '404 error' not in content


def test_playerstats_fantasy_yearly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_fantasy_yearly(seas, offset)
    assert content is not None
    assert '404 error' not in content


def test_player_fantasy_year(scraper, parser, seas, player):
    content = scraper.player_fantasy_season(seas, player)
    assert parser.player_fantasy_season(content) is not None
    assert '404 error' not in content


def test_playerstats_offense_weekly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_offense_weekly(seas, week, offset)
    assert len(parser.playerstats_offense_weekly(content)) > 0
    assert '404 error' not in content


def test_playerstats_offense_yearly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_offense_yearly(seas, offset)
    assert len(parser.playerstats_offense_yearly(content)) > 0
    assert '404 error' not in content


def test_playerstats_passing_weekly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_passing_weekly(seas, week, offset)
    assert len(parser.playerstats_offense_weekly(content)) > 0
    assert '404 error' not in content


def test_playerstats_passing_yearly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_passing_yearly(seas, offset)
    assert len(parser.playerstats_passing_yearly(content)) > 0
    assert '404 error' not in content


def test_playerstats_receiving_weekly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_receiving_weekly(seas, week, offset)
    assert len(parser.playerstats_offense_weekly(content)) > 0
    assert '404 error' not in content


def test_playerstats_receiving_yearly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_receiving_yearly(seas, offset)
    assert len(parser.playerstats_receiving_yearly(content)) > 0
    assert '404 error' not in content


def test_playerstats_rushing_weekly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_rushing_weekly(seas, week, offset)
    assert len(parser.playerstats_offense_weekly(content)) > 0
    assert '404 error' not in content


def test_playerstats_rushing_yearly(scraper, parser, seas, week, offset):
    content = scraper.playerstats_rushing_yearly(seas, offset)
    assert len(parser.playerstats_rushing_yearly(content)) > 0
    assert '404 error' not in content


def test_team_passing_weekly(scraper, parser, seas, week, offset):
    season = seas
    content = scraper.team_passing_weekly(season, season, week)
    assert len(parser.team_offense_weekly(content)) > 0
    assert '404 error' not in content


def test_team_defense_yearly(scraper, parser, seas, week, offset):
    sy = seas
    content = scraper.team_defense_yearly(seas)
    assert len(parser.team_defense_yearly(content, seas)) > 0
    assert '404 error' not in content


def test_team_defense_weekly(scraper, parser, seas, week, offset):
    season = seas
    content = scraper.team_defense_weekly(season, season, week)
    assert len(parser.team_defense_weekly(content)) > 0
    assert '404 error' not in content


def test_team_offense_weekly(scraper, parser, seas, week, offset):
    season = seas
    content = scraper.team_offense_weekly(season, season, week)
    assert len(parser.team_offense_weekly(content)) > 0
    assert '404 error' not in content
