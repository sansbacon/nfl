# update_gamesmeta.py
# adds gsis_id, scores, winner to gamesmeta table

import json
import logging
import os
import sys

from configparser import ConfigParser

from nfl.db.nflpg import NFLPostgres
from nfl.pipelines.nflcom import gamesmeta_table


def run():
    config = ConfigParser()
    configfn = os.path.join(os.path.expanduser('~'), '.pgcred')
    config.read(configfn)
    db = NFLPostgres(user=config['nfldb']['username'],
                  password=config['nfldb']['password'],
                  database=config['nfldb']['database'])

    q = """
    update gamesmeta set gsis_id = '{gsis_id}', is_home = {is_home}
    where season_year = {season_year} AND week = {week} AND team_code = '{team_code}';
    """

    with open('/home/sansbacon/gamesmeta.json', 'r') as infile:
        statements = [
            q.format(gsis_id=g['gsis_id'], is_home=g['is_home'], season_year=g['season_year'], week = g['week'], team_code=g['team_code'])
            for g in gamesmeta_table(json.load(infile))
        ]

    if statements:
        db.batch_update(statements)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    run()
