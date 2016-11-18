import copy
from functools import reduce
import glob
import json
from operator import or_
import os.path
import pprint

from bs4 import BeautifulSoup
import pandas as pd

def merge_tables(offense, passing, rushing):
    teams = copy.deepcopy(offense)
            
    for t in offense:
        p = passing.get(t)
               
        for k,v in p.items():
            teams[t][k] = v

            r = rushing.get(t)
                
        for k,v in r.items():
            teams[t][k] = v
                    
    return teams

def season_from_path(path):
    '''Extracts 4-digit season from path, each html file begins with season'''

    fn = os.path.split(path)[-1]
    return fn[0:4]

def team_offense(soup, season):
    '''
        scrapes table //*[@id="team_stats"]
        returns list of teams
    '''
    
    teams = {}
    offense = soup.find('table', {'id': 'team_stats'}).find('tbody')

    for tr in offense.findAll('tr'):
        team = {'season': season}
    
        for td in tr.findAll('td'):
            val = td.text
            
            # fix team name - has newline and extra space
            if '\n' in val:
                val = ' '.join(val.split('\n'))
                val = ' '.join(val.split())
                
            # column headers on page are duplicates (yds, td, etc.)    
            # data-stat attribute has accurate column name (rush_yds)
            team[td['data-stat']] = val
        
        k = team['team'] + "_" + season
        teams[k] = team

    return teams

def team_passing(soup, season):
    '''
        scrapes table //*[@id="passing"]
        returns list of teams
    '''
    
    teams = {}
    passing = soup.find('table', {'id': 'passing'}).find('tbody')

    for tr in passing.findAll('tr'):
        team = {'season': season}
    
        for td in tr.findAll('td'):
            val = td.text
            
            # fix team name - has newline and extra space
            if '\n' in val:
                val = ' '.join(val.split('\n'))
                val = ' '.join(val.split())
                
            # column headers on page are duplicates (yds, td, etc.)    
            # data-stat attribute has accurate column name (rush_yds)
            team[td['data-stat']] = val

        k = team['team'] + "_" + season
        teams[k] = team

    return teams

def team_rushing(soup, season):
    '''
        scrapes table //*[@id="rushing"]
        returns list of teams
    '''
    
    teams = {}
    rushing = soup.find('table', {'id': 'rushing'}).find('tbody')

    for tr in rushing.findAll('tr'):
        team = {'season': season}
    
        for td in tr.findAll('td'):
            val = td.text
            
            # fix team name - has newline and extra space
            if '\n' in val:
                val = ' '.join(val.split('\n'))
                val = ' '.join(val.split())
                
            # column headers on page are duplicates (yds, td, etc.)    
            # data-stat attribute has accurate column name (rush_yds)
            team[td['data-stat']] = val

        k = team['team'] + "_" + season
        teams[k] = team

    return teams

if __name__ == '__main__':

    teams = []

    for f in glob.glob('pfr-team/*.htm'):
    
        season = season_from_path(f)
    
        with open(f, 'r') as infile:
            html = infile.read()
            soup = BeautifulSoup(html, 'lxml')
            
            # 3 tables: team_offense, passing, rushing
            # need to combine given team & season
            offense = team_offense(soup, season)
            passing = team_passing(soup, season)
            rushing = team_rushing(soup, season)           
            
            season_teams = merge_tables(offense, passing, rushing)
            teams += season_teams.values()
               
    df = pd.DataFrame(teams)
    df.to_csv('~/pfr-teams.csv', index=False)
