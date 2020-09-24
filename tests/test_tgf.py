# tests/test_tgf.py

from io import StringIO
import logging
import sys
import unittest
from unittest.mock import patch

from nfl.tgf import TeamGameFinder


class Pgf_test(unittest.TestCase):
    '''
    Test methods based on https://stackoverflow.com/questions/34500249/
                          writing-unittest-for-python3-shell-based-on-cmd-module
    '''

    def create(self):
        '''

        '''
        return TeamGameFinder()

    @unittest.skip
    def test_do_search(self):
        '''

        Returns:

        '''
        cli = self.create()

        # valid season
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd('settings')
        return_value = fakeOutput.getvalue().strip()
        assert return_value is not None


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()

