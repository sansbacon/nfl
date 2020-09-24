"""

# nfl/ppe.py
# player profiler explorer

"""

from cmd import Cmd
import logging
import os
from pathlib import Path

import json

from pprint import pprint

try:
    import readline
except ImportError:
    readline = None

from fcache.cache import FileCache

from .pp import Scraper, Parser
from namematcher import match_fuzzy, match_interactive


def read_json(file_name):
    """

    Args:
        file_name:

    Returns:

    """
    with open(file_name, "r") as f:
        return json.load(f)


class PlayerProfilerExplorer(Cmd):
    """
    Interactive command line app

    """

    histfile = str(Path.home() / f".{__name__}_history")
    histfile_size = 1000

    prompt = "player_profiler explorer> "
    intro = "Welcome to Player Profiler Explorer! Type ? to list commands"

    def __init__(self, file_name, **kwargs):
        """
        Creates interactive app

        # pylint: disable=too-many-instance-attributes
        """
        super().__init__()
        logging.getLogger(__name__).addHandler(logging.NullHandler())

        if kwargs.get("cache_name"):
            self.cache = FileCache(kwargs["cache_name"], flag="cs")
            self._s = Scraper(cache_name=kwargs["cache_name"])
        else:
            self.cache = FileCache("ppe", flag="cs")
            self._s = Scraper(cache_name="ppe")
        self._p = Parser()
        self.player_lookup = read_json(file_name)

    def _dump_msg(self, msg):
        """
        Standard message format

        Args:
            msg:

        Returns:

        """
        print("\n", "\n", msg, "\n")

    def do_exit(self, inp):
        """
        Quit app

        Args:
            inp:

        Returns:

        """
        print("Bye %s" % inp)
        return True

    def do_search_match(self, name):
        """

        Args:
            name:

        Returns:

        """
        logging.info("trying fuzzy match")
        match_from = list(self.player_lookup.keys())
        match_name, conf = match_fuzzy(name, match_from)
        if conf >= 90:
            return match_name
        logging.info("trying interactive match")
        match_name, conf = match_interactive(name, match_from)
        if match_name:
            return match_name
        return None

    def do_search(self, inp):
        """
        Specify opponent

        Args:
            inp:

        Returns:

        """
        player_code = self.player_lookup.get(inp.strip())
        if not player_code:
            player_name = self.do_search_match(inp.strip())
            player_code = self.player_lookup.get(player_name)
        if player_code:
            print(f"Getting {inp.strip()} {player_code}")
            content = self._s.player_page(player_code)
            player = self._p.player_core(content)
            pprint(player)
        else:
            print(f"Invalid player name: {inp}")

    def help_exit(self):
        """
        Help for quitting application

        Returns:

        """
        msg = "exit the application. Shorthand: x q Ctrl-D."
        self._dump_msg(msg)
        return msg

    def help_search(self):
        """
        Help for search interface

        Returns:

        """
        msg = "Searches playerprofiler for comps"
        self._dump_msg("\n".join(msg))
        return msg

    def preloop(self):
        """

        Returns:

        """
        if readline and Path(self.histfile).is_file():
            readline.read_history_file(self.histfile)

    def postloop(self):
        """

        Returns:

        """
        if readline:
            readline.set_history_length(self.histfile_size)
            readline.write_history_file(self.histfile)

    do_EOF = do_exit
    help_EOF = help_exit


if __name__ == "__main__":
    pass
