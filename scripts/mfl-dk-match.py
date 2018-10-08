# scripts/mfl-dk-match.py
# matches mfl and dk players


from nfl.utility import merge, getdb
from nfl.player.mflxref import *
from nfl.player.playerxref import player_match_fuzzy, player_match_interactive


def _fix_team(tm):
    '''
    Standardizes team code
    
    Args:
        tm(str):
        
    Returns:
        str
        
    '''
    d = {'NEP': 'NE', 'GBP': 'GB', 'KCC': 'KC', 'JAC': 'JAX',
         'TBB': 'TB', 'NOS': 'NO', 'SFO': 'SF'}
    return d.get(tm, tm)

def match(db):
    matches = []
    q = """
      SELECT 
        source_player_id as dkid,
        concat_ws('_', source_player_name, source_team_id, dfs_position) as plk 
      FROM dfs.fn_dksal_sws(2018, {}, '{}')
    """

    # get dict of dk players
    d1 = {p['plk']: int(p['dkid']) for p in db.select_dict(q.format(2, 'tm'))}
    d2 = {p['plk']: int(p['dkid']) for p in db.select_dict(q.format(3, 'tm'))}
    d3 = {p['plk']: int(p['dkid']) for p in db.select_dict(q.format(1, 'main'))}
    dkpl = merge({}, [d1,d2,d3])

    # now get dict of mfl players
    mflp = {}
    for p in mfl_players_web(2018):
        ln, fn = p['name'].split(', ')
        k = '{} {}_{}_{}'.format(fn, ln, _fix_team(p['team']), p['position'])
        mflp[k] = int(p['id'])
    
    # get mfl_dk_xref dict
    dk_mfl_d = mfl_dk_xref(db, first='dk')
        
    # now try to match
    intable = 0
    unmatched = []
    mflk = list(mflp.keys())
    for k,v in dkpl.items():
        # look for match in existing cross-reference table
        # can skip if already have in table
        if dk_mfl_d.get(v):
            intable += 1
            continue
    
        # look for direct key match
        m = mflp.get(k)
        if m:
            matches.append('match {} to {} - {}'.format(k, v, m))
        else:
            m, conf = player_match_fuzzy(k, mflk)
            if conf >= 90:
                matches.append('match {} to {} - {}'.format(k, v, mflp.get(m)))
            else:
                m = player_match_interactive(k, mflk)
                if m:
                    matches.append('match {} to {} - {}'.format(k, v, mflp.get(m)))
                else:
                    unmatched.append((k,v))

    return(matches, unmatched)

if __name__ == '__main__':
    #db = getdb('nfl')
    #run()
    pass
