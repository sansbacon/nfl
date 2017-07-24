# dates.py
# common date routines

from past.builtins import basestring

import datetime
import logging
import re


def convert_format(d, site):
    '''
    Converts string from one date format to another

    Args:
        d: datestring
        site: 'nfl', 'fl', 'std', etc.

    Returns:
        Datestring in new format
    '''
    fmt = format_type(d)
    newfmt = site_format(site)
    if fmt and newfmt:
        try:
            dt = datetime.datetime.strptime(d, fmt)
            return datetime.datetime.strftime(dt, newfmt)
        except:
            return None
    else:
        return None

def date_list(d1, d2):
    '''
    Takes two datetime objects or datestrings and returns a list of datetime objects

    Args:
        d1: more recent datetime object or string
        d2: less recent datetime object or string

    Returns:
        dates (list): list of datetime objects
        
    Examples:
        for d in date_list('10_09_2015', '10_04_2015'):
            print datetime.strftime(d, '%m_%d_%Y')
    '''
    if isinstance(d1, str):
        try:
            d1 = strtodate(d1)
        except:
            logging.error('{0} is not in %m_%d_%Y format'.format(d1))
    if isinstance(d2, str):
        try:
            d2 = strtodate(d2)
        except:
            logging.error('{0} is not in %m_%d_%Y format'.format(d1))
    season = d1 - d2
    return [d1 - datetime.timedelta(days=x) for x in range(0, season.days+1)]

def datetostr(d, site):
    '''
    Converts datetime object to formats used by different sites

    Args:
        d: DateTime object
        site: str, such as 'nfl' or 'fl'

    Returns:
        datestr in specified format
    '''
    return datetime.datetime.strftime(d, site_format(site))

def format_type(datestr):
    '''
    Uses regular expressions to determine format of datestring

    Args:
        d (str): date string in a variety of different formats

    Returns:
        fmt (str): format string for date

    '''

    if re.match(r'\d{1,2}_\d{1,2}_\d{4}', datestr):
        return site_format('fl')

    elif re.match(r'\d{4}-\d{2}-\d{2}', datestr):
        return site_format('nfl')

    elif re.match(r'\d{1,2}-\d{1,2}-\d{4}', datestr):
        return site_format('std')

    elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', datestr):
        return site_format('odd')

    elif re.match(r'\d{8}', datestr):
        return site_format('db')

    else:
        return None

def site_format(site):
    '''
    Stores date formats used by different sites
    '''
    fmt = {
        'std': '%m-%d-%Y',
        'fl': '%m_%d_%Y',
        'nfl': '%Y-%m-%d',
        'odd': '%m/%d/%Y',
        'db': '%Y%m%d'
    }
    return fmt.get(site, None)

def strtodate(d):
    '''
    Converts date formats used by different sites
    '''
    return datetime.datetime.strptime(d, format_type(d))


def subtract_datestr(d1, d2):
    '''
    Subtracts d2 from d1
    Args:
        d1: datestr
        d2: datestr

    Returns:
        int
    '''
    if isinstance(d1, basestring):
        delta = strtodate(d1) - strtodate(d2)
    else:
        delta = d1 - d2
    return delta.days

def today(fmt='nfl'):
    '''
    Datestring for today's date

    Args:
        fmt: str, code like 'nfl'

    Returns:
        datestr
    '''
    fmt = site_format(fmt)
    if not fmt:
        raise ValueError('invalid date format')
    return datetime.datetime.strftime(datetime.datetime.today(), fmt)

def yesterday(fmt='nfl'):
    '''
    Datestring for yesterday's date

    Args:
        fmt: str, code like 'nfl'

    Returns:
        datestr
    '''
    fmt = site_format(fmt)
    if not fmt:
        raise ValueError('invalid date format')
    return datetime.datetime.strftime(datetime.datetime.today() - datetime.timedelta(1), fmt)
