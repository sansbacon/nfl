'''
names.py
'''

import logging

from fuzzywuzzy import process
from nameparser import HumanName

logging.getLogger(__name__).addHandler(logging.NullHandler())


def first_last(name):
    '''
    Returns name in First Last format
    
    '''
    hn = HumanName(name)
    return '{0} {1}'.format(hn.first, hn.last)

def first_last_pair(name):
    '''
    Returns name in First Last pair

    '''
    hn = HumanName(name)
    return [hn.first, hn.last]

def last_first(name):
    '''
    Returns name in Last, First format
    '''

    hn = HumanName(name)
    return '{1}, {0}'.format(hn.first, hn.last) 


def match_player (to_match, match_from, threshold = .8):
    '''
    Matches player with direct or fuzzy match
    Args:
        to_match (str): player name to match
        match_from (list): list of player names to match against

    Returns:
        name (str): matched name from match_from list

    Example:
        name = match_player(player, players)
    '''
    name = None

    # first see if there is a direct match
    if to_match in match_from:
        name = to_match

    # try first last
    if not name:
        for mf in match_from:
            to_match = first_last(to_match)
            possible_match = first_last(mf)
            if to_match == possible_match:
                name = mf

    # if still no match, then try fuzzy matching
    if not name:
        fuzzy, confidence = process.extractOne(to_match, match_from)
        if confidence >= threshold:
            name = fuzzy
    return name


if __name__ == '__main__':
    pass
