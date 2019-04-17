'''

# nfl/gf.py
# interactive search of player_game_finder

'''

from cmd import Cmd
import logging
from pathlib import Path
from pprint import pprint

try:
    import readline
except ImportError:
    readline = None

from fcache.cache import FileCache

import pandas as pd

from .pfr import Scraper, Parser
from .seasons import current_season_year


class GameFinder(Cmd):
    '''
    Interactive command line app

    '''

    histfile = str(Path.home() / f'.{__name__}_history')
    histfile_size = 1000

    def __init__(self, **kwargs):
        '''
        Creates interactive app

        # pylint: disable=too-many-instance-attributes
        '''
        super(GameFinder, self).__init__()
        logging.getLogger(__name__).addHandler(logging.NullHandler())


        if kwargs.get('cache_name'):
            self.cache = FileCache(kwargs['cache_name'], flag='cs')
            self._s = Scraper(cache_name=kwargs['cache_name'])
        else:
            self.cache = FileCache('gf', flag='cs')
            self._s = Scraper(cache_name='gf')

        if kwargs.get('opp'):
            self.opp = kwargs['opp']
        else:
            self.opp = self.cache.get('opp')

        if kwargs.get('pos'):
            self.pos = self.positions.get(kwargs['pos'])
        else:
            self.pos = self.positions.get(self.cache.get('pos'))

        if kwargs.get('seas'):
            self.seas = kwargs['seas']
        else:
            self.seas = self.cache.get('seas')

        if kwargs.get('thresh'):
            self.thresh = kwargs['thresh']
        else:
            self.thresh = self.cache.setdefault('thresh', 0)

        if kwargs.get('path'):
            try:
                self.path = Path(kwargs['path'])
            except:
                self.path = Path('/tmp')
        else:
            self.path = Path('/tmp')

        self.dfs = self.cache.setdefault('dfs', {})
        self._p = Parser()

    @property
    def basecols(self):
        '''

        Returns:

        '''
        return [
            "player",
            "pos",
            "week",
            "team",
        ]

    @property
    def flexcols(self):
        '''

        Returns:

        '''
        return [
                "targets",
                "rec",
                "rec_yds",
                "rec_td",
                "rush_att",
                "rush_yds",
                "rush_td",
                "dkpts",
        ]

    @property
    def positions(self):
        '''

        Returns:

        '''
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
    def qbcols(self):
        '''

        Returns:

        '''
        return [
            "pass_att",
            "pass_cmp",
            "pass_yds",
            "pass_td",
            "rush_att",
            "rush_yds",
            "rush_td",
            "dkpts",
        ]

    @property
    def team_codes(self):
        '''

        Returns:

        '''
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

    def _dump_msg(self, msg):
        '''
        Standard message format

        Args:
            msg:

        Returns:

        '''
        print("\n", "\n", msg, "\n")

    def clean_results(self, df, pos):
        '''

        Args:
            df:
            pos:

        Returns:
            df

        '''
        # clean data by removing NA and duplicate rows
        df = df.rename(columns={'week_num': 'week',
                                'draftkings_points': 'dkpts'})
        df = df.dropna(axis=0, how='all')
        subset_cols = ['player', 'week', 'team']
        df = df.drop_duplicates(subset=subset_cols, keep='first')
        df['week'] = df['week'].astype(int)

        # fix position & relevant columns
        pos = pos.upper()
        if pos == "QB":
            df[self.qbcols] = df[self.qbcols].apply(pd.to_numeric, errors='coerce')
            df = df[self.basecols + self.qbcols]
        else:
            df[self.flexcols] = df[self.flexcols].apply(pd.to_numeric, errors='coerce')
            df['pos'] = df['pos'].replace({'HB': 'RB', 'FB': 'RB'})
            df = df[self.basecols + self.flexcols]
        return df

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
            print(f'Set seas to {self.seas}')

    def do_settings(self, inp):
        '''
        Print current settings

        Args:
            inp:

        Returns:

        '''
        pprint(self.__dict__)

    def do_thresh(self, inp):
        '''
        Set threshold for fantasy points

        Args:
            inp:

        Returns:

        '''
        try:
            self.thresh = float(inp.strip())
            self.cache['thresh'] = self.thresh
            print("Set thresh to {}".format(self.thresh))
        except ValueError as ve:
            logging.exception(ve)
            print(f"Invalid threshold {inp}")

    def gf_search(self):
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
            return self._p.player_game_finder(content)
        except Exception as e:
            print(e)
            print(self._s.urls[-1])
            return None

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
        self._dump_msg(msg)
        return msg

    def help_thresh(self):
        '''
        Help for thresh command

        Returns:

        '''
        msg = "Sets threshold fantasy points to display player, e.g. 5"
        self._dump_msg(msg)
        return msg

    def print_results(self, df, **kwargs):
        """
        Pretty-prints results

        """
        if 'cols' in kwargs:
            cols = kwargs['cols']
        else:
            cols = ['week', 'dkpts']
        if 'order' in kwargs:
            order = kwargs['order']
        elif len(cols) == 2:
            order = [True, False]
        else:
            order = [True for _ in cols]
        print(df.sort_values(cols, ascending=order))

    def preloop(self):
        '''

        Returns:

        '''
        if readline and Path(self.histfile).is_file():
            readline.read_history_file(self.histfile)

    def postloop(self):
        '''

        Returns:

        '''
        if readline:
            readline.set_history_length(self.histfile_size)
            readline.write_history_file(self.histfile)

    def read_csv(self, path):
        '''

        Returns:

        '''
        # Read types first line of csv
        dtypes = {key: value for (key, value) in
                  pd.read_csv(path, nrows=1).iloc[0].to_dict().items() if
                  'date' not in value}

        parse_dates = [key for (key, value) in
                       pd.read_csv(path, nrows=1).iloc[0].to_dict().items() if
                       'date' in value]

        # Read the rest of the lines with the types from above
        return pd.read_csv(path, dtype=dtypes, parse_dates=parse_dates, skiprows=[1])

    def to_csv(self, df, path):
        '''

        Args:
            path:

        Returns:

        '''
        # Prepend dtypes to the top of df
        df2 = df.copy()
        df2.loc[-1] = df2.dtypes
        df2.index = df2.index + 1
        df2.sort_index(inplace=True)
        # Then save it to a csv
        df2.to_csv(path, index=False)

    do_EOF = do_exit
    help_EOF = help_exit


if __name__ == "__main__":
    pass
