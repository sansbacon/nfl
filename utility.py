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

from nfl.db.nflpg import NFLPostgres


def csv_to_dict(fn):
    '''
    Takes csv filename and returns dicts

    Arguments:
        fn (str): name of file to read/parse

    Returns:
        list: List of dicts
        
    '''
    with open(fn, 'r') as infile:
        for row in csv.DictReader(infile, skipinitialspace=True, delimiter=','):
            yield {k: v for k, v in row.items()}


def digits(s):
    '''
    Removes non-numeric characters from a string

    Args:
        s (str): string with non-numeric characters 

    Returns:
        str
        
    '''
    return ''.join(ch for ch in s if ch.isdigit())


def flatten(d):
    '''
    Flattens nested dict into single dict

    Args:
        d (dict): The original dict

    Returns:
        dict: nested dict flattened into dict
        
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
        l (list): original list of lists

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

    Args:
        fname (str): filename
        
    Returns:
        None
        
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


def getdb(key='nfldb', configfn=None):
    '''
    Gets database instance
    
    Args:
        key (str): top-level key in configfile 
        configfn (str): filename of configfile 

    Returns:
        NFLPostgres instance
    
    '''
    try:
        import ConfigParser as configparser
    except ImportError:
        import configparser
    config = configparser.ConfigParser()
    if not configfn:
        config.read(os.path.join(os.path.expanduser('~'), '.fantasy'))
    else:
        config.read(configfn)
    return NFLPostgres(user=config.get(key, 'username'),
                       password=config.get(key, 'password'),
                       database=config.get(key, 'db'))


def getengine(key='nfldb', configfn=None):
    '''
    Gets sqlite engine

    Args:
        key (str): top-level key in configfile 
        configfn (str): filename of configfile 

    Returns:
        sqlalchemy engine

    '''
    try:
        import ConfigParser as configparser
    except ImportError:
        import configparser
    config = configparser.ConfigParser()
    if not configfn:
        config.read(os.path.join(os.path.expanduser('~'), '.fantasy'))
    else:
        config.read(configfn)
    try:
        from sqlalchemy import create_engine
        base_connstr = 'postgresql://{u}:{p}@localhost:5432/{db}'
        connstr = base_connstr.format(u=config.get(key, 'username'),
            p=config.get(key, 'password'), db=config.get(key, 'db'))
        return create_engine(connstr)
    except:
        return None


def isfloat(x):
    '''
    Tests if conversion to float succeeds
    
    Args:
        x: value to test

    Returns:
        boolean: True if can convert to float, False if cannot.
        
    '''
    try:
        a = float(x)
    except Exception as e:
        return False
    else:
        return True


def isint(x):
    '''
    Tests if value is integer

    Args:
        x: value to test

    Returns:
        boolean: True if int, False if not.

    '''
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

    Args:
        json_fname (str): name of file to read/parse

    Returns:
        dict: Parsed json into dict
        
    '''
    if os.path.exists(json_fname):
        with open(json_fname, 'r') as infile:
            return json.load(infile)
    else:
        raise ValueError('{0} does not exist'.format(json_fname))


def memoize(function):
    '''
    Memoizes function
    
    Args:
        function (func): the function to memoize

    Returns:
        func: A memoized function
        
    '''
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
    Merges multiple dictionaries into one
    
    Note:
        See http://stackoverflow.com/questions/28838291/merging-multiple-dictionaries-in-python

    Args:
        merge_dico (dict): dict to merge into
        dico_list (list): list of dict

    Returns:
        dict: merged dictionary
        
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
    Merges two dictionaries into one. Second dict will overwrite values in first.

    Args:
        d1 (dict): first dictionary
        d2 (dict): second dictionary

    Returns:
        dict: A merged dictionary
        
    '''
    context = d1.copy()
    context.update(d2)
    return context    


def pair_list(list_):
        '''
        Allows iteration over list two items at a time
        '''
        list_ = list(list_)
        return [list_[i:i + 2] for i in range(0, len(list_), 2)]


def save_csv(data, csv_fname, fieldnames, sep=';'):
    '''
    Takes datastructure and saves as csv file

    Args:
        data (iterable): python data structure
        csv_fname (str): name of file to save
        fieldnames (list): list of fields

    Returns:
        None
 
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

    Args:
        pkl_fname (str): name of file to read/parse

    Returns:
        iterable: python datastructure
        
    '''
    if os.path.exists(pkl_fname):
        with open(pkl_fname, 'rb') as infile:
            return pickle.load(infile)
    else:
        raise ValueError('{0} does not exist'.format(pkl_fname))


def read_json(json_fname):
    '''
    Reads json file

    Arguments:
        json_fname (str): name of file to save

    Returns:
        dict

    '''
    try:
        with open(json_fname, 'r') as infile:
            return json.load(infile)
    except:
        logging.exception('{0} does not exist'.format(json_fname))


def save_json(data, json_fname):
    '''
    Takes data and saves to json file

    Arguments:
        data (iterable): python data structure
        json_fname (str): name of file to save
        
    Returns:
        None
        
    '''
    try:
        with open(json_fname, 'w') as outfile:
            json.dump(data, outfile)
    except:
        logging.exception('{0} does not exist'.format(json_fname))


def save_pickle(data, pkl_fname):
    '''
    Saves data structure to pickle file

    Args:
        data (iterable): python data structure
        pkl_fname (str): name of file to save

    Returns:
        None
        
    '''
    try:
        with open(pkl_fname, 'wb') as outfile:
            pickle.dump(data, outfile)
    except:
        logging.exception('{0} does not exist'.format(pkl_fname))


def save_file(data, fname):
    '''
    Pass filename, it returns datastructure. Decides based on file extension.
    
    Args:
        data (iterable): arbitrary datastructure
        fname (str): filename to save
    
    Returns:
        None
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
    Python 2/3 url quoting    

    Args:
        s (str): string to quote

    Returns:
        str: URL quoted string

    '''
    try:
        import urllib.parse
        return urllib.parse.quote(s)
    except:
        import urllib
        return urllib.quote(s)


if __name__ == '__main__':
    pass