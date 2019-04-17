# tests/test_gf.py

from io import StringIO
import logging
import pickle
import sys
import unittest
from unittest.mock import patch

from nfl.gf import GameFinder
from nfl.seasons import current_season_year


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
        with open('../data/gf_dataframe.pkl', 'rb') as f:
            df = pickle.load(f)

        # test qb columns
        clean_df = cli.clean_results(df, 'qb')
        for qbcol in cli.qbcols:
            self.assertIn(qbcol, clean_df.columns)

        # test flex columns
        clean_df = cli.clean_results(df, 'rb')
        for flexcol in cli.flexcols:
            self.assertIn(flexcol, clean_df.columns)

        # test invalid position
        # list function then arguments rather than calling function
        self.assertRaises(AttributeError, cli.clean_results, df, 0.0)

    def test_opp(self):
        """
        Tesing `opp` command

        """
        cli = self.create()

        # opp identical to pfr team code
        opp = 'gnb'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd(f'opp {opp}'))
        self.assertEqual(f'Set opp to {opp}', fakeOutput.getvalue().strip())

        # convert opp to valid pfr team code
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd('opp gb'))
        self.assertEqual('Set opp to gnb', fakeOutput.getvalue().strip())

        # invalid pfr team code
        opp = 'nx'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd(f'opp {opp}'))
        self.assertEqual(f"Invalid team code: {opp}", fakeOutput.getvalue().strip())

    def test_pos(self):
        """
        Tesing `pos` command

        """
        cli = self.create()

        # valid uppercase pos code
        pos = 'QB'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd(f'pos {pos}'))
        self.assertEqual(f'Set pos to {pos}', fakeOutput.getvalue().strip())

        # valid lowercase pos code
        pos = 'wr'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd(f'pos {pos}'))
        self.assertEqual(f'Set pos to {pos.upper()}', fakeOutput.getvalue().strip())

        # invalid pos code
        pos = 'k'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd(f'pos {pos}'))
        self.assertEqual(f"Invalid position: {pos}", fakeOutput.getvalue().strip())

    def test_seas(self):
        """
        Tesing `seas` command

        """
        cli = self.create()

        # valid season
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd('seas 2018'))
        self.assertEqual('Set seas to 2018', fakeOutput.getvalue().strip())

        # invalid season returns current season
        seas = current_season_year()
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd('seas x'))
        self.assertEqual(f'Set seas to {seas}', fakeOutput.getvalue().strip())

    def test_settings(self):
        """
        Tesing `setting` command

        """
        cli = self.create()

        # valid season
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd('settings'))
        return_value = fakeOutput.getvalue().strip()
        self.assertIn('seas', return_value)
        self.assertIn('pos', return_value)
        self.assertIn('thresh', return_value)

    def test_thresh(self):
        """
        Tesing `thresh` command

        """
        cli = self.create()

        # valid thresh
        thresh = 2.5
        cmd = f'thresh {thresh}'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd(cmd))
        self.assertEqual(f'Set thresh to {thresh}', fakeOutput.getvalue().strip())

        # invalid thresh returns error message
        thresh = 'x'
        cmd = f'thresh {thresh}'
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            self.assertFalse(cli.onecmd(cmd))
        self.assertEqual(f"Invalid threshold {thresh}", fakeOutput.getvalue().strip())

    def test_exit(self):
        """
        Test exit command

        """
        cli = self.create()

        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            # is True because onecmd returns flag indicating
            # whether interpretation of commands should stop
            self.assertTrue(cli.onecmd('exit'))
        self.assertEqual('Bye', fakeOutput.getvalue().strip())


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()
