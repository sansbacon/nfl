"""

# nfl/tgf.py
# interactive search of team-level stats allowed

"""

import logging
import pandas as pd
from .gf import GameFinder


class TeamGameFinder(GameFinder):
    """
    Interactive command line app

    """

    prompt = "team_game_finder> "
    intro = "Welcome to Team Game Finder! Type ? to list commands"

    @property
    def basecols(self):
        return ["pos", "week", "team"]

    def do_search(self, inp):
        """
        Search for stats

        Args:
            None

        Returns:
            None

        """
        logging.debug(inp)
        file_name = self.path / f"{self.seas}_{self.opp}_{self.pos}.csv"
        if file_name.is_file():
            df = self.read_csv(file_name)
        else:
            vals = self.gf_search()
            df = pd.DataFrame(vals)
            df = self.clean_results(df, self.pos)
        if self.pos == "QB":
            agg_df = df.groupby(self.basecols)[self.qbcols].sum().reset_index()
        else:
            agg_df = df.groupby(self.basecols)[self.flexcols].sum().reset_index()
        self.print_results(agg_df)


if __name__ == "__main__":
    pass
