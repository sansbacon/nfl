# tests/test_pgf.py

from io import StringIO
import logging
import sys
import unittest
from unittest.mock import patch

from nfl.pgf import PlayerGameFinder


class Pgf_test(unittest.TestCase):
    '''
    Test methods based on https://stackoverflow.com/questions/34500249/
                          writing-unittest-for-python3-shell-based-on-cmd-module
    '''

    def create(self):
        '''

        '''
        return PlayerGameFinder()

    @unittest.skip
    def test_do_search(self):
        '''

        Returns:

        '''
        cli = self.create()

        # valid season
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd('settings'))
        return_value = fakeOutput.getvalue().strip()
        self.assertIsNotNone(return_value)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()

