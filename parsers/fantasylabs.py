import json
import logging


class FantasyLabsNFLParser():
    '''
    FantasyLabsNFLParser

    Usage:

        from FantasyLabsNFLScraper import FantasyLabsNFLScraper
        from FantasyLabsNFLParser import FantasyLabsNFLParser
        s = FantasyLabsNFLScraper()
        p = FantasyLabsNFLParser()

        # games
            games_json = s.games()
            games = p.games(games_json)
        
        # models
            model_json = s.model()
            players = p.model(model_json)

        # weekly
            from nfl.parsers import fantasylabs
            from nfl.db import nflpg

            logging.basicConfig(level=logging.DEBUG)
            fn = '/home/sansbacon/9_14_2016.json'
            with open(fn, 'r') as infile:
                content = infile.read()

            p = fantasylabs.FantasyLabsNFLParser()
            players = p.dk_salaries(content, 2016, 2)
            nflp = nflpg.NFLPostgres(user='postgres', password='cft091146', database='nfl')
            nflp.insert_dicts(players, 'salaries')

                ## step five: update player_id
            q = "
                update salaries s
                set player_id = sq.player_id
                from (
                    SELECT player_id, site_player_id
                    FROM player_xref
                    WHERE site = '{site}'
                ) sq
                WHERE s.source_player_id = sq.site_player_id AND s.season = {season} AND s.week = {week} AND s.player_id is null;
           "
           nflp.update(q.format(season, week))
    '''

    def __init__(self,**kwargs):
        '''

        '''
        logging.getLogger(__name__).addHandler(logging.NullHandler())
                        

    def games(self, content, **kwargs):
        '''
        Parses json that is list of games

        Usage:
            games = p.games(games_json)
            games = p.games(games_json, omit=[])

        '''

        if 'omit' in kwargs:
            omit = kwargs['omit']

        else:
            omit = ['ErrorList', 'ReferenceKey', 'HomePrimaryPlayer', 'VisitorPrimaryPlayer', 'HomePitcherThrows', 'VisitorPitcherThrows','LoadWeather', 'PeriodDescription', 'IsExcluded' 'AdjWindBearing', 'AdjWindBearingDisplay', 'SelectedTeam', 'IsWeatherLevel1', 'IsWeatherLevel2', 'IsWeatherLevel3', 'WeatherIcon', 'WeatherSummary', 'EventWeather', 'EventWeatherItems', 'UseWeather']

        games = []

        try:
            parsed = json.loads(content)

        except:
            logging.error('parser.today(): could not parse json')
            return None

        if parsed:
            for item in parsed:
                game = {k:v for k,v in item.items() if not k in omit}
                games.append(game)
            
        return games

    def model(self, content, site=None):
        '''
        Parses json associated with model (player stats / projections)
        The model has 3 dicts for each player: DraftKings, FanDuel, Yahoo
        SourceIds: 4 is DK, 11 is Yahoo, 3 is FD

        Usage:
            model = p.model(model_json)
            model = p.model(model_json, site='dk')
            model = p.model(model_json, site='fd')
            model = p.model(model_json, site='yahoo')
            model = p.model(model_json, omit_properties=[])
            model = p.model(model_json, omit_other=[])

        '''

        players = {}

        omit_properties = ['IsLocked']
        omit_other = ['ErrorList', 'LineupCount', 'CurrentExposure', 'ExposureProbability', 'IsExposureLocked', 'Positions', 'PositionCount', 'Exposure', 'IsLiked', 'IsExcluded']

        try:
            parsed = json.loads(content)

        except:
            logging.error('could not parse json')

        if parsed:
            for playerdict in parsed.get('PlayerModels'):
                player = {}

                for k,v in playerdict.items():

                    if k == 'Properties':

                        for k2,v2 in v.items():

                            if not k2 in omit_properties:
                                player[k2] = v2

                    elif not k in omit_other:
                        player[k] = v

                # test if already have this player
                # use list where 0 index is DK, 1 FD, 2 Yahoo
                pid = player.get('PlayerId', None)
                pid_players = players.get(pid, [])
                pid_players.append(player)
                players[pid] = pid_players

        if site:
            site_players = []
            
            site_ids = {'dk': 4, 'fd': 3, 'yahoo': 11}               

            for pid, player in players.items():
                for p in player:
                    if p.get('SourceId', None) == site_ids.get(site, None):
                        site_players.append(p)

            players = site_players
        
        return players

    def dk_salaries(self, content, season, week, db=True):
        '''
        Gets list of salaries for insertion into database
        Args:
            content (str):
            season (int):
            week (int):
            db (bool):

        Returns:
            players (list): of player dict
        '''

        site = 'dk'
        wanted = ['Score', 'Player_Name', 'Position', 'Team', 'Ceiling', 'Floor', 'Salary', 'AvgPts', 'p_own', 'PlayerId']
        salaries = [{k:v for k,v in p.items() if k in wanted} for p in self.model(content, site=site)]

        # add columns to ease insertion into salaries table
        if db:
            fixed = []
            for salary in salaries:
                fx = {'source': 'fantasylabs', 'dfs_site': site, 'season': season, 'week': week}
                fx['source_player_id'] = salary.get('PlayerId')
                fx['player'] = salary.get('Player_Name')
                fx['salary'] = salary.get('Salary')
                fx['team'] = salary.get('Team')
                fx['pos'] = salary.get('Position')
                fixed.append(fx)
            salaries = fixed

        return salaries

if __name__ == "__main__":
    pass
