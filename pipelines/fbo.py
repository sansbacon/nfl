# -*- coding: utf-8 -*-
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())


def snapcounts_table(sc):
    '''
    Converts snapcounts for insertion into extra_fo.snapcounts
        
    Args:
        sc (list): of dict 

    Returns:
        list: of dict
        
    '''
    fixed = []
    wanted = ['season_year', 'week', 'started', 'total_snaps', 'def_snap_pct',
              'def_snaps', 'off_snap_pct', 'off_snaps', 'st_snap_pct', 'st_snaps']
    for p in [item for sublist in sc for item in sublist]:
        fx = {k: v for k, v in p.items() if k in wanted}
        fx['source'] = 'fo_snapcounts'
        fx['source_player_id'] = p['player']
        fx['source_player_name'] = p['player'].split('-')[-1]
        fx['source_player_position'] = p['position']
        fx['source_player_team'] = p['team']
        if p['started'] == 'NO':
            fx['started'] = False
        else:
            fx['started'] = True
        for k2, v2 in p.items():
            if '_pct' in k2:
                pct = v2.replace('%', '')
                fx[k2] = float(pct) / 100
        fixed.append(fx)
    return fixed


if __name__ == '__main__':
    pass