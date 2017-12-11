# coding: utf-8
'''
Parses dk salaries file
Gets ffnerd projections
Compares salary rank to projection rank by position

todo: there are 2 michael thomas, will be more reliable if match IDs
'''

import logging
import os
import random

import pandas as pd

from nfl.parsers.ffnerd import FFNerdNFLParser
from nfl.parsers.fantasypros import FantasyProsNFLParser
from nfl.scrapers.ffnerd import FFNerdNFLScraper
from nfl.scrapers.fantasypros import FantasyProsNFLScraper


def dkplayers(contestfn):
    '''
    Parses dkcontest file, which has player salaries
    Args:
        contestfn: 

    Returns:

    '''
    players = []
    contestheaders = ['position', 'name_ID', 'name', 'ID', 'salary', 'game', 'team']
    with open(contestfn, 'r') as infile:
        for line in infile.readlines()[7:]:
            cells = [c.strip() for c in line.split(',')[14:] if len(c) >= 2]
            players.append(dict(zip(contestheaders, cells)))

    return {'{}_{}'.format(p.get('name'), p.get('position')): p for p in players}
        
def ffnproj(scraper, week, pos):
    '''
    Gets positional projection from ffnerd
    
    Args:
        scraper: 
        week: 
        pos: 

    Returns:

    '''
    content = scraper.weekly_rankings(week=week, pos=pos)
    parser = FFNerdNFLParser()
    players = parser.weekly_rankings(content)
    logging.info(random.choice(players))
    return players

def fpranks(scraper, week, pos, fmt='ppr'):
    '''
    
    Returns:

    '''
    parser = FantasyProsNFLParser()
    return parser.weekly_rankings(scraper.weekly_rankings(pos, fmt, week))
    

def xref(dkp, proj):
    '''
    Adds ffnerd projections to dk salaries
    Args:
        dkp: 
        proj: 

    Returns:

    '''
    for p in proj:
        key = '{}_{}'.format(p.get('name'), p.get('source_player_position'))
        if key in dkp:
            ppr_proj = p.get('ppr')
            if ppr_proj:
                dkp[key]['projection'] = float(p['ppr'])
            else:
                dkp[key]['projection'] = 0
    return dkp

def posdframe(dkp, pos):
    '''
    Creates pandas dataframe of qb, adds and removes columns
    
    Args:
        dkp: 

    Returns:

    '''
    vals = [v for k,v in dkp.items() if pos in k]
    df = pd.DataFrame([v for v in vals if 'projection' in v])
    pd.to_numeric(df.projection)

    # calculate max value
    max = df.projection.max()
    thresh = float(max/3)
    posdf = df.where(df['projection'] >= thresh).dropna()
    del posdf['game']
    del posdf['name_ID']
    posdf.salary = posdf.salary.apply(pd.to_numeric)
    posdf['salrank'] = posdf['salary'].rank(ascending=False)
    posdf['projrank'] = posdf['projection'].rank(ascending=False)
    posdf['diff'] = posdf.salrank - posdf.projrank
    return posdf

def run():
    logging.basicConfig(level=logging.ERROR)
    contestfn = os.path.join(os.path.expanduser('~'), 'Downloads/DKEntries (5).csv')
    savefn = os.path.join(os.path.expanduser('~'), 'dkranks.pkl')
    ffnscraper = FFNerdNFLScraper(api_key='8x3g9y245w6a')
    dkp = dkplayers(contestfn)
    dfs = []

    for pos in ['QB', 'RB', 'WR', 'TE']:
        logging.info('starting {}'.format(pos))
        proj = ffnproj(ffnscraper, 14, pos)
        dkp = xref(dkp, proj)
        dfs.append(posdframe(dkp, pos))

    df = pd.concat(dfs, ignore_index = True)
    logging.info(df.nlargest(25, 'diff'))
    df.to_pickle(savefn)

if __name__ == '__main__':
    run()
