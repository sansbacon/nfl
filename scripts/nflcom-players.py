from nfl.scrapers.scraper import FootballScraper
from nfl.parsers.nflcom import NFLComParser

results = []
s = FootballScraper()
parser = NFLComParser()

# get players from player
q = """select profile_id::varchar, profile_url from player where profile_id IS NOT NULL"""
ids = {p.get('profile_id'): p.get('profile_url') for p in db.select_dict(q)}

# now scrape nfl website
teamcodes = []
teamplayers_url = 'http://www.nfl.com/players/search?category=team&playerType=current'
team_url = 'http://www.nfl.com/players/search?category=team&playerType=current&d-447263-p={}&filter={}'

content = s.get(teamplayers_url)
soup = BeautifulSoup(content, 'lxml')

# get all of the team codes
# exclude codes not specific to one team
for a in soup.find_all('a', {'href': re.compile(r'/players/search\?category=team')}):
    try:
        link = a['href']
        team_code = link.split('filter=')[-1]
        team_code = str(team_code.split('&')[0])
        if 'search' in team_code:
            pass
        else:
            teamcodes.append(team_code)
    except:
        pass

# loop through teamcodes
for tc in teamcodes:
    teamplayers = []
    
    # need 2 pages to get all of the players on a team
    for offset in [1,2]:
        contenti = s.get(team_url.format(offset, tc))
        soupi = BeautifulSoup(contenti, 'lxml')
        for a in soupi.find_all('a', {'href': re.compile(r'/player/.*?/profile')}):
            profile_id = a['href'].split('/')[-2]
            if profile_id in ids:
                continue
            else:
                url = 'http://www.nfl.com' + a['href']
                profile_content = s.get(url)
                soupj = BeautifulSoup(profile_content, 'lxml')
                player = {}

                for c in soupj.find_all(string=lambda text: isinstance(text, Comment)):
                    if 'GSIS' in c:
                        parts = [part.strip() for part in c.split('\n')]
                        esb_id = parts[2].split(':')[-1].strip()
                        gsis_id = parts[3].split(':')[-1].strip()
                        player['player_id'] = gsis_id
                        player['profile_id'] = profile_id
                        break

                paras = soupj.find('div', {'id': 'player-profile'}).find_all('p')

                if len(paras) >= 6:
                    # paras[0]: name and number
                    logging.info(paras[0])
                    spans = paras[0].find_all('span')
                    name = spans[0].text.strip()
                    player['full_name'] = name
                    player['first_name'], player['last_name'] = first_last_pair(name)
                    number, pos = spans[1].text.split()
                    player['number'] = number.replace('#', '')
                    player['position'] = pos

                    # paras[1]: team
                    logging.info(paras[1])
                    player['team'] = paras[1].find('a')['href'].split('=')[-1]

                    # paras[2]: height, weight, age
                    logging.info(paras[2])
                    parts = paras[2].text.split()
                    player[parts[0].lower()] = parts[1]
                    player[parts[2].lower()] = parts[3]
                    player[parts[4].lower()] = parts[5]

                    # birthdate
                    parts = paras[3].text.split()
                    player['birthdate'] = parts[1].strip()

                    # college
                    parts = paras[4].text.split()
                    player['college'] = parts[1].strip()

                    # years pro
                    parts = paras[5].text.split()
                    ordinal = parts[1].strip()
                    player['years_pro'] = ''.join(ch for ch in ordinal if ch.isdigit())

                    # status
                    player['status'] = 'Active'
                    
                    print(player)
