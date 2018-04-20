# fbdb.py
# pipeline for footballdatabase stats

wanted = ['season_year', 'week', 'source', 'source_player_id',
          'source_player_name', 'source_player_position']

offensive_bonuses = {
    'passing_yards': {'threshold': 300, 'bonus': 3},
    'rushing_yards': {'threshold': 100, 'bonus': 3},
    'receiving_yards': {'threshold': 100, 'bonus': 3},
}
          
vals = []
for p in fbdb_gl:
    p2 = {k:v for k,v in p.items() if k in wanted}
    p2['source_team_id'] = p['source_player_team']
    p2['nflcom_player_id'] = fbdbp.get(p2['source_player_id'])

    # now need to calculate other scoring
    if 'std' in p['scoring_format'] or 'standard' in p['scoring_format']:
        p2['fantasy_points_std'] = float(p['fantasy_points'])
        p2['fantasy_points_ppr'] = p2['fantasy_points_std'] + float(p['rec_rec'])
        p2['fantasy_points_hppr'] = round((p2['fantasy_points_ppr'] + p2['fantasy_points_std'])/2, 1)
        p2['fanduel_points'] = p2['fantasy_points_hppr']
        p2['draftkings_points'] = p2['fantasy_points_ppr']
        
        for key in offensive_bonuses:
            if p2.get(key, 0) >= offensive_bonuses[key]['threshold']:
                p2['draftkings_points'] += offensive_bonuses[key]['value'] 
        vals.append(p2)
