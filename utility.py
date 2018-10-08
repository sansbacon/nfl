import collections
import csv
from functools import wraps
import json
import logging
import os
import random
import sys
from urllib.parse import urlsplit, parse_qs, urlencode

try:
    import cPickle as pickle
except ImportError:
    import pickle

import pandas as pd
from nflmisc.nflpg import NFLPostgres

 
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


def dict_to_csv(dicts, fn, fields=None):
    '''
    Writes list of dict to csv file. Can specify fields or use keys for dicts[0].

    Args:
        dicts(list): of dict
        fn(str): name of csvfile
        fields(list): fieldnames, default None
    
    Returns:
        None
        
    '''
    with open(fn, 'w') as csvfile:
        if not fields:
            fields = list(dicts[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        for d in dicts:
            writer.writerow(d)


def df_to_html(df, sort_index='', sort_type='desc', targets='', fn=None):
    '''
    Outputs an html table to disk

    Args:
        df (DataFrame): the dataframe to create html from
        sort_index(int): column to sort by
        sort_type(str): asc or desc
        targets(str): numeric columns for sorting
        fn (str): filename to save
        
    Returns:
        str

    '''
    # using plugin any-number to sort numeric columns - that is the "type" entry in columnDefs
    # use jquery script to alternate shading rows in white and grey
    # pandas creates a table that is plugged into the page
    page = '''<!DOCTYPE html><html>
              <head>
                <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/v/dt/dt-1.10.16/datatables.min.css"/>
              <body>
                  <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
                  <script type="text/javascript" src="https://cdn.datatables.net/v/dt/dt-1.10.16/datatables.min.js"></script>
                  <script type="text/javascript" src="https://cdn.datatables.net/1.10.16/js/dataTables.bootstrap.min.js"></script>
                  <script type="text/javascript" src="https://cdn.datatables.net/plug-ins/1.10.18/sorting/any-number.js"></script>
                  <script type="text/javascript">
                    $(document).ready(function() {
                      $('#draft').DataTable( {
                        "iDisplayLength": 300,
                        "order": [|INDEX|],
                        "columnDefs": [
                            {"className": "dt-center", "targets": "_all"},
                            {"type": "any-number", "targets": [|TARGETS|]}
                          ]
                      } );
                    } );
                  </script>
                  <script type="text/javascript">
                  $(document).ready(function()
                    {$("tr:odd").css({
                     "background-color":"#cacfd2",
                     "color":"#000"});
                  });
                  </script>
                  |TABLE|
              </body>
              </html>'''

    # pandas 0.23 has improved API for generating tables
    # this code won't work in earlier versions of pandas
    tbl = df.to_html(border=0,
                      index=False,
                      classes=['display'], 
                      table_id='draft')
    
    # insert table into page
    page = page.replace('|TABLE|', tbl).replace('|TARGETS|', targets)
    
    # if sort index, also specify sort type
    # otherwise, leave sort index blank
    if sort_index:
        page = page.replace('|INDEX|', str(sort_index) + ', ' + '"' + sort_type + '"')
    else:
        page = page.replace('|INDEX|', str(sort_index))

    # save to file if specify filename
    if fn:
        with open(fn, 'w') as outfile:
            outfile.write(page)

    return page
    
            
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


def getdb(key='nfl', configfn=None):
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


def getengine(key='nfl', configfn=None):
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
    except Exception as e:
        logging.exception(e)
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


def dict_to_qs(d):
    '''
    Converts dict into query string for url
    
    Args:
        dict
        
    Returns:
        str
        
    '''
    return urlencode(d)


def qs_to_dict(qs):
    '''
    Converts query string from url into dict
    
    Args:
        qs(str): url with query string
        
    Returns:
        dict
        
    '''
    query = urlsplit(url).query
    return parse_qs(query)


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


def sample_dict(d, n=1):
    '''
    Gets random sample of dictionary
    
    Args:
        d(dict):
        
    Returns:
        dict
        
    '''
    keys = list(d.keys())
    return {k:d[k] for k in random.sample(keys, n)}
    
    
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
