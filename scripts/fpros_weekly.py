'''
fpros_weekly
gets fpros rankings for range of weeks
arguments:
    --fmt
    --weekstart
    --weekend
    
usage:
    python fpros_weekly.py --fmt='ppr' --weekstart=1 --weekend=17
'''

import logging
import click

from nfl.parsers.fantasypros import FantasyProsNFLParser
from nfl.scrapers.fantasypros import FantasyProsNFLScraper
from nfl.seasons import current_season_year
from nfl.utility import getdb


def _fix_null(k, v, wanted=['season_year', 'source_player_id', 'source_player_position']):
    if k in wanted:
        if v == '':
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

    #wanted = ['source', 'source_player_id', 'source_player_name', 'source_last_updated',
    #          'source_player_position', 'season_year', 'week', 'source_player_team',
    #          'source_player_opp', 'rank', 'avg', 'best', 'worst', 'stdev',]

    numeric_fields = ['avg', 'best', 'rank', 'stdev', 'worst']

    for player in vals:
        p = {}
        for k,v in player.items():
            if k == 'source_player_posrk':
                continue
            elif k in numeric_fields:
                p[k] = _fix_val(v)
            elif (v == '' or v == '-'):
                p[k] = None
            else:
                p[k] = v
        db._insert_dict(p, 'extra_fantasy.weekly_rankings')


@click.command()
@click.option('--weekstart')
@click.option('--weekend')
@click.option('--fmt', default='ppr')
@click.option('--position', default='all')
def run(fmt, weekstart, weekend, position):
    '''
    Gets fantasypros ranks for range of weeks and positions    
    Args:
        fmt: 
        weekstart: 
        weekend: 
        position: 

    Returns:
        list, list
    '''
    db = getdb()
    parser = FantasyProsNFLParser()
    scraper = FantasyProsNFLScraper(cache_name='fpros', delay=1)

    # can pass pipe-delimited list of positions
    if position == 'all':
        positions = ['qb', 'wr', 'te', 'rb', 'flex', 'dst', 'k']
    elif '|' in position:
        positions = position.split('|')
    else:
        positions = [position]

    # returns players and flex
    players = []
    flex = []

    # loop through weeks and positions
    for week in range(int(weekstart), int(weekend)+1):
        logging.info('starting {}'.format(week))
        for pos in positions:
            logging.info('starting {}'.format(pos))
            content = scraper.weekly_rankings(pos, fmt, week)
            ranks = parser.weekly_rankings(content=content, fmt=fmt, pos=pos,
                                           season_year=current_season_year(), week=week)
            if pos in ['flex', 'FLEX']:
                flex = ranks
            else:
                players += ranks
            logging.info('{} finished week {}'.format(pos, week))
            _insp(db, ranks)

    return players, flex


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()