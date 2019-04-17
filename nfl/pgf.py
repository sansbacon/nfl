'''

# nfl/pgf.py
# interactive search of player_game_finder

'''
import logging

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
            inp(str):

        Returns:
            None

        '''
        logging.debug(inp)
        file_name = self.path / f'{self.seas}_{self.opp}_{self.pos}.csv'
        if file_name.is_file():
            df = self.read_csv(file_name)
            self.print_results(df)
        else:
            vals = self.gf_search()
            df = pd.DataFrame(vals)
            df = self.clean_results(df, self.pos)
            if self.pos == 'QB':
                cols = self.basecols + self.qbcols
            else:
                cols = self.basecols + self.flexcols
            self.to_csv(df[cols], file_name)
            self.print_results(df[cols])


if __name__ == "__main__":
    pass
