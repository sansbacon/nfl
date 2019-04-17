'''

# nfl/pgf.py
# interactive search of player_game_finder

'''

import pandas as pd
from .gf import GameFinder


class PlayerGameFinder(GameFinder):
    '''
    Interactive command line app

    '''

    prompt = "player_game_finder> "
    intro = "Welcome to Player Game Finder! Type ? to list commands"

    def do_search(self, inp):
        '''
        Search for stats

        Args:
            None

        Returns:
            None

        '''
        vals = self.gf_search(inp)
        try:
            df = pd.DataFrame(vals)
            df = self.clean_results(df, self.pos)
            if self.pos == 'QB':
                cols = self.basecols + self.qbcols
            else:
                cols = self.basecols + self.flexcols
            self.print_results(df[cols])
        except:
            print('could not convert to dataframe')
            self.do_settings('')


if __name__ == "__main__":
    pass
