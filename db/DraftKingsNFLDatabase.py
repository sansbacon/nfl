import MySQLdb

class DraftKingsNFLDatabase():

    def get_players(cursor):
        players_sql = 'select full_name, dk_nfl_players_id as pid from dk_nfl_players'
        cursor.execute(players_sql)
        players = {x[0]: x[1] for x in cursor.fetchall()}
        return players

    def insert_entry(self, entry, cursor):
        '''
        TODO: entry dictionary should already have player_id
        :param entry(dict):
        :param cursor(MySQLdb.cursor):
        :return:
        '''

        # Insert into dk_nfl_entries
        entries_columns = ['dk_nfl_contests_id', 'contest_rank', 'entry_id', 'entry_name', 'num_entries', 'points']
        entries_values = [dk_nfl_contests_id, entry['contest_rank'], entry['entry_id'], entry['entry_name'], entry['num_entries'], entry['points']]
        placeholders = ', '.join(['%s'] * len(entries_columns))
        entries_sql = "INSERT into %s ( %s ) VALUES ( %s )" % ('dk_nfl_entries', ', '.join(entries_columns), placeholders)
        cursor.execute(entries_sql, entries_values)

        # Insert into dk_nfl_lineups
        # For each entry, multiple insertion into lineups table, need foreign key dk_nfl_entries_id
        dk_nfl_entries_id = cursor.lastrowid

        for position in ['qb', 'rb1', 'rb2', 'wr1', 'wr2', 'te', 'flex', 'dst']:
            player_id = entry[position]
            lineup_columns = ['dk_nfl_entries_id', 'dk_nfl_players_id']
            lineup_values = [str(dk_nfl_entries_id), str(player_id)]
            placeholders = ', '.join(['%s'] * len(lineup_columns))
            lineup_sql = "INSERT into %s ( %s ) VALUES ( %s )" % ('dk_nfl_lineups', ', '.join(lineup_columns), placeholders)
            cursor.execute(lineup_sql, lineup_values)