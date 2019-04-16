#!/usr/bin/env python3

'''

# nfl/tgf.py
# interactive search of team-level stats allowed

'''

from fcache.cache import FileCache
import pandas as pd
from nfl.gf import GameFinder

class TeamGameFinder(GameFinder):
    '''
    Interactive command line app

    '''

    prompt = "team_game_finder> "
    intro = "Welcome to Team Game Finder! Type ? to list commands"

    def __init__(self, *args):
        '''
        Creates interactive app

        '''
        super(TeamGameFinder, self).__init__(*args)
        self.cache = FileCache('tgf', flag='cs')

    @property
    def basecols(self):
        return [
            "pos",
            "week",
            "team",
        ]


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
            "pos[]": self.pos.upper(),
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
            if self.pos == "QB":
                agg_df = df.groupby(self.basecols)[self.qbcols].sum().reset_index()
            else:
                agg_df = df.groupby(self.basecols)[self.flexcols].sum().reset_index()
            self.print_results(agg_df)
        except Exception as e:
            print('could not get dataframe')
            print(e)
            self.do_settings('')


if __name__ == "__main__":
    pass
