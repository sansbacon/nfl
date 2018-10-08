# pipelines/nflscrapr.py

import logging

from psycopg2.extras import Json
from nfl.utility import getdb

logging.getLogger(__name__).addHandler(logging.NullHandler())


def game_table(l, week=None):
    '''
    Prepares data for insertion into nflscrapr.game table

    Args:
        l(list): of dict
        week(int): week of season
    Returns:
        list of dict

    '''
    gs = []
    c = {'GameID': 'game_id',
         'Season': 'season_year',
         'date': 'game_date',
         'home': 'home_team_id',
         'away': 'away_team_id',
         'homescore': 'home_score',
         'awayscore': 'away_score'}
    for g in l:
        d = {c.get(k): v for k,v in g.items() if k in c}
        if week:
            d['week'] = week
    return gs


def playerstats_weekly_table(l):
    '''
    Prepares data for insertion into nflscrapr.game table

    Args:
        l(list): of dict

    Returns:
        list of dict

    '''
    ps = []
    c = {'season': 'season_year',
         'week': 'week',
         'team': 'source_team_id',
         'name': 'source_player_name',
         'dkpts': 'draftkings_points',
         'fdpts': 'fanduel_points'}
    for g in l:
        d = {c.get(k): v for k,v in g.items() if k in c}
        d['data'] = Json(g)
    return ps


"""
create table nflscrapr.playerstats_weekly (
  playerstats_weekly_id serial primary key,
  season_year smallint NOT NULL,
  week smallint NOT NULL,
  source_player_id varchar NOT NULL,
  source_player_name varchar NOT NULL,
  source_team_id varchar NOT NULL,
  source_player_position varchar NOT NULL,
  fantasy_points_std numeric(4,2) DEFAULT NULL,
  fantasy_points_ppr numeric(4,2) DEFAULT NULL,
  draftkings_points numeric(4,2) DEFAULT NULL,
  fanduel_points numeric(4,2) DEFAULT NULL,
  data jsonb NOT NULL,
  UNIQUE (season_year, week, source_player_id)
);

create table nflscrapr.playerstats_yearly (
  playerstats_yearly_id serial primary key,
  season_year smallint NOT NULL,
  source_player_id varchar NOT NULL,
  source_team_id varchar NOT NULL,
  source_player_position varchar NOT NULL,
  fantasy_points_std numeric(4,2) DEFAULT NULL,
  fantasy_points_ppr numeric(4,2) DEFAULT NULL,
  draftkings_points numeric(4,2) DEFAULT NULL,
  fanduel_points numeric(4,2) DEFAULT NULL,
  data jsonb NOT NULL,
  UNIQUE (season_year, source_player_id)
);

create table nflscrapr.teamstats_weekly (
  teamstats_weekly_id serial primary key,
  season_year smallint NOT NULL,
  week smallint NOT NULL,
  source_team_id varchar NOT NULL,
  data jsonb NOT NULL,
  UNIQUE (season_year, week, source_team_id)
);

create table nflscrapr.teamstats_yearly (
  teamstats_yearly_id serial primary key,
  season_year smallint NOT NULL,
  source_team_id varchar NOT NULL,
  data jsonb NOT NULL,
  UNIQUE (season_year, source_team_id)
);

create table nflscrapr.play_by_play (
  play_by_play serial primary key,
  season_year smallint NOT NULL,
  week smallint NOT NULL,
  game_id varchar NOT NULL references nflscrapr.game(game_id),
  source_team_id varchar NOT NULL,
  drive smallint NOT NULL,
  quarter smallint NOT NULL,
  down smallint,
  data jsonb NOT NULL
)
"""

if __name__ == '__main__':
    pass