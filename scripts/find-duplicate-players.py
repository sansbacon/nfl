# scripts/find-duplicate-players.py
# finds duplicate players in the player table

from collections import defaultdict
import datetime

from nfl.utility import getdb


def consolidate_players(l, choice):
    '''
    Combines keys together
    
    Args:
        l(list): of dict
        choice(str): 2 (all), 3 (1 and 2), 4 (1 and 3), 5 (2 and 3)
        
    Returns:
        list: of str
        
    '''
    sql = []
    uq = """UPDATE base.player SET mfl_player_id = {} WHERE player_id = {};"""
    dq = """DELETE FROM base.player WHERE player_id = {};"""
    if choice == '2':
        pass
    elif choice == '3':
        p1, p2 = l
        if p1.get('nflcom_player_id'):
            if not p1.get('mfl_player_id'):
                sql.append(dq.format(p2.get('player_id')))
                sql.append(uq.format(p2.get('mfl_player_id'), 
                                     p1.get('player_id')))
                
    elif choice == '4':
        pass
    elif choice == '5':
        pass
    return sql
    
    
def run():
    db = getdb('nfl')

    dupsq = """
        WITH p AS (
          select *, lower(concat_ws('_', left(first_name,3), last_name, pos)) as pkey
          from base.player
        ),

        p2 AS (
          select *, row_number() OVER (PARTITION BY pkey ORDER BY player_id) as r
          from p
        )

        SELECT * FROM p
        WHERE pkey IN (SELECT DISTINCT pkey FROM p2 WHERE r > 1)
        ORDER BY pkey, player_id
    """

    # create dict where key is pkey and val is list of players with that key
    players_d = defaultdict(list)
    for p in db.select_dict(dupsq):
       players_d[p['pkey']].append(p)

    # loop through values, each one is a list
    # sort by player_id
    for li in players_d.values():
        # get the first player in the list
        players = sorted(li, key=lambda k: k['player_id'])
        for p in players:
            print(p)
        
        # now ask me what to do
        question = """
            Options:
            1. Leave them alone
            2. Consolidate all
            3. Consolidate 1 and 2
            4. Consolidate 1 and 3
            5. Consolidate 2 and 3
            6. Quit
            
        """
        
        # go through the options
        choice = input(question)
        if choice == '1':
            continue
        elif choice in ['2', '3', '4', '5']:
            consolidated = consolidate_players(players, choice)
            print()
            print('\n'.join(consolidated))
        else:
            exit
        
        
if __name__ == '__main__':
    run()
