import json
import logging
import os
from pprint import pformat
import random
import time

from bs4 import BeautifulSoup as BS
from configparser import ConfigParser

from nfl.db.nflpg import NFLPostgres
from nfl.scrapers.scraper import FootballScraper


def scrape_ot():
    results = []
    s = FootballScraper(cache_name='pfr-game-results')

    base_url = ('http://www.pro-football-reference.com/play-index/tgl_finder.cgi?'
                'request=1&match=game&year_min={year_min}&year_max={year_max}&'
                'game_type=R&game_num_min=0&game_num_max=99&week_num_min=0&'
                'week_num_max=99&temperature_gtlt=lt&overtime=Y&'
                'team_conf_id=All%20Conferences&'
                'team_div_id=All%20Divisions&opp_conf_id=All%20Conferences&'
                'opp_div_id=All%20Divisions&team_off_scheme=Any%20Scheme&'
                'team_def_align=Any%20Alignment&opp_off_scheme=Any%20Scheme&'
                'opp_def_align=Any%20Alignment&c1stat=choose&c1comp=gt&'
                'c2stat=choose&c2comp=gt&c3stat=choose&c3comp=gt&c4stat=choose&'
                'c4comp=gt&c5comp=choose&c5gtlt=lt&c6mult=1.0&c6comp=choose&'
                'order_by=game_date&order_by_asc=Y&offset={offset}')
               
    for offset in range(0, 300, 100):
        url = base_url.format(year_min=2002, year_max=2008, offset=offset)
        logging.debug(url)
        content = s.get(url)
        results.append(ot_results(content))
        logging.info('finished offset {}'.format(offset))
        time.sleep(random.random() * float(5))
    
    with open('/home/sansbacon/ot_results.json', 'w') as outfile:
        json.dump(results, outfile)
            
    logging.info(pformat(results))

def ot_results(content):
    '''
    Takes HTML of 100 rows of results, returns list of dict

    Args:
        content: HTML string

    Returns:
        list of results dict
    '''
    soup = BS(content, 'lxml')
    tb = soup.find('table', {'id': 'results'}).find('tbody')
    return [{td['data-stat']: td.text for td in tr.find_all('td')}
            for tr in tb.findAll('tr', {'class': None})]

def team_results(content):
    '''
    Takes HTML of 100 rows of results, returns list of dict

    Args:
        content: HTML string

    Returns:
        list of results dict
    '''
    soup = BS(content, 'lxml')
    tb = soup.find('table', {'id': 'results'}).find('tbody')
    return [{td['data-stat']: td.text for td in tr.find_all('td')}
            for tr in tb.findAll('tr', {'class': None})]

def scrape_team_results():
    results = []
    s = FootballScraper(cache_name='pfr-game-results')

    base_url = ('http://www.pro-football-reference.com/play-index/tgl_finder.cgi?'
                'request=1&match=game&year_min={year_min}&year_max={year_max}&'
                'game_type=R&game_num_min=0&game_num_max=99&week_num_min=0&'
                'week_num_max=99&temperature_gtlt=lt&team_conf_id=All%20Conferences&'
                'team_div_id=All%20Divisions&opp_conf_id=All%20Conferences&'
                'opp_div_id=All%20Divisions&team_off_scheme=Any%20Scheme&'
                'team_def_align=Any%20Alignment&opp_off_scheme=Any%20Scheme&'
                'opp_def_align=Any%20Alignment&c1stat=choose&c1comp=gt&'
                'c2stat=choose&c2comp=gt&c3stat=choose&c3comp=gt&c4stat=choose&'
                'c4comp=gt&c5comp=choose&c5gtlt=lt&c6mult=1.0&c6comp=choose&'
                'order_by=pass_td&offset={offset}')
                
    for offset in range(0, 3600, 100):
        url = base_url.format(year_min=2002, year_max=2008, offset=offset)
        logging.debug(url)
        content = s.get(url)
        results.append(team_results(content))
        logging.info('finished offset {}'.format(offset))
        time.sleep(random.random() * float(5))
    
    with open('/home/sansbacon/game_results.json', 'w') as outfile:
        json.dump(results, outfile)
            
    logging.info(pformat(results))

def _fix(r):
    f = {}
    if r['team'] == 'SFO':
        f['team_code'] = 'SF'
    elif r['team'] == 'TAM':
        f['team_code'] = 'TB'
    elif r['team'] == 'TAM':
        f['team_code'] = 'TB'
    elif r['team'] == 'SDG':
        f['team_code'] = 'SD'
    elif r['team'] == 'NWE':
        f['team_code'] = 'NE'
    elif r['team'] == 'KAN':
        f['team_code'] = 'KC'
    elif r['team'] == 'NOR':
        f['team_code'] = 'NO'
    elif r['team'] == 'GNB':
        f['team_code'] = 'GB'
    elif r['team'] == 'JAX':
        f['team_code'] = 'JAC'
    else:
        f['team_code'] = r['team']
    f['season_year'] = int(r['year_id'])
    f['week'] = int(r['week_num'])
    win, score = r['game_result'].split()
    f['is_win'] = win == 'W'
    f['s'] = int(score.split('-')[0])
    return f    

def _ot(r):
    f = {}
    if r['team'] == 'SFO':
        f['team_code'] = 'SF'
    elif r['team'] == 'TAM':
        f['team_code'] = 'TB'
    elif r['team'] == 'TAM':
        f['team_code'] = 'TB'
    elif r['team'] == 'SDG':
        f['team_code'] = 'SD'
    elif r['team'] == 'NWE':
        f['team_code'] = 'NE'
    elif r['team'] == 'KAN':
        f['team_code'] = 'KC'
    elif r['team'] == 'NOR':
        f['team_code'] = 'NO'
    elif r['team'] == 'GNB':
        f['team_code'] = 'GB'
    elif r['team'] == 'JAX':
        f['team_code'] = 'JAC'
    else:
        f['team_code'] = r['team']
    f['season_year'] = int(r['year_id'])
    f['week'] = int(r['week_num'])
    f['is_ot'] = True
    return f    

def _statement(i):
    q = """
    UPDATE gamesmeta SET is_win={is_win}, s={s}
    WHERE season_year={seas} AND week={week} AND team_code='{team_code}'
    """
    return q.format(is_win=i['is_win'], seas=i['season_year'], 
                    s=i['s'], week=i['week'], team_code=i['team_code'])

def _ot_statement(i):
    q = """
    UPDATE gamesmeta SET is_ot={is_ot}
    WHERE season_year={seas} AND week={week} AND team_code='{team_code}'
    """
    return q.format(is_ot=i['is_ot'], seas=i['season_year'], 
                    week=i['week'], team_code=i['team_code'])


def run():
    with open('/home/sansbacon/ot_results.json', 'r') as infile:
        items = [_ot(r) for r in 
                    [item for sublist in json.load(infile) for item in sublist]
                ]

    config = ConfigParser()
    configfn = os.path.join(os.path.expanduser('~'), '.pgcred')
    config.read(configfn)
    db = NFLPostgres(user=config['nfldb']['username'],
                  password=config['nfldb']['password'],
                  database=config['nfldb']['database'])

    db.batch_update([_ot_statement(item) for item in items])


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    run()
