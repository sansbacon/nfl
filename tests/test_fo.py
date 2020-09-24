# -*- coding: utf-8 -*-

import logging
import pytest
import random

import nfl.fo as nf

logging.basicConfig(level=logging.INFO)

@pytest.fixture
def season():
    return random.choice(range(2009, 2017))


@pytest.fixture
def week():
    return random.choice(range(1, 18))


@pytest.fixture
def scraper():
    return nf.Scraper(cache_name='test-fo-scraper')

@pytest.fixture
def parser():
    return nf.Parser()


def test_ol(scraper, parser):
    season_year = 2018
    logging.info('starting %s', season_year)
    response = scraper.ol(season_year)
    assert 'OFFENSIVE LINES' in response.text
    ol = parser.ol(response)
    assert isinstance(ol, list)
    assert isinstance(random.choice(ol), dict)

    season_year = random.randint(2009, 2017)
    logging.info('starting %s', season_year)
    response = scraper.ol(season_year)
    assert 'OFFENSIVE LINES' in response.text
    ol = parser.ol(response)
    assert isinstance(ol, list)
    assert isinstance(random.choice(ol), dict)

    """
    def test_dl(self):
        content = scraper.dl()
        self.assertIsNotNone(content)
        parser.dl(content)
    
    
    def test_drive(self):
        content = scraper.drive()
        self.assertIsNotNone(content)
        parser.drive(content)    
    
    def test_qb(self):
        content = scraper.qb()
        self.assertIsNotNone(content)
        parser.qb(content)
    
    
    def test_rb(self):
        content = scraper.rb()
        self.assertIsNotNone(content)
        parser.rb(content)
    
    
    def test_snap_counts(self):
        content = scraper.snap_counts()
        self.assertIsNotNone(content)
        parser.snap_counts(content)
    
    
    def test_te(self):
        content = scraper.te()
        self.assertIsNotNone(content)
        parser.te(content)
    
    
    def test_team_defense(self):
        content = scraper.team_defense()
        self.assertIsNotNone(content)
        parser.team_defense(content)
    
    
    def test_team_efficiency(self):
        content = scraper.team_efficiency()
        self.assertIsNotNone(content)
        parser.team_efficiency(content)
    
    
    def test_team_offense(self):
        content = scraper.team_offense()
        self.assertIsNotNone(content)
        parser.team_offense(content)
    
    
    def test_wr(self):
        content = scraper.wr()
        self.assertIsNotNone(content)
        parser.wr(content)
    """

