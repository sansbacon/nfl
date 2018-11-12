'''
seasons.py
provides functions for findings dates in NFL seasons
'''

import datetime
import logging

import nfl.seasonsdata
from nfl.dates import site_format

logger = logging.getLogger(__name__)


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
    dt_today = datetime.date.today()
    if dt_today.month > 2:
        return dt_today.year
    return dt_today.year - 1


def fantasylabs_week(seas, week, fmt='fl_matchups'):
    '''
    Determines date for fantasylabs API request given season and week

    Args:
        seas(int):
        week(int):
        fmt(str):

    Returns:
        str

    '''
    flweek = None
    try:
        nfl_seas = get_season(seas)
        nfl_week = nfl_seas.get(week)
        start = nfl_week.get('start')
        flweek = datetime.datetime.strftime(start - datetime.timedelta(days=1), site_format(fmt))
    except ValueError:
        pass
    return flweek


def get_season(year):
    '''
    Given int y, returns entire season of weeks w/ start & end dates

    Args:
        year(int): NFL year

    Returns:
        dict

    '''
    return nfl.seasonsdata.SEASONS.get(year)


def salary_week(dtobj=None):
    '''
    Takes date and figures out season and upcoming week.

    Arguments:
        dtobj(datetime.date): the day of the game, default today

    Returns:
        tuple: int, int
        
    '''
    if not dtobj:
        dtobj = datetime.datetime.now().date()
    elif isinstance(dtobj, datetime.datetime):
        dtobj = dtobj.date()
        
    # get the year and month
    # infer which season based on these
    year = dtobj.year
    month = dtobj.month

    # year is 1 above season if january/february
    if month < 3:
        seas_year = year - 1
    else:
        seas_year = year

    # guess the week to start with
    guess_week = 1
    season = get_season(seas_year)
    if month < 3:
        guess_week = 15
    elif month == 10:
        guess_week = 2
    elif month == 11:
        guess_week = 6
    elif month == 12:
        guess_week = 10

    # loop from guess
    for week in range(guess_week, 18):
        seas_week = season.get(week)
        start = seas_week.get('start')
        end = seas_week.get('end')
        if start <= dtobj <= end:
            # we want to get the upcoming week, 
            # so if we are on a sunday or monday, 
            # will add 1 to week
            if dtobj.weekday() in [0, 6]:
                return seas_year, week + 1
            return seas_year, week
    return None


def season_week(dtobj):
    '''
    Takes date and figures out season and week

    Arguments:
        dtobj(datetime.date): the day of the game

    '''

    if not isinstance(dtobj, datetime.date):
        raise ValueError('dtobj must be date')

    # get the year and month
    # infer which season based on these
    year = dtobj.year
    month = dtobj.month

    # year is 1 above season if january/february
    if month < 3:
        seas_year = year - 1
    else:
        seas_year = year

    # guess the week to start with
    guess_week = 1
    season = get_season(seas_year)

    if month < 3:
        guess_week = 15
    elif month == 10:
        guess_week = 2
    elif month == 11:
        guess_week = 6
    elif month == 12:
        guess_week = 10

    # loop from guess
    for week in range(guess_week, 18):
        seas_week = season.get(week)
        start = seas_week.get('start')
        end = seas_week.get('end')
        if start <= dtobj <= end:
            return {'season': seas_year, 'week': week}

    # return empty dict on fail
    return {}


def week_end(season, week):
    '''
    Given season and week, provides end date of NFL week (Monday)

    Args:
        season: int 2016, 2015, etc.
        week: int 1, 2, etc.

    Returns:
        datetime
    '''
    try:
        return get_season(season).get(week).get('end')
    except ValueError:
        return None


def week_start(season, week):
    '''
    Given season and week, provides start date of NFL week (Tuesday)

    Args:
        season(int): 2016, 2015, etc.
        week(int): 1, 2, etc.

    Returns:
        datetime

    '''
    try:
        return get_season(season).get(week).get('end')
    except ValueError:
        return None


if __name__ == '__main__':
    pass
