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
            for playerdict in parsed.get('PlayerModels', []):
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
        
if __name__ == "__main__":
    pass
