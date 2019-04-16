'''

# nfl/pgf.py
# interactive search of player_game_finder

'''

import pandas as pd
from fcache.cache import FileCache
from nfl.gf import GameFinder


class PlayerGameFinder(GameFinder):
    '''
    Interactive command line app

    '''

    prompt = "player_game_finder> "
    intro = "Welcome to Player Game Finder! Type ? to list commands"

    def __init__(self, *args):
        '''
        Creates interactive app

        '''
        super(PlayerGameFinder, self).__init__(*args)
        self.cache = FileCache('pgf', flag='cs')

    def do_search(self, inp):
        '''
        Search for stats

        Args:
            None

        Returns:
            None

        '''
        extra_params = {
            "opp_id": self.opp,
            "pos[]": self.pos,
            "c2val": self.thresh,
            "year_min": self.seas,
            "year_max": self.seas
        }

        try:
            content = self._s.player_game_finder(extra_params)
            vals = self._p.player_game_finder(content)
        except Exception as e:
            print(e)
            print(self._s.urls[-1])
        try:
            df = pd.DataFrame(vals)
            df = self.clean_results(df, self.pos)
            if self.pos == 'QB':
                cols = self.basecols + self.qbcols
            else:
                cols = self.basecols + self.flexcols
            self.print_results(df[cols])
        except:
            print('could not get dataframe')
            self.do_settings('')


if __name__ == "__main__":
    pass
