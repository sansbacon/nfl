# -*- coding: utf-8 -*-
# tests/test_teams.py
# tests for nfl.teams module

import logging
import random
import pytest

import nfl.teams as nt


logging.basicConfig(level=logging.INFO)


def test_get_team_code():
    """Test get team code"""
    assert nt.get_team_code('rav') == 'BAL'
    assert nt.get_team_code('RAV') == 'BAL'
    assert nt.get_team_code('bal') == 'BAL'
    assert nt.get_team_code('ravens') == 'BAL'
    with pytest.raises(ValueError):
        nt.get_team_code('xanadu')

