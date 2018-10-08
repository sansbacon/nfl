# scripts/mfl-fd-match.py
# matches mfl and fd players


from nfl.utility import merge, getdb
from nfl.player.mflxref import *
from nfl.player.playerxref import player_match_fuzzy, player_match_interactive


def match(db):
    '''

    Args:
        db(NFLPostgres):

    Returns:
        tuple

    '''
    q = """
      SELECT 
        source_player_id as fdid,
        concat_ws('_', source_player_name, source_team_id, dfs_position) as plk 
      FROM dfs.fn_fdsal_sws(2018, {}, '{}')
    """

    # get dict of dk players
    d1 = {p['plk']: p['fdid'] for p in db.select_dict(q.format(2, 'tm'))}
    d2 = {p['plk']: p['fdid'] for p in db.select_dict(q.format(3, 'tm'))}
    d3 = {p['plk']: p['fdid'] for p in db.select_dict(q.format(1, 'main'))}
    fdpl = merge({}, [d1,d2,d3])

    # now get dict of mfl players
    mflp = {}
    for p in mfl_players_web(2018):
        ln, fn = p['name'].split(', ')
        k = '{} {}_{}_{}'.format(fn, ln, p['team'], p['position'])
        mflp[k] = int(p['id'])
    
    # get mfl_fd_xref dict
    fd_mfl_d = mfl_fd_xref(db, first='fd')
        
    # now try to match
    intable = 0
    matches = []
    unmatched = []
    mflk = list(mflp.keys())
    for k,v in fdpl.items():
        # look for match in existing cross-reference table
        # can skip if already have in table
        if fd_mfl_d.get(v):
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
    db = getdb('nfl')
    match(db)
