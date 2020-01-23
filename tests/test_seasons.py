# -*- coding: utf-8 -*-
# tests/test_dates.py
# tests for nfl.dates module

import datetime
import logging
import random
import pytest

import nfl.seasons as ns


logging.basicConfig(level=logging.INFO)


@pytest.fixture
def seas():
    return random.choice(range(2009, 2020))


@pytest.fixture
def week():
    return random.choice(range(1, 18))


def test_all_seasons(seas, week):
    """Tests all seasons"""
    allseas = ns.all_seasons()
    assert isinstance(allseas, dict)
    assert seas in allseas


def test_current_season_year(seas, week):
    y = ns.current_season_year()
    assert y <= datetime.datetime.now().year


def test_fantasylabs_week(seas, week):
    fl = ns.fantasylabs_week(seas, week)
    logging.info(fl)
    assert '-' in fl


def test_get_season(seas, week):
    s = ns.get_season(seas)
    assert isinstance(s, dict)


def test_season_week(seas, week):
    d = datetime.datetime(2018, 10, 13).date()
    sw = ns.season_week(d)
    logging.info(sw)
    assert sw['season'] == 2018
    assert sw['week'] == 5


def test_week_end(seas, week):
    """Tests week_end"""
    assert isinstance(ns.week_end(seas, week), datetime.date)

    y = 2018
    w = 5
    assert ns.week_end(y, w) < datetime.datetime.now().date()


def test_week_start(seas, week):
    """tests week_start"""
    assert isinstance(ns.week_start(seas, week), datetime.date)
    y = 2018
    w = 5
    assert ns.week_start(y, w) < datetime.datetime.now().date()
