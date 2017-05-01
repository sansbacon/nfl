import logging

from bs4 import BeautifulSoup


class ScoutNFLParser(object):
    '''
    
    '''

    def __init__(self,**kwargs):
        '''

        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())


    def depth_chart(self, content, as_of=None):
        '''
        Parses HTML of NFL depth charts (all teams)

        Args:
            content: HTML string
            as_of: date string

        Returns:
            dc: list of dict
        '''
        dc = []
        soup = BS(content, 'lxml')
        for div in soup.find_all('div', class_='team'):
            a = div.select_one('h3 a')
            team = a.get('href').split('=')[-1]
            for li in div.select('ul li'):
                p = {'source': 'scout', 'team_code': team, 'as_of': as_of}
                p['source_player_position'] = li.contents[0]
                p['source_player_name'] = li.contents[1].text
                p['source_player_id'] = li.contents[1].get('href').split('=')[-1] 
                dc.append(p)
        return dc
        
        
if __name__ == "__main__":
    pass
