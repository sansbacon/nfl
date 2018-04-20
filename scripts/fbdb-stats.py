# footballdatabase-scraper
import json
import time

from bs4 import BeautifulSoup
from nfl.scrapers.scraper import FootballScraper


def _parse_page(content, scoring_format, fdb_d=None):
    '''
    Parses skill-position player page from footballdatabase
    
    Args:
        content(str): HTML
        scoring_format(str): std, ppr, etc.
    
    Returns:
        list: of dict
        
    '''
    results = []
    headers = ['fantasy_points', 'pass_att', 'pass_cmp', 'pass_yds', 'pass_td',
               'pass_int', 'pass_tpc', 'rush_att', 'rush_yds', 'rush_td', 'rush_tpc',
               'rec_rec', 'rec_yds', 'rec_td', 'rec_tpc', 'fumbles_lost', 'off_fumble_td']              
   
    soup = BeautifulSoup(content, 'lxml')
    # position, year are found in options that are selected
    pos, y, w = [opt['value'] for opt in soup.find_all('option', selected=True)][0:3]
    for tr in soup.select('table.statistics')[0]. \
                          find_all('tr', class_=['row0', 'row1']):
        tds = tr.find_all('td')        
        player = {'season_year': y, 'week': w, 
                  'source_player_position': pos,
                  'source': 'footballdatabase', 
                  'scoring_format': scoring_format}
        player['source_player_name'] = tds[0].find('span').text
        player['source_player_id'] = tr.find('a')['href']. \
                                     split('/')[2].split('-')[-1]
        player['source_player_team'] = tds[1].find('b').text
        for h, v in zip(headers, [td.text for td in tds[2:]]):
            player[h] = v
        if fdb_d:
            match = fdb_d.get(player['source_player_id'])
            if match:
                player['nflcom_player_id'] = match['nflcom_player_id']
                player['nflcom_team_id'] = match['nflcom_team_id'] 
        
        results.append(player)

    return results
    
def run():
    s = FootballScraper(delay=1.5, cache_name='fdb-scraper')
    results = []

    # pos=TE&yr=2010&wk=1&rules=2
    base_url = 'https://www.footballdb.com/fantasy-football/index.html?'
    rules = {1: 'footballdatabase_standard', 2: 'footballdatabase_ppr'}

    for yr in range(2010, 2017):
        for pos in ['QB', 'RB', 'WR', 'TE']:
            for w in range(1, 18):
                for rule in [1, 2]:
                    params = {'pos':pos, 'yr':yr, 'wk':w, 'rules':rule}
                    content = s.get(base_url, payload=params)
                    results.append(_parse_page(content, rules[rule]))
                    print('finished {} week {} {} {}'.format(yr, w, pos, rules[rule]))
    with open('fdb-skill.json', 'w') as f:
        json.dump([items for sublist in results 
                   for item in sublist], f)
        
if __name__ == '__main__':
    run()
