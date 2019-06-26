"""

# tests/test_db.py

"""

import logging
import random
import sys
import unittest

import sqlalchemy
from sqlalchemy.orm import Session

from playermatcher.db import setup


logger = logging.getLogger()
logger.level = logging.ERROR


class Db_test(unittest.TestCase):
    """
    Tests db

    """
    def setUp(self):
        """

        Returns:

        """
        stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(stream_handler)

    def test_setup(self):
        """

        Returns:

        """
        dbname = 'sqlite'
        dbfile = '../playermatcher.sqlite'
        Base, eng, session = setup(database=dbname,
                                      database_file=dbfile)
        self.assertIsInstance(eng, sqlalchemy.engine.base.Engine)
        self.assertIsInstance(session, Session)
        self.assertIsInstance(Base, sqlalchemy.ext.declarative.api.DeclarativeMeta)

        dbname = 'pg'
        Base, eng, session = setup(database=dbname)
        self.assertIsInstance(eng, sqlalchemy.engine.base.Engine)
        self.assertIsInstance(session, Session)
        self.assertIsInstance(Base, sqlalchemy.ext.declarative.api.DeclarativeMeta)


if __name__=='__main__':
    unittest.main()
