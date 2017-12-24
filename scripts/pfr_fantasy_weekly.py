'''
pfr_fantasy_weekly
gets fantasy results for range of weeks and seasons
arguments:
    --seasonstart
    --seasonend
    --weekstart
    --weekend
    
usage:
    python pfr_fantasy_weekly.py --seasonstart=2017 --seasonend=2017 --weekstart=1 --weekend=17
'''

import json
import logging
import pprint

import click

from nfl.scrapers.pfr import PfrNFLScraper
from nfl.parsers.pfr import PfrNFLParser
from nfl.utility import getdb


def _fix_null(k, v):
    if k in ['season_year', 'source_player_id', 'source_player_position']:
        if v == "":
            return None
        else:
            return v
    else:
        return _fix_val(v)


def _fix_val(v):
    try:
        v = float(v)
    except:
        v = 0
    finally:
        return v


def _insp(db, vals):
    '''
    Inserts player into database
    
    Args:
        db:
        vals: 

    Returns:

    '''

    wanted = ['season_year', 'source_player_id', 'source_player_position',
              'draftkings_points', 'fanduel_points']

    for player in vals:
        p = {k: _fix_null(k, v) for k, v in player.items() if k in wanted}
        p['source'] = 'pfr'
        p['source_team_id'] = player['team']
        p['source_player_name'] = player['player']
        p['fantasy_points_std'] = _fix_val(player['fantasy_points'])
        p['fantasy_points_ppr'] = _fix_val(player['fantasy_points']) + _fix_val(player['rec'])
        p['week'] = player['week_num']
        db._insert_dict(p, 'extra_fantasy.playerstats_fantasy_weekly')
        logging.info('inserted into db: {}'.format(pprint.pformat(p)))

@click.command()
@click.option('--startseason')
@click.option('--endseason')
@click.option('--weekstart')
@click.option('--weekend')
@click.option('--savefile', default=None)
def run(startseason, endseason, weekstart, weekend, savefile):
    db = getdb()
    parser = PfrNFLParser()
    scraper = PfrNFLScraper(cache_name='pfr-fantasy', delay=1)

    all_players = []

    for seas in range(startseason, endseason+1):
        for week in range(weekstart, weekend):
            logging.info('starting {}'.format(week))
            for pos in ['QB', 'WR', 'TE', 'RB']:
                logging.info('starting {}'.format(pos))
                content = scraper.playerstats_fantasy_weekly(
                    season_year=seas, week=week, pos=pos)
                players = parser.playerstats_fantasy_weekly(
                    content, season_year=seas, pos=pos)
                all_players.append(players)
                logging.info('{} finished {} week {} offset 0'.format(seas, pos, week))
                _insp(db, players)

                if len(players) == 100:
                    try:
                        content = scraper.playerstats_fantasy_weekly(
                            season_year=seas, week=week, pos=pos, offset=100)
                        players = parser.playerstats_fantasy_weekly(
                            content, season_year=seas, pos=pos)
                        all_players.append(players)
                        logging.info('finished {} week {} offset 100'.format(pos, week))
                        _insp(players)

                    except:
                        pass
    if savefile:
        with open('/home/sansbacon/fantasy{}-{}_{}-{}.json'.format(startseason, endseason, weekend), 'w') as outfile:
            json.dump(all_players, outfile)

    # now update references to nflcom_player_id
    sql = """
        update extra_fantasy.playerstats_fantasy_weekly
        set nflcom_player_id = sq.nflcom_player_id
        from (
            select * from extra_misc.player_xref where source = 'pfr'
        ) sq
        where playerstats_fantasy_weekly.source_player_id = sq.source_player_id
    """
    db.execute(sql)

    # update references to nflcom_team_id
    sql = """
        update extra_fantasy.playerstats_fantasy_weekly
        set nflcom_team_id = sq.nflcom_team_id
        from (
            select * from extra_misc.team_xref where source = 'pfr'
        ) sq
        where playerstats_fantasy_weekly.source_team_id = sq.source_team_id
    """
    db.execute(sql)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()