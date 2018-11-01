"""
# dates.py
# common date routines

"""

import datetime
import logging
import re

from past.builtins import basestring


def convert_format(datestr, site):
    '''
    Converts string from one date format to another

    Args:
        datestr(str): date as string
        site(str): 'nfl', 'fl', 'std', etc.

    Returns:
        str

    '''
    fmt = format_type(datestr)
    newfmt = site_format(site)
    if fmt and newfmt:
        try:
            dtobj = datetime.datetime.strptime(datestr, fmt)
            return datetime.datetime.strftime(dtobj, newfmt)
        except BaseException:
            return None
    else:
        return None


def date_list(date1, date2):
    '''
    Takes two datetime objects or datestrings and returns a list of datetime objects

    Args:
        date1: more recent datetime object or string
        date2: less recent datetime object or string

    Returns:
        dates (list): list of datetime objects

    Examples:
        for d in date_list('10_09_2015', '10_04_2015'):
            print datetime.strftime(d, '%m_%d_%Y')

    '''
    if isinstance(date1, str):
        try:
            date1 = strtodate(date1)
        except BaseException:
            logging.error('%s is not in m_d_Y format', date1)
    if isinstance(date2, str):
        try:
            date2 = strtodate(date2)
        except BaseException:
            logging.error('%s is not in m_d_Y format', date2)
    season = date1 - date2
    return [date1 - datetime.timedelta(days=x) for x in range(0, season.days + 1)]


def datetostr(dtobj, site):
    '''
    Converts datetime object to formats used by different sites

    Args:
        dtobj(datetime): object
        site(str):  'nfl' or 'fl'

    Returns:
        datestr in specified format

    '''
    return datetime.datetime.strftime(dtobj, site_format(site))


def format_type(datestr):
    '''
    Uses regular expressions to determine format of datestring

    Args:
        datestr (str): date string in a variety of different formats

    Returns:
        fmt (str): format string for date

    '''
    val = None
    if re.match(r'\d{1,2}_\d{1,2}_\d{4}', datestr):
        val = site_format('fl')
    elif re.match(r'\d{4}-\d{2}-\d{2}', datestr):
        val = site_format('nfl')
    elif re.match(r'\d{1,2}-\d{1,2}-\d{4}', datestr):
        val = site_format('std')
    elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', datestr):
        val = site_format('odd')
    elif re.match(r'\d{8}', datestr):
        val = site_format('db')
    elif re.match(r'\w+ \d+, \d+', datestr):
        val = site_format('bdy')
    return val


def site_format(site):
    '''
    Stores date formats used by different sites

    Args:
        site(str):

    Returns:
        str

    '''
    return {
        'std': '%m-%d-%Y',
        'fl': '%m_%d_%Y',
        'fl2017': '%m-%d-%Y',
        'fl_matchups': '%-m-%-d-%Y',
        'nfl': '%Y-%m-%d',
        'odd': '%m/%d/%Y',
        'db': '%Y%m%d',
        'bdy': '%B %d, %Y',
        'espn_fantasy': '%Y%m%d'
    }.get(site, None)


def strtodate(dstr):
    '''
    Converts date formats used by different sites

    Args:
        dstr(dstr): datestring

    Returns:
        datetime.datetime

    '''
    return datetime.datetime.strptime(dstr, format_type(dstr))


def subtract_datestr(date1, date2):
    '''
    Subtracts d2 from d1

    Args:
        date1(str): '2018-01-01'
        date2(str): '2017-12-12'

    Returns:
        int: number of days between dates

    '''
    if isinstance(date1, basestring):
        delta = strtodate(date1) - strtodate(date2)
    else:
        delta = date1 - date2
    return delta.days


def today(fmt='nfl'):
    '''
    Datestring for today's date

    Args:
        fmt(str): 'nfl'

    Returns:
        str

    '''
    fmt = site_format(fmt)
    if not fmt:
        raise ValueError('invalid date format')
    return datetime.datetime.strftime(datetime.datetime.today(), fmt)


def yesterday(fmt='nfl'):
    '''
    Datestring for yesterday's date

    Args:
        fmt(str):  'nfl'

    Returns:
        str

    '''
    fmt = site_format(fmt)
    if not fmt:
        raise ValueError('invalid date format')
    return datetime.datetime.strftime(
        datetime.datetime.today() - datetime.timedelta(1), fmt)


def yesterday_x(interval, fmt='nfl'):
    '''
    Datestring for two days ago date

    Args:
        fmt(str): 'nfl'

    Returns:
        str

    '''
    fmt = site_format(fmt)
    if not fmt:
        raise ValueError('invalid date format')
    return datetime.datetime.strftime(
        datetime.datetime.today() -
        datetime.timedelta(interval),
        fmt)


if __name__ == '__main__':
    pass
