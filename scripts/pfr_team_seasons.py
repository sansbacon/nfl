'''
NOTE: html has tables hidden in comments
Scraper will either need to fix this or use headless browser
'''
import json
import pprint

from bs4 import BeautifulSoup
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from nfl.teams import long_to_code 
from nfl.db.nflpg import NFLPostgres
 
 
def run(): 
    db = NFLPostgres(user='nfldb', password='cft0911', database='nfldb')
    display = Display(visible=0, size=(800, 600))
    display.start()
    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    browser = webdriver.Firefox(capabilities=caps)
    url = 'http://www.pro-football-reference.com/years/{}/'

    overall_results = []

    for season_year in range(2010, 2016):
        print('starting {}'.format(season_year))
        browser.get(url.format(season_year))
        elem = browser.find_element_by_xpath("//*")
        content = elem.get_attribute("outerHTML")
        soup = BeautifulSoup(content, 'lxml')

        season_results = []
        teams = {}

        # passing
        print('starting {} passing'.format(season_year))
        t = soup.find('table', {'id': 'passing'})
        tbody = t.find('tbody')
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            team = tr.find('a').text
            teams[team] = {}
            for key in ['pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'pass_sacked', 'pass_sacked_yds', 'exp_pts_pass']:
                vals = [td for td in tds if td.get('data-stat') == key]
                if vals:
                    val = vals[0].text
                    if not val:
                        val = 0
                    teams[team][key] = val

        # rushing
        print('starting {} rushing'.format(season_year))
        t = soup.find('table', {'id': 'rushing'})
        tbody = t.find('tbody')
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            team = tr.find('a').text
            for key in ['rush_att', 'rush_yds', 'rush_td', 'fumbles', 'exp_pts_rush']:
                vals = [td for td in tds if td.get('data-stat') == key]
                if vals:
                    val = vals[0].text
                    if not val:
                        val = 0
                    teams[team][key] = val
            

        # team scoring
        print('starting {} scoring'.format(season_year))
        t = soup.find('table', {'id': 'team_scoring'})
        tbody = t.find('tbody')
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            team = tr.find('a').text
            for key in ['two_pt_md', 'two_pt_att', 'fgm', 'fga']:
                vals = [td for td in tds if td.get('data-stat') == key]
                if vals:
                    val = vals[0].text
                    if not val:
                        val = 0
                    teams[team][key] = val

        # drives
        print('starting {} drives'.format(season_year))
        t = soup.find('table', {'id': 'drives'})
        tbody = t.find('tbody')
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            team = tr.find('a').text
            for key in ['drives', 'play_count_tip', 'score_pct', 'turnover_pct', 'start_avg', 'time_avg', 'points_avg']:
                vals = [td for td in tds if td.get('data-stat') == key]
                if vals:
                    if key == 'time_avg':
                        val = vals[0].text
                        min_, sec_ = val.split(':')
                        teams[team][key] = int(min_) * 60 + int(sec_)      
                    elif key == 'start_avg':
                        teams[team][key] = vals[0].get('csk')      
                    else:
                        val = vals[0].text
                        if not val:
                            val = 0
                        teams[team][key] = val

        for k,v in teams.items():
            v['season_year'] = season_year
            v['team'] = long_to_code(k)
            print(v)
            season_results.append(v)    

        ## insert into db
        print('starting {} database'.format(season_year))
        db.insert_dicts(season_results, 'teamstats_offense_yearly')
        
        ## add to tally
        overall_results.append(season_results)

    return [item for sublist in overall_results for item in sublist]


if __name__ == '__main__':
    results = run()
    pprint.pprint(results)
    with open('results.json', 'wb') as outfile:
        json.dump(results, outfile)
