'''
names.py
'''

import logging
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


if __name__ == '__main__':
    pass
