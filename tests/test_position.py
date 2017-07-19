# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, division


from __future__ import absolute_import, print_function

import logging
import sys
import unittest

from nfl.player.position import position


class position_test(unittest.TestCase):

    def setUp(self):
        pass

    def test_depth_chart(self):
        pos = position('Robert Herron', 'http://www.nfl.com/player/robertherron/2543777/profile')
        self.assertIn(pos, [u'QB', u'RB', u'WR', u'TE', u'UNK'])
        logging.info(pos)


if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    unittest.main()