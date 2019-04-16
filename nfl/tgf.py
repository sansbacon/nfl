#!/usr/bin/env python3

'''

# nfl/tgf.py
# interactive search of team-level stats allowed

'''

from cmd import Cmd
import logging
from pprint import pprint

import os.path
try:
    import readline
except ImportError:
    readline = None

from fcache.cache import FileCache

import pandas as pd

from nfl.pfr import Scraper, Parser
from nfl.seasons import current_season_year


class TeamGameFinder(Cmd):
    '''
    Interactive command line app

    '''

    prompt = "team_game_finder> "
    intro = "Welcome to Team Game Finder! Type ? to list commands"
    histfile = os.path.expanduser('~/.tgf_history')
    histfile_size = 1000

    def __init__(self):
        '''
        Creates interactive app

        '''
        super(TeamGameFinder, self).__init__()
        self._s = Scraper(cache_name="pgf")
        self._p = Parser()
        self.cache = FileCache('tgf', flag='cs')
        self.opp = self.cache.get('opp')
        self.pos = self.cache.get('pos')
        self.seas = self.cache.get('seas')

    @property
    def basecols(self):
        return [
            "pos",
            "week_num",
            "team",
        ]

    @property
    def qbcols(self):
        return [
            "pass_att",
            "pass_cmp",
            "pass_yds",
            "pass_td",
            "rush_att",
            "rush_yds",
            "rush_td",
            "draftkings_points",
        ]

    @property
    def flexcols(self):
        return [
                "targets",
                "rec",
                "rec_yds",
                "rec_td",
                "rush_att",
                "rush_yds",
                "rush_td",
                "draftkings_points",
        ]

    @property
    def positions(self):
        return {
            "qb": "QB",
            "rb": "RB",
            "te": "TE",
            "wr": "WR",
            "QB": "QB",
            "RB": "RB",
            "TE": "TE",
            "WR": "WR"
        }

    @property
    def team_codes(self):
        return {
            'ari': 'crd',
            'crd': 'crd',
            'atl': 'atl',
            'rav': 'rav',
            'bal': 'rav',
            'buf': 'buf',
            'car': 'car',
            'chi': 'chi',
            'cin': 'cin',
            'cle': 'cle',
            'dal': 'dal',
            'den': 'den',
            'det': 'det',
            'gb': 'gnb',
            'gnb': 'gnb',
            'htx': 'htx',
            'hou': 'htx',
            'clt': 'clt',
            'ind': 'clt',
            'jax': 'jax',
            'jac': 'jax',
            'kan': 'kan',
            'kc': 'kan',
            'sdg': 'sdg',
            'sd': 'sdg',
            'lac': 'sdg',
            'ram': 'ram',
            'stl': 'ram',
            'lar': 'ram',
            'la': 'ram',
            'mia': 'mia',
            'min': 'min',
            'nwe': 'nwe',
            'ne': 'nwe',
            'nor': 'nor',
            'no': 'nor',
            'nyg': 'nyg',
            'nyj': 'nyj',
            'rai': 'rai',
            'oak': 'rai',
            'phi': 'phi',
            'pit': 'pit',
            'sfo': 'sfo',
            'sf': 'sfo',
            'sea': 'sea',
            'tam': 'tam',
            'tb': 'tam',
            'ten': 'oti',
            'oti': 'oti',
            'was': 'was'
        }

    def _conv_col(self, v):
        """
        Converts value to float or zero

        Args:
            v:

        Returns:
            float

        """
        try:
            return float(v)
        except ValueError:
            return 0.0

    def _dump_msg(self, msg):
        '''
        Standard message format

        Args:
            msg:

        Returns:

        '''
        print("\n", "\n", msg, "\n")

    def _dump_search(self, df, pos):
        """
        Pretty-prints results

        """
        # clean data by removing NA and duplicate rows
        df = df.dropna(axis=0, how="all")
        subset_cols = ["player", "week_num", "team"]
        df = df.drop_duplicates(subset=subset_cols, keep="first")
        df['week_num'] = df['week_num'].astype(int)

        if pos == "QB":
            df[self.qbcols] = df[self.qbcols].apply(pd.to_numeric, errors='coerce')
            agg_df = df.groupby(self.basecols)[self.qbcols].sum().reset_index()
        elif pos in ["RB", "WR", "TE"]:
            df[self.flexcols] = df[self.flexcols].apply(pd.to_numeric, errors='coerce')
            df['pos'] = df['pos'].replace({'HB': 'RB', 'FB': 'RB'})
            agg_df = df.groupby(self.basecols)[self.flexcols].sum().reset_index()

        # cleanup resuls
        if 'week_num' in agg_df.columns:
            agg_df = agg_df.rename(columns={'week_num': 'week'})
        if 'draftkings_points' in agg_df.columns:
            agg_df = agg_df.rename(columns={'draftkings_points': 'dkpts'})

        # sort values
        print(agg_df.sort_values('week'))

    def do_exit(self, inp):
        '''
        Quit app

        Args:
            inp:

        Returns:

        '''
        print("Bye")
        return True

    def do_opp(self, inp):
        '''
        Specify opponent

        Args:
            inp:

        Returns:

        '''
        tc = self.team_codes.get(inp.lower())
        if tc:
            self.opp = tc
            self.cache['opp'] = tc
            print(f"Set opp to {self.opp}")
        else:
            print(f"Invalid team code: {inp}")
            print(f"Valid codes are: \n{self.team_codes.keys()}")

    def do_pos(self, inp):
        '''
        Set position for search

        Args:
            inp:

        Returns:

        '''
        pos = self.positions.get(inp.strip())
        if pos:
            self.pos = pos
            self.cache['pos'] = pos
            print(f"Set pos to {self.pos}")
        else:
            print(f"Invalid position: {inp}")
            print(f"Valid positions are: \n{self.positions}")

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
            df.to_csv('tgf.csv', index=False)
            self._dump_search(df, self.pos)
        except Exception as e:
            print(e)
        finally:
            return None

    def do_seas(self, inp):
        '''
        Sets season

        Args:
            inp:

        Returns:

        '''
        try:
            self.seas = int(inp)
        except ValueError:
            self.seas = current_season_year()
        finally:
            self.cache['seas'] = self.seas
            print(f'set seas to {self.seas}')

    def do_settings(self, inp):
        '''
        Print current settings

        Args:
            inp:

        Returns:

        '''
        pprint({k:v for k,v in self.__dict__.items() if not '_' in k})

    def help_exit(self):
        '''
        Help for quitting application

        Returns:

        '''
        msg = ("exit the application. Shorthand: x q Ctrl-D.")
        self._dump_msg(msg)
        return msg

    def help_opp(self):
        '''
        Help on specifying opponent

        Returns:

        '''
        msg = "Sets opponent or shows valid opponents, e.g. car"
        self._dump_msg(msg)
        return msg

    def help_pos(self):
        '''
        Help for position command

        Returns:

        '''
        msg = "Sets position or shows valid positions, e.g. QB"
        self._dump_msg(msg)
        return msg

    def help_search(self):
        '''
        Help for search interface

        Returns:

        '''
        msg = (
            "Searches pfr for positional results vs. team",
            "Can use opp, pos, and thresh and pass no parameters"
        )
        self._dump_msg("\n".join(msg))
        return msg

    def help_seas(self):
        '''
        Help for seas command

        Returns:
            None

        '''
        msg = "Sets season year"
        self._dump_msg(msg)
        return msg

    def help_settings(self):
        '''
        Help for printing settings

        Returns:

        '''
        msg = "Shows current settings, such as opp, pos, and thresh"
        print("\n", msg, "\n")
        return msg

    def preloop(self):
        '''

        Returns:

        '''
        if readline and os.path.exists(self.histfile):
            readline.read_history_file(self.histfile)

    def postloop(self):
        '''

        Returns:

        '''
        if readline:
            readline.set_history_length(self.histfile_size)
            readline.write_history_file(self.histfile)

    do_EOF = do_exit
    help_EOF = help_exit


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler("/tmp/pgf.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.ERROR)
    TeamGameFinder().cmdloop()
