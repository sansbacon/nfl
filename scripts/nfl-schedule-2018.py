# nfl-schedule-2018.py
# scrapes nfl schedule
# can list by weeks by position

import arrow
import pandas as pd
import requests
from requests_html import HTMLSession

s = HTMLSession()
url = 'http://www.nfl.com/schedules/2018/REG{}'

# scrape schedule from NFL.com
schedule = []
url = 'http://www.nfl.com/schedules/2018/REG{}'
for w in range(1,18):
    r = s.get(url.format(w))
    for div in r.html.find('div.schedules-list-content'):
        g = {'season_year': 2018, 'week': w}
        g['gsis_id'] = div.attrs.get('data-gameid')
        g['home_team'] = div.attrs.get('data-home-abbr')
        g['away_team'] = div.attrs.get('data-away-abbr')
        tm = div.attrs.get('data-localtime')
        g['start_time'] = arrow.get(g['gsis_id'][0:8] + ' ' + tm, 'YYYYMMDD HH:mm:ss').datetime
        schedule.append(g)    
        print('finished week {}, {} games'.format(w, len([gm for gm in schedule if gm['week'] == w])))
        
# make teams meta
# that is, have two rows per game (one per team)
# makes it much easier to determine bye weeks
tm = []
for gm in schedule:
    tm.append({'gsis_id': gm['gsis_id'],
          'season_year': gm['season_year'],
          'week': gm['week'],
          'team': gm['home_team'],
          'opp': gm['away_team'],
          'start_time': gm['start_time']})
    tm.append({'gsis_id': gm['gsis_id'], 
               'season_year': gm['season_year'],
               'week': gm['week'],
               'team': gm['away_team'],
               'opp': gm['home_team'],
               'start_time': gm['start_time']})

# pivot and then unstack gets True/False for whether week is missing               
# you'll get the bye weeks when column 0 is True
df = pd.DataFrame(tm)
pv = df.pivot(index='team', columns='week', values='opp')
pv2 = pv.isnull().unstack().reset_index()
pv3 = pv2[pv2[0] != False][['week', 'team']]

# now select players from DRAFT to match bye weeks to players
q = """
  select first_name || ' ' || last_name as player, 
    team, drafts_adp as adp
  from extra_dfs_draft.adp2018
  where "position" = '{}' AND drafts_adp > 0 AND team != 'FA'
"""
qbs = db.select_dict(q.format('QB')

# have to fix JAC/JAX
byes = {row['team']: row['week'] for idx, row in pv3.iterrows()} 
byes['JAX'] = 9

# add bye week to player
for idx, qb in enumerate(qbs):
    qbs[idx]['bye_week'] = byes.get(qb['team'])
    
# then loop through weeks, add players who have bye that week
qb_byes = {}
for week in range(1,13):
    matches = [qb['player'] for qb in qbs if qb['bye_week'] == week]
    if matches:
        qb_byes[week] = matches

# print out the results        
for k,v in qb_byes.items():
    print('  ', k, ': ', ', '.join(v))

# can also do for other positions
def bye_week_by_position(db, pos, team_byes, adp=0, exclude='FA'):
    '''
    Gets bye weeks for players by position
    
    Args:
        db (NFLPostgres): db instance
        pos (str): 'QB', etc.
        team_byes (dict): key is 'ATL', etc. and value is week
        adp (int): minimum adp, default 0
        exclude (str): team to exclude, default 'FA' (mostly rookies)
    
    Returns:
        dict: key is week, value is list of player names
    
    '''
    q = """
      select first_name || ' ' || last_name as player, 
        team, drafts_adp as adp
      from extra_dfs_draft.adp2018
      where "position" = '{}' AND drafts_adp > {} AND team != '{}'
    """        
    players = db.select_dict(q.format(pos, adp, exclude))
    for idx, p in enumerate(players):
        players[idx]['bye_week'] = byes.get(p['team'])
    
    posbyes = {}
    for week in range(1,13):
        matches = [p['player'] for p in players if p['bye_week'] == week]
        if matches:
            posbyes[week] = matches
            
    return posbyes
