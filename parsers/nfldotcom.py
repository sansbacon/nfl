
import logging
import re

from bs4 import BeautifulSoup
# json module in standard library could not parse gamecenter
#import demjson

from nfl.utility import merge


class NFLDotComParser:
    '''
    Used to parse NFL.com GameCenter pages, which are json documents with game and play-by-play stats
    '''

    def __init__(self):
        logging.getLogger(__name__).addHandler(logging.NullHandler())


    def _gamecenter_team(self, team):
        '''
        Parses home or away team into stats dictionary       
        Args:
            team: dictionary representing home or away team
        Returns:
            players: dictionary of team stats
        '''
        categories = ['passing', 'rushing', 'receiving', 'fumbles', 'kickret', 'puntret', 'defense']
        players = {}
        for category in categories:
            for player_id, player_stats in team[category].items():
                if not player_id in players:
                    players[player_id] = {'player_id': player_id}
                    players[player_id][category] = player_stats
        return players


    def gamecenter(self, parsed):
        '''
        Parses gamecenter (json document)
        Args:
            content: parsed json document
        Returns:
            dict            
        Misc:
            puntret: avg, lng, lngtd, name, ret, tds
            fumbles: lost, name, rcv, tot, trcv, yds
            defense: ast, ffum, int, name, sk, tkl
            rushing: att, lng.lngtd, name, tds, twopta, twoptm, yds
            receiving: lng, lngtd, name, rec, tds, twopta, twoptm, yds
            passing: att, cmp, ints, name, tds, twopta, twoptm, yds
        '''
        game_id = parsed.keys()[0]
        home_team_stats = self._gamecenter_team(parsed[game_id]['home']['stats'])
        away_team_stats = self._gamecenter_team(parsed[game_id]['away']['stats'])
        return merge(dict(),[home_team_stats, away_team_stats])


    def position(self, content):
        '''
        Returns position from profile page
        Args:
            content: HTML string   
        Returns:
            pos: 'QB', 'RB', 'WR', 'TE', 'UNK'
        '''
        patt = re.compile(r'[A-Z]{1}.*?,\s+([A-Z]{1,2})', re.IGNORECASE | re.UNICODE)
        soup = BeautifulSoup(content, 'lxml')
        title = soup.title.text
        match = re.search(patt, title)
        if match:
            return match.group(1)
        else:
            return u'UNK'


if __name__ == "__main__":
    pass
