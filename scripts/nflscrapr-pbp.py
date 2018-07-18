# nflscrapr-pbp.py
# converts play-by-play file 
# for use in database

def _fix_fields(fields):
    '''
    Prepares fields for insertion into db
    
    '''
    fields = [f.replace('.', '') for f in fields]
    
def _fix_val(val):
    '''
    Converts NaN to None
    
    '''
    if val in ['', ' ', '-', 'NA', 'NaN', 'None']:
        return None
    elif 'e3' in val:
        d1, d2 = val.split('e')
        try:
            return float(d1) * (10**int(d2))
        except:
            return val
    else:
        return val
        

def play_by_play_table(plays):
    '''
    Converts list of dict for entry into play_by_play table
    
    Args:
        plays(list): of dict
    
    Returns:
        list: of dict
        
    '''
    fixed = []
    
    for p in plays:
        # remove periods from field names and make lowercase
        d = {k.replace('.','').lower(): _fix_val(v) for k,v in p.items()}
        
        # season, gameid, date, desc
        d['gsis_id'] = d.pop('gameid')
        d['play_description'] = d.pop('desc')
        d.pop('season', None)
        d.pop('date', None)
        
        # it is ready
        fixed.append(d)
        
    return fixed
    
