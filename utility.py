import collections
import csv
from functools import wraps
import json
import logging
import os

try:
    import cPickle as pickle
except ImportError:
    import pickle


def csv_to_dict(fn):
    '''
    Takes csv filename and returns dicts

    Arguments:
        fn: string - name of file to read/parse

    Returns:
        List of dicts
    '''
    with open(fn, 'r') as infile:
        for row in csv.DictReader(infile, skipinitialspace=True, delimiter=','):
            yield {k: v for k, v in row.items()}

def digits(s):
    '''
    Removes non-numeric characters from a string
    Args:
        s: 

    Returns:
        str
    '''
    return ''.join(ch for ch in s if ch.isdigit())

def flatten(d):
    '''
    Flattens nested dict into single dict

    Args:
        d: original dict

    Returns:
        dict
    '''
    items = []
    for k, v in d.items():
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v).items())
        else:
            items.append((k, v))
    return dict(items)

def flatten_list(l):
    '''
    Flattens list of lists into list

    Args:
        l: original list of lists

    Returns:
        list
    '''
    try:
        return [item for sublist in l for item in sublist]
    except:
        return l

def file_to_ds(fname):
    '''
    Pass filename, it returns data structure. Decides based on file extension.
    '''
    ext = os.path.splitext(fname)[1]
    if ext == '.csv':
        return csv_to_dict(fname)
    elif ext == '.json':
        return json_to_dict(fname)
    elif ext == 'pkl':
        return read_pickle(fname)
    else:
        raise ValueError('{0} is not a supported file extension'.format(ext))


def getdb(configfn=None):
    try:
        import ConfigParser as configparser
    except ImportError:
        import configparser

    from nfl.db.nflpg import NFLPostgres
    config = configparser.ConfigParser()
    if not configfn:
        config.read(os.path.join(os.path.expanduser('~'), '.fantasy'))
    else:
        config.read(configfn)
    return NFLPostgres(user=config['db']['username'], password=config['db']['password'], database='nfldb')


def isfloat(x):
    try:
        a = float(x)
    except Exception as e:
        return False
    else:
        return True


def isint(x):
    try:
        a = float(x)
        b = int(a)
    except Exception as e:
        return False
    else:
        return a == b


def json_to_dict(json_fname):
    '''
    Takes json file and returns data structure

    Arguments:
        json_fname: name of file to read/parse

    Returns:
        parsed json into dict
    '''
    if os.path.exists(json_fname):
        with open(json_fname, 'r') as infile:
            return json.load(infile)
    else:
        raise ValueError('{0} does not exist'.format(json_fname))

def memoize(function):
    memo = {}
    @wraps(function)
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper

def merge(merge_dico, dico_list):
        '''
        See http://stackoverflow.com/questions/28838291/merging-multiple-dictionaries-in-python

        Arguments:
            merge_dico:
            dico_list:

        Returns:
            merged dictionary
        '''
        for dico in dico_list:
            for key, value in dico.items():
                if type(value) == type(dict()):
                    merge_dico.setdefault(key, dict())
                    merge(merge_dico[key], [value])
                else:
                    merge_dico[key] = value
        return merge_dico

def merge_two(d1, d2):
    '''
    See http://stackoverflow.com/questions/28838291/merging-multiple-dictionaries-in-python

    Arguments:
        d1: dict
        d2: dict
    Returns:
        merged dictionary
    '''
    context = d1.copy()
    context.update(d2)
    return context    

def save_csv(data, csv_fname, fieldnames, sep=';'):
    '''
    Takes datastructure and saves as csv file

    Arguments:
        data: python data structure
        csv_fname: name of file to save
        fieldnames: list of fields
    '''
    try:
        with open(csv_fname, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    except:
        logging.exception('could not save csv file')


def read_pickle(pkl_fname):
    '''
    Takes pickle file and returns data structure

    Arguments:
        pkl_fname: name of file to read/parse

    Returns:
        parsed json
    '''
    if os.path.exists(pkl_fname):
        with open(pkl_fname, 'rb') as infile:
            return pickle.load(infile)
    else:
        raise ValueError('{0} does not exist'.format(pkl_fname))


def save_json(data, json_fname):
    '''
    Takes data and saves to json file

    Arguments:
        data: python data structure
        json_fname: name of file to save
    '''
    try:
        with open(json_fname, 'wb') as outfile:
            json.dump(data, outfile)
    except:
        logging.exception('{0} does not exist'.format(json_fname))


def save_pickle(data, pkl_fname):
    '''
    Saves data structure to pickle file

    Arguments:
        data: python data structure
        pkl_fname: name of file to save
    '''
    try:
        with open(pkl_fname, 'wb') as outfile:
            pickle.dump(data, outfile)
    except:
        logging.exception('{0} does not exist'.format(pkl_fname))


def save_file(data, fname):
    '''
    Pass filename, it returns datastructure. Decides based on file extension.
    '''
    ext = os.path.splitext(fname)[1]
    if ext == '.csv':
        save_csv(data=data, csv_fname=fname, fieldnames=data[0])
    elif ext == '.json':
        save_json(data, fname)
    elif ext == 'pkl':
        save_pickle(data, fname)
    else:
        raise ValueError('{0} is not a supported file extension'.format(ext))

def url_quote(s):
    '''
    
    Args:
        s: 

    Returns:

    '''
    try:
        import urllib.parse
        return urllib.parse.quote(s)
    except:
        import urllib
        return urllib.quote(s)

if __name__ == '__main__':
    pass
