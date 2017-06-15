from copy import deepcopy
import json
import logging
import os
import pprint
import time

from configparser import ConfigParser
from pyvirtualdisplay import Display
from selenium import webdriver 

from nfl.db.nflpg import NFLPostgres


def _parse(result, season, week):
    '''
    Gets team and linescores from ESPN scoreboard page JSON
    '''
    games = []
    for event in result['events']:  
        try:
            comp = event['competitions'][0]
            g1 = {'game_id': comp['id'], 'game_date': comp['date'], 'season_year': season, 'week': week}
            g2 = deepcopy(g1)
            t1, t2 = comp['competitors']
            g1['team_code'] = t1['team']['abbreviation']
            g1['linescores'] = t1['linescores']
            games.append(g1)
            g2['team_code'] = t2['team']['abbreviation']
            g2['linescores'] = t2['linescores']
            games.append(g2)
        except:
            pass
    return games
        
def _scrape():
    results = []
    url = 'http://www.espn.com/nfl/scoreboard/_/year/{season}/seasontype/2/week/{week}'
    
    display = Display(visible=0, size=(800, 600))                             
    display.start()
    
    firefox_capabilities = webdriver.DesiredCapabilities.FIREFOX
    firefox_capabilities['marionette'] = True
    fp = webdriver.FirefoxProfile('/home/sansbacon/.mozilla/firefox/6h98gbaj.default/')
    driver = webdriver.Firefox(capabilities=firefox_capabilities)
    for season in range(2002, 2009):
        for week in range(1, 18):
            driver.get(url.format(season=season, week=week))
            js = driver.execute_script("return window.espn.scoreboardData")
            result = _parse(js, season, week)
            logging.info('finished {} week {}'.format(season, week))
            logging.info(pprint.pformat(result))
            results.append(result)    
            time.sleep(2)
    return results
        
def run():
    results = []
    fn = '/home/sansbacon/linescores.json'
    config = ConfigParser()
    configfn = os.path.join(os.path.expanduser('~'), '.pgcred')
    config.read(configfn)
    db = NFLPostgres(user=config['nfldb']['username'],
                  password=config['nfldb']['password'],
                  database=config['nfldb']['database'])

    if os.path.exists(fn):
        with open(fn, 'r') as infile:
            try:
                results = json.load(infile)
            except:
                pass

    if not results:
        results = _scrape()
        with open(fn, 'w') as outfile:
            json.dump(results, outfile)

    q = """UPDATE gamesmeta SET q1={q1}, q2={q2}, q3={q3}, q4={q4}, ot1={ot1}
           WHERE season_year={season} AND week={week} AND team_code='{team}'"""
        
    statements = []
    for r in [item for sublist in results for item in sublist]:
        g = {'season_year': r.get('season_year'), 
             'week': r.get('week')}
             
        team_code = r.get('team_code')
        if team_code == 'JAX':
            g['team_code'] = 'JAC'
        elif team_code == 'WSH':
            g['team_code'] = 'WAS'
        else:
            g['team_code'] = team_code
        
        ls = [ls.get('value') for ls in r.get('linescores')]
        if len(ls) == 4:
            ls.append('NULL')
        g['q1'], g['q2'], g['q3'], g['q4'], g['ot1'] = ls
        statements.append(q.format(q1=g['q1'], q2=g['q2'], q3=g['q3'], 
            q4=g['q4'], ot1=g['ot1'], season=g['season_year'], week=g['week'], 
            team=g['team_code']))

    db.batch_update(statements)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()
