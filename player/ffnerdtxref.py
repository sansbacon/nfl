# ffnerdxref.py

from fuzzywuzzy import process
from nfl.player.playerxref import nflcom_players

def ffnerd_xref(db, ffnpls):
    '''
    Cross-reference fantasyfootballnerd.com and nfl.com players
    
    Args:
        players: 

    Returns:
        list of dict
    '''
    leftovers = []
    nflp = nflcom_players(db)

    for idx, dpl in enumerate(ffnpls):
        k = dpl['source_player_name'] + '_' + dpl['source_player_position']
        match = nflp.get(k)
        if match and len(match) == 1:
            ffnpls[idx]['nflcom_player_id'] = nflp[k][0]['player_id']
        elif match and len(match) > 1:
            print('duplicate for {}'.format(k))
        else:
            fuzzy, confidence = process.extractOne(k, list(nflp.keys()))
            if confidence > .95:
                match = nflp.get(fuzzy)
                pieces = ['ffnerd', str(dpl['source_player_id']), dpl['source_player_name'],
                          dpl['source_player_position'], dpl['source_player_dob'],
                          match[0]['player_id'], match[0]['full_name']]
                print(', '.join(pieces))
                try:
                    resp = input()
                except:
                    resp = raw_input()
                if resp == 'x' or resp == 'n':
                    leftovers.append(', '.join(pieces))
                else:
                    ffnpls[idx]['nflcom_player_id'] = match[0]['player_id']
            else:
                print('could not match {}'.format(k))

    return leftovers

def xref_update_db(db, players):
    '''
    TODO: this should be moved to agent?
    Updates database with items that have nflcom_player_id
    '''
    wanted = ['source', 'source_player_id', 'source_player_name', 'nflcom_player_id',
              'source_player_dob', 'source_player_position',]
    for dpl in [p for p in players if p.get('nflcom_player_id')]:
        # ffnerd has player DOB, so can use to try to match to nflcom
        pl = {k: v for k, v in dpl.items() if k in wanted}

        # filter out invalid dob
        if '0000' in pl.get('source_player_dob', ''):
            pl['source_player_dob'] = None

        db._insert_dict(pl, 'extra_misc.player_xref')

if __name__ == '__main__':
    pass
    '''
    import json

    from nfl.parsers.ffnerd import FFNerdNFLParser
    from nfl.player.ffnerdtxref import ffnerd_xref
    from nfl.scrapers.ffnerd import FFNerdNFLScraper
    
    scraper = FFNerdNFLScraper(api_key='8x3g9y245w6a')
    parser = FFNerdNFLParser()
    
    content = scraper.players(pos='K')
    players = parser.players(content)
    
    fixed = []                                                                                                                        
    for p in players:                                                                                                                   
        f = {'source': 'ffnerd'}                                                                                       
        f['source_player_name'] = p['displayName']          
        f['source_player_id'] = p['playerId']                              
        f['source_player_position'] = p['position']                            
        f['source_player_dob'] = p['dob']
        fixed.append(f) 
    
    leftovers = ffnerd_xref(db, fixed) 
    
    wanted = ['source', 'source_player_id', 'source_player_name', 
              'source_player_dob', 'source_player_position', 'nflcom_player_id']
    
    for dpl in [p for p in fixed if p.get('nflcom_player_id')]:
        pl = {k:v for k,v in dpl.items() if k in wanted}
        if '0000' in pl.get('source_player_dob', ''):
            pl['source_player_dob'] = None
        db._insert_dict(pl, 'extra_misc.player_xref')
        logging.info('added {}'.format(pl))
    '''