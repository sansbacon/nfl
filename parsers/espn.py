# -*- coding: utf-8 -*-
import datetime
import logging
import re

from bs4 import BeautifulSoup

from nfl.teams import nickname_to_code

class ESPNNFLParser(object):

    def __init__(self):
        '''
        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def _parse_projections_row(self, row):
        '''
        Parses <tr> element into key-value pairs
        :param row(str): html <tr> element
        :return player(dict):
        '''
        player = {}

        # get the player name / id
        link = row.find("a", {"class": "flexpop"})
        player['espn_id'] = link.get('playerid')
        player['full_name'] = link.string

        # get the player position / team (, Phi WR)
        pos_tm_string = link.nextSibling.string
        pos_tm_string = re.sub(r'\s?,\s+', '', pos_tm_string).strip()
        logging.debug('position team string is %s', pos_tm_string)

        if 'D/ST' in pos_tm_string:
            player['position'] = 'DST'
            player['team'] = self._fix_team_code(link.string.split()[0])
            player['full_name'] = '{0}_DST'.format(player['team'])
            player['injury'] = False

        else:
            try:
                if '*' in pos_tm_string:
                    player['injury'] = True
                    pos_tm_string = player['full_name'].replace('*', '')

                else:
                    player['injury'] = False

                player_team, player_position = pos_tm_string.split()
                player['team'] = re.sub(r'\s+', '', player_team)
                player['position'] = re.sub(r'\s+', '', player_position)

            except ValueError:
                logging.exception("pos_tm_string error")

        # now get the projected points
        fantasy_points = row.find("td", {"class": "appliedPoints"}).string
        if '--' in fantasy_points:
            player['fantasy_points'] = 0
        else:
            player['fantasy_points'] = fantasy_points

        return player

    def nfl_team_roster(self, content):
        '''
        Parses team roster page into list of player dict
        
        Args:
            content: HTML of espn nfl team roster page

        Returns:
            list of dict
        '''
        players = []
        soup = BeautifulSoup(content, 'lxml')
        for tr in soup.find_all('tr'):
            a = tr.find('a', {'href': re.compile(r'/nfl/player/_/id/')})
            if a:
                player = {'source': 'espn'}
                tds = tr.find_all('td')
                player['source_player_position'] = tds[2].text
                player['source_player_name'] = a.text
                player['source_player_id'] = a['href'].split('/')[-2]
                players.append(player)
        return players

    def projections(self, content):
        '''
        Takes HTML, returns list of player dictionaries
        :param content: html page of projections
        :return rows(list): player dictionaries
        '''

        rows = []
        soup = BeautifulSoup(content)

        for row in soup.findAll("tr", {"class": "pncPlayerRow"}):
            player = self._parse_projections_row(row)
            rows.append(player)

        return rows

    def league_rosters(self, rosters):
        '''

        Args:
            rosters (dict): key is person_teamid, value is html string

        Returns:
            rosters (list): list of dict
                            keys --
        '''
        rosters = []

        for t, c in rosters.items():

            rosters += self.team_roster(t, c)
        return rosters

    def lovehate(self, season, week, lh):
        '''

        Args:
            season(int):
            week(int):
            d(dict): keys are position_love, position_hate

        Returns:
            players(list): of player dict
        '''

        players = []

        for poslh, ratings in lh.items():
            pos = poslh.split('_')[0]
            label = ratings.get('label')
            sublabel = None

            if label in ('favorite', 'bargain', 'desparate'):
                sublabel = label
                label = 'love'
            for link in ratings.get('links'):
                url = link.split('"')[1]
                site_player_id, site_player_stub = url.split('/')[7:9]
                site_player_name = link.split('>')[1].split('<')[0]

        #print season, week, pos, label, sublabel, site_player_id, site_player_stub, site_player_name


    def team_roster(self, team_string, content):
        '''
        Parses one team clubhouse
        Args:
            team_string (str): TEAMOWNER_TEAMID
            content (str): html string

        Returns:
            roster (list): of player dict
        '''

        roster = []
        team_owner, team_id = team_string.split('_')

        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'playertable_0'})
        if not t: return roster
        today = datetime.datetime.strftime(datetime.date.today(), '%m-%d-%Y')

        for tr in t.findAll('tr', {'class': 'pncPlayerRow'}):
            player = {}
            pid = tr.get('id')
            if pid: player['espn_player_id'] = re.findall(r'\d+', pid)[0]
            slot = tr.find('td', {'class': 'playerSlot'})
            if slot: player['slot'] = slot.text.strip()
            player_name = tr.find('a', {'class': 'flexpop'})
            if player_name: player['espn_player_name'] = player_name.text.strip()
            player['fantasy_team'] = team_owner
            player['fantasy_team_id'] = team_id
            player['roster_date'] = today
            if player.get('espn_player_name', None):
                roster.append(player)

        return roster

    def fantasy_waiver_wire(self, content):
        '''

        Args:
            content (str): HTML string from espn waiver wire page

        Returns:
            players (list): list of player dict
                {'espn_id': '11373',
                'espn_player_name': u'Jacob Tamme',
                'player_position': u'TE',
                'player_team': u'Atl',
                'season': '2016'}
        '''
        players = []

        # irregular use of non-breaking spaces; easier to remove at start
        content = content.replace('&nbsp;', ' ')
        content = content.replace('*', ' ')

        soup = BeautifulSoup(content, 'lxml')
        t = soup.find('table', {'id': 'playertable_0'})

        #loop through rows in table
        for tr in t.findAll('tr', {'class': 'pncPlayerRow'}):
            player = {'source': 'espn'}
            tds = tr.findAll('td')
            if not tds or len(tds) == 0:
                continue
            else:
                try:
                    # td[0]: name, team, pos
                    ptp = tds[0].text
                    if 'D/ST' in ptp:
                        pattern = r'(.*?)\s+D/ST'
                        match = re.match(pattern, ptp)
                        if match:
                            player['source_player_name'] = '{} Defense'.format(match.group(1))
                            player['source_player_position'] = 'DST'
                            player['source_player_team'] = nickname_to_code(match.group(1))

                    # [u'Kenny Stills', u'Mia WR  Q']
                    elif '  ' in ptp:
                        pattern = r'(.*?),\s+(\w{2,4})\s+(\w{2})\s+(\w+)'
                        match = re.match(pattern, ptp)
                        if match:
                            if not player.get('espn_player_name'): player['espn_player_name'] = match.group(1)
                            player['source_player_team'] = match.group(2).upper()
                            player['source_player_position'] = match.group(3)

                    # [u'Dexter McCluster', u'Ten RB']
                    else:
                        # do generic split routine
                        pn, tp = ptp.split(', ')
                        if not player.get('espn_player_name'):
                            player['espn_player_name'] = pn
                        player['source_player_team'], player['source_player_position'] = tp.split()

                    # a[0]: player_id
                    a = tr.find('a')
                    if a:
                        player['source_player_id'] = a.attrs.get('playerid')

                    # tds[2]: player status
                    player['player_status'] = tds[2].text

                    # tds[-2]: owernership
                    player['player_own'] = tds[-2].text

                    # tds[-1]: plus/minus
                    player['player_own_pm'] = tds[-1].text.replace('+', '')

                    players.append(player)

                except Exception as e:
                    logging.exception(e)

        return players

if __name__ == "__main__":
    pass
