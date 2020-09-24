# -*- coding: utf-8 -*-

import logging
import pytest
import random

import nfl.espn as ne
from nfl.teams import espn_teams


logging.basicConfig(level=logging.INFO)


@pytest.fixture
def offset(pos):
    if pos == 'k':
        return 0
    elif pos in ['qb', 'te']:
        return random.choice([0, 40])
    else:
        return random.choice([0, 40, 80])


@pytest.fixture
def pos():
    return random.choice(['qb', 'rb', 'wr', 'te'])


@pytest.fixture
def season():
    return random.choice([2019])


@pytest.fixture
def team():
    return random.choice(espn_teams())


@pytest.fixture
def scraper():
    return ne.Scraper(cache_name='test-espn-scraper')


@pytest.fixture
def parser():
    return ne.Parser()


@pytest.fixture
def scraper():
    return ne.Scraper(cache_name='test-espn-scraper')


@pytest.fixture
def agent():
    return ne.Agent()


def test_adp(scraper, parser, season):
    content = scraper.adp(season)
    assert isinstance(content, dict)
    assert list(content.keys())[0] == 'players'
    players = parser.adp(content)
    logging.info(players)
    assert len(players) >= 1


def test_players_position(scraper, parser, pos):
    """Tests players_position"""
    content = scraper.players_position(pos)
    players = parser.players_position(content, pos)
    logging.info(players)
    assert isinstance(players, list)
    assert isinstance(random.choice(players), dict)
    keys = {'source', 'source_player_position', 'source_player_name', 'source_player_id',
            'source_team_name', 'source_team_code'}
    assert not keys - set(random.choice(players).keys())


def test_agent_adp(agent):
    data = agent.adp(2019)
    logging.info(data)
    assert isinstance(data, list)
    assert isinstance(data[0], dict)
    assert 'ppr_rank' in data[0].keys()


def test_team_rosters(scraper, parser):
    """Test team_rosters"""
    content = scraper.team_roster('CHI')
    data = parser.team_roster(content)
    assert isinstance(data, list)
    assert isinstance(data[0], dict)
    assert 'source_player_name' in data[0].keys()


