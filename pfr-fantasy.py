import os
import pickle
import re

from bs4 import BeautifulSoup
import requests

url = 'http://www.pro-football-reference.com/years/{0}/fantasy.htm'

def parse_season(content, season):
    soup = BeautifulSoup(content)

    players = []

    headers = [
        'rk', 'player', 'team', 'age', 'g', 'gs', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'rush_att', 'rush_yds', 'rush_yds_per_att',
        'rush_td', 'targets', 'rec', 'rec_yds', 'rec_yds_per_rec', 'rec_td', 'fantasy_pos', 'fantasy_points', 'draftkings_points', 'fanduel_points', 'vbd', 'fantasy_rank_pos', 'fantasy_rank_overall'
    ]

    t = soup.find('table', {'id': 'fantasy'})
    body = t.find('tbody')

    for row in body.findAll('tr'):
        values = [cell.text for cell in row.findAll('td')]

        # filter out header rows
        if 'Receiving' in values or 'Y/A' in values:
            continue
            
        player = (dict(zip(headers, values)))
        player['Season'] = season

        # fix *+ in name
        # add playerid
        link = row.find('a', href=re.compile(r'/players/'))

        if link:
            player['Player'] =  link.text
            pid = link['href'].split('/')[-1]
            player['Id'] = pid[:-4]

        else:
            name = player.get('Player')
            if name:
                name.replace('*', '')
                name.replace('*', '+')
                player['Player'] = name

        players.append(player)

    return players

if __name__ == '__main__':
    all_players = []
    for season in range(2001, 2016):
        print('getting {}'.format(season))
        fn = 'pfr_fantasy_{0}.html'.format(season)

        if os.path.isfile(fn):
            with open(fn, 'r') as infile:
                content = infile.read()
            
        else:
            r = requests.get(url.format(season))
                    
            with open(fn, 'w') as outfile:
                outfile.write(r.text)

            content = r.content

        all_players += parse_season(content, season)

    with open('fixed_pfr_fantasy.pkl', 'wb') as pklfile:
        pickle.dump(all_players, pklfile)
