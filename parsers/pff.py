import logging

from bs4 import BeautifulSoup

from nfl.parsers import projections


class PFFParser():


    def __init__(self):
        '''

        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def position_grades(content):
        '''
        Parses season-ending grades for 
        
        Args:
            content: dict with keys teams, rosters

        Returns:
            players
        '''
        players = []
        keys = ['first_name','last_name', 'franchise_id', 'gsis_id']
        snap_exclude = ['player_id', 'season', 'week']

        for item in content['rosters']:
            player = {k:v for k,v in item.items() if k in keys}
            context = player.copy()
            if item.get('grade', None):
                context.update(item['grade'])
            if item.get('snapCount', None):
                context.update({k:v for k,v in item['snapCount'].items() if k not in snap_exclude})
            players.append(context)

        return players

if __name__ == "__main__":
    pass
