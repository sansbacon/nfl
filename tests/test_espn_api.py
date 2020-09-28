# -*- coding: utf-8 -*-
import json
import logging
from pathlib import Path
import pytest
import random


import nfl.espn_api as ne


@pytest.mark.skip
def test_scraper_weekly_projections():
    s = ne.Scraper(season=2020, cache_name="test-espn-api-scraper")
    proj = s.weekly_projections_by_team(week=3, team_id=22)
    assert isinstance(proj, dict)


def test_espn_team():
    assert ne.espn_team(team_code="PHI") == 21
    assert ne.espn_team(team_code="Eagles") == 21
    assert ne.espn_team(team_id=21) == "PHI"


def test_parser_weekly_projections(tprint):
    p = ne.Parser(season=2020)
    fn = Path.home() / "nfl" / "tests" / "espn_api_weekly_team_projection.json"
    with fn.open("r") as f:
        content = json.load(f)
    proj = p.weekly_projections_by_team(content, 3)
    assert isinstance(proj, list)
    assert isinstance(proj[0], dict)
