# tests/test_gf.py

from io import StringIO
import logging
import sys
import unittest
from unittest.mock import patch

import pandas as pd

from nfl.gf import GameFinder
from nfl.seasons import current_season_year
import pytest


logger = logging.getLogger(__name__)


class Gf_test(unittest.TestCase):
    '''
    Test methods based on https://stackoverflow.com/questions/34500249/
                          writing-unittest-for-python3-shell-based-on-cmd-module
    '''

    def create(self):
        '''

        '''
        return GameFinder()

    def test_clean_results(self):
        '''

        Returns:

        '''
        cli = self.create()
        df = pd.read_json('../data/gf_dataframe.json')

        # test qb columns
        clean_df = cli.clean_results(df, 'qb')
        for qbcol in cli.qbcols:
            assert qbcol in clean_df.columns

        # test flex columns
        clean_df = cli.clean_results(df, 'rb')
        for flexcol in cli.flexcols:
            assert flexcol in clean_df.columns

        # test invalid position
        # list function then arguments rather than calling function
        with pytest.raises(AttributeError):
            cli.clean_results(df, 0.0)

    @unittest.skip
    def test_gf_search(self):
        '''

        Returns:

        '''
        cli = self.create()
        if not cli.seas:
            cli.seas = 2018
        if not cli.opp:
            cli.opp = 'CHI'
        if not cli.pos:
            cli.pos = 'TE'
        vals = cli.gf_search()
        assert isinstance(vals, list)
        logger.info(vals)
        #self.assertIsInstance(vals[0], dict)

    def test_opp(self):
        """
        Tesing `opp` command

        """
        cli = self.create()

        # opp identical to pfr team code
        opp = 'gnb'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd(f'opp {opp}')
        assert f'Set opp to {opp}' == fakeOutput.getvalue().strip()

        # convert opp to valid pfr team code
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd('opp gb')
        assert 'Set opp to gnb' == fakeOutput.getvalue().strip()

        # invalid pfr team code
        opp = 'nx'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd(f'opp {opp}')
        assert f"Invalid team code: {opp}" == fakeOutput.getvalue().strip()

    def test_pos(self):
        """
        Tesing `pos` command

        """
        cli = self.create()

        # valid uppercase pos code
        pos = 'QB'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd(f'pos {pos}')
        assert f'Set pos to {pos}' == fakeOutput.getvalue().strip()

        # valid lowercase pos code
        pos = 'wr'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd(f'pos {pos}')
        assert f'Set pos to {pos.upper()}' == fakeOutput.getvalue().strip()

        # invalid pos code
        pos = 'k'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd(f'pos {pos}')
        assert f"Invalid position: {pos}" == fakeOutput.getvalue().strip()

    def test_seas(self):
        """
        Tesing `seas` command

        """
        cli = self.create()

        # valid season
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd('seas 2018')
        assert 'Set seas to 2018' == fakeOutput.getvalue().strip()

        # invalid season returns current season
        seas = current_season_year()
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd('seas x')
        assert f'Set seas to {seas}' == fakeOutput.getvalue().strip()

    def test_settings(self):
        """
        Tesing `setting` command

        """
        cli = self.create()

        # valid season
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd('settings')
        return_value = fakeOutput.getvalue().strip()
        assert 'seas' in return_value
        assert 'pos' in return_value
        assert 'thresh' in return_value

    def test_thresh(self):
        """
        Tesing `thresh` command

        """
        cli = self.create()

        # valid thresh
        thresh = 2.5
        cmd = f'thresh {thresh}'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd(cmd)
        assert f'Set thresh to {thresh}' == fakeOutput.getvalue().strip()

        # invalid thresh returns error message
        thresh = 'x'
        cmd = f'thresh {thresh}'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            assert not cli.onecmd(cmd)
        assert f"Invalid threshold {thresh}" == fakeOutput.getvalue().strip()

    def test_exit(self):
        """
        Test exit command

        """
        cli = self.create()

        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            # is True because onecmd returns flag indicating
            # whether interpretation of commands should stop
            assert cli.onecmd('exit')
        assert 'Bye' == fakeOutput.getvalue().strip()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
