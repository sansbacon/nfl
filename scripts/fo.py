import json
import pprint
import time

from bs4 import BeautifulSoup
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from nfl.db.nflpg import NFLPostgres
 
 
def run(): 
    results = []
    db = NFLPostgres(user='nfldb', password='cft0911', database='nfldb')
    display = Display(visible=0, size=(800, 600))
    display.start()
    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    ffprofile = webdriver.FirefoxProfile('/home/sansbacon/.mozilla/firefox/6h98gbaj.default')
    browser = webdriver.Firefox(capabilities=caps, firefox_profile=ffprofile)
    
    url = 'http://www.footballoutsiders.com/premium/weekTeamSeasonDvoa.php?od=O&year=2016&team=ARI&week={}'
    
    for week in range(1, 18):
        browser.get(url.format(week))
        elem = browser.find_element_by_xpath("//*")
        content = elem.get_attribute("outerHTML")
        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'dataTable'})
        thead = t.find('thead')
        headers = [th.text for th in thead.find_all('th')]
        for tr in t.find('tbody').find_all('tr'):
            result = dict(zip(headers, [td.text for td in tr.find_all('td')]))
            result['season_year'] = 2016
            result['week'] = week
            results.append(result)
        time.sleep(1)
            
    with open('results.json', 'w') as outfile:
        json.dump(results, outfile)

    pprint.pprint(results)

if __name__ == '__main__':
    run()
