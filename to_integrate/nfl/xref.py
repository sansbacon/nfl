"""
xref.py
provides classes for matching players across sites

"""
import abc
import logging
from collections import defaultdict

from playermatcher.match import player_match
from playermatcher.name import first_last


class Site(metaclass=abc.ABCMeta):
    """
    Site subclasses should implement these methods
    https://stackoverflow.com/questions/372042/
    """

    def __init__(self, db):
        """

        Args:
            db(NFLPostgres): instance

        """
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        self.db = db

    @abc.abstractmethod
    def add_xref(self, *players):
        """
        Interface

        Returns:

        """
        raise NotImplementedError("users must define add_xref to use this base class")

    @abc.abstractmethod
    def get_mfld(self, first):
        """
        Interface

        Returns:

        """
        raise NotImplementedError("users must define get_mfld to use this base class")

    @abc.abstractmethod
    def get_players(self):
        """
        Interface

        Returns:

        """
        raise NotImplementedError(
            "users must define get_players to use this base class"
        )

    def get_playersd(
        self,
        dict_key="name",
        id_key="source_player_id",
        name_key="source_player_name",
        pos_key="source_player_position",
    ):
        """
        Gets site players by key

        Args:
            dict_key(str):
            id_key(str):
            name_key(str):
            pos_key(str):

        Returns:
            dict

        """
        players = self.get_players()
        if dict_key == "name":
            playersd = defaultdict(list)
            for p in players:
                playersd[p[name_key]].append(p)
        elif dict_key == "namepos":
            playersd = defaultdict(list)
            for p in players:
                k = (p[name_key], p[pos_key])
                playersd[k].append(p)
        elif dict_key == "id":
            playersd = {p[id_key]: p for p in players}
        else:
            raise ValueError("invalid key %s", dict_key)
        return playersd

    def match_mfl(
        self,
        mfl_players,
        id_key="source_player_id",
        name_key="source_player_name",
        interactive=False,
    ):
        """
        Matches mfl players to site players

        Args:
            mfl_players(list):
            id_key(str):
            name_key(str):
            pos_key(str):
            interactive(bool):

        Returns:
            list: of player

        """
        mfld = self.get_mfld(first="mfl")
        playersd = self.get_playersd("name")
        playernames = list(playersd.keys())

        for idx, p in enumerate(mfl_players):
            # first option is to see if already in database
            if mfld.get(p[id_key]):
                mfl_players[idx][id_key] = mfld[p[id_key]]
                continue

            # if not in database, use matcher
            match_name = player_match(
                first_last(p[name_key]), playernames, thresh=90, interactive=interactive
            )
            match = playersd.get(match_name)
            if match and len(match) == 1:
                mfl_players[idx][id_key] = match[0][id_key]
        return mfl_players


class NFL(Site):
    """
    Used to cross-reference NFL players

    """

    def add_xref(self, *players):
        """
        Adds players to xref table

        Args:
            players: list of dict

        Returns:
            None

        """
        # TODO: implement this
        return None

    def get_mfld(self, first="mfl"):
        """
        Query database for dict to cross-reference nflcom with mfl or vice versa

        Args:
            first(str): which site is first, default 'mfl'

        Returns:
            dict - mfl_player_id: fanball_id or vice versa

        """
        q = """SELECT mfl_player_id as m, nflcom_player_id as f 
               FROM base.player
               WHERE mfl_player_id IS NOT NULL AND
                     nflcom_player_id IS NOT NULL"""
        players = self.db.select_dict(q)
        if first == "mfl":
            return {p["m"]: p["f"] for p in players}
        return {p["m"]: p["f"] for p in players}

    def get_players(self):
        """
        Gets nflcom players from base.player

        Returns:
            list: of dict

        """
        q = """SELECT * FROM base.player
               WHERE nflcom_player_id IS NOT NULL"""
        return self.db.select_dict(q)

    def get_playersd(
        self,
        dict_key="name",
        id_key="nflcom_player_id",
        name_key="full_name",
        pos_key="primary_pos",
    ):
        """
        Gets players by key

        Args:
            key(str):

        Returns:
            dict

        """
        return super().get_playersd(dict_key, id_key, name_key, pos_key)

    def match_mfl(
        self,
        mfl_players,
        id_key="nflcom_player_id",
        name_key="full_name",
        interactive=False,
    ):
        """
        Matches mfl players to fanball players

        Args:
            mfl_players(list):
            id_key(str):
            name_key(str):
            pos_key(str):
            interactive(bool):

        Returns:
            list: of player

        """
        return super().match_mfl(mfl_players, id_key, name_key, interactive)


class PFF(Site):
    """
    Used to cross-reference PFF players

    """

    def add_xref(self, *players):
        """
        Adds players to xref table

        Args:
            players: list of dict

        Returns:
            None

        """
        # TODO: implement this
        return None

    def get_mfld(self, first="mfl"):
        """
        Query database for dict to cross-reference fanball with mfl or vice versa

        Args:
            first(str): which site is first, default 'mfl'

        Returns:
            dict - mfl_player_id: fanball_id or vice versa

        """
        q = """SELECT mfl_player_id as m, pff_player_id as f FROM dfs.pff_mfl_xref"""
        players = self.db.select_dict(q)
        if first == "mfl":
            return {p["m"]: p["f"] for p in players}
        return {p["m"]: p["f"] for p in players}

    def get_players(self):
        """
        Gets MFL players from salary table

        Returns:
            list

        """
        q = """SELECT * FROM base.player_xref WHERE source = 'pff'"""
        return self.db.select_dict(q)


if __name__ == "__main__":
    pass
