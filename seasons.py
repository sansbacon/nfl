'''
seasons.py
provides functions for findings dates in NFL seasons
'''

import datetime
import logging

from nfl.dates import site_format
import nfl.seasonsdata


def all_seasons():
    '''
    Returns all seasons of weeks w/ start & end dates
    '''
    return nfl.seasonsdata.SEASONS


def current_season_year():
    '''
    Gets current season based on today's date

    Returns:
        int
    '''
    d = datetime.date.today()
    if d.month > 2:
        return d.year
    else:
        return d.year - 1


def fantasylabs_week(seas, wk, fmt='fl_matchups'):
    '''
    Determines date for fantasylabs API request given season and week

    Args:
        seas: 
        wk: 
        fmt: 

    Returns:

    '''
    s = get_season(seas)
    if s:
        w = s.get(wk)
        if w:
            st = w.get('start')
            if st:
                return datetime.datetime.strftime(st - datetime.timedelta(days=1), site_format(fmt))
    return None


def get_season(y):
    '''
    Given int y, returns entire season of weeks w/ start & end dates
    '''
    return nfl.seasonsdata.SEASONS.get(y)


def season_week(d):
    '''
    Takes date and figures out season and week

    Arguments:
        d(datetime.date): the day of the game
    '''

    if not isinstance(d, datetime.date):
        raise ValueError('d must be date')

    # get the year and month
    # infer which season based on these
    year = d.year
    month = d.month

    # year is 1 above season if january/february
    if month < 3:
        season_year = year - 1
    else:
        season_year = year
    logging.debug('season year is {}'.format(season_year))

    # guess the week to start with
    guess_week = 1
    season = get_season(season_year)

    if month < 3:
        guess_week = 15
    elif month == 10:
        guess_week = 2
    elif month == 11:
        guess_week = 6
    elif month == 12:
        guess_week = 10
    logging.debug('guess week is {}'.format(guess_week))

    # loop from guess
    for week in range(guess_week, 18):
        season_week = season.get(week)
        start = season_week.get('start')
        logging.debug('start is {}'.format(start))
        end = season_week.get('end')
        logging.debug('end is {}'.format(end))
        if start <= d <= end:
            logging.info('{0} is between {1} and {2}'.format(d, start, end))
            return {'season': season_year, 'week': week}

    # return None on fail
    return None


def week_end(season, week):
    '''
    Given season and week, provides end date of NFL week (Monday)

    Args:
        season: int 2016, 2015, etc.
        week: int 1, 2, etc.

    Returns:
        datetime
    '''
    seas = get_season(season)
    if seas:
        wk = seas.get(week)
        if wk:
            return wk.get('end')
    return None


def week_start(season, week):
    '''
    Given season and week, provides start date of NFL week (Tuesday)
    
    Args:
        season: int 2016, 2015, etc.
        week: int 1, 2, etc.

    Returns:
        datetime
    '''
    seas = get_season(season)
    if seas:
        wk = seas.get(week)
        if wk:
            return wk.get('start')
    return None


if __name__ == '__main__':
    pass
