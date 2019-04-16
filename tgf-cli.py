#!/usr/bin/env python3

'''

# tgf-cli.py
# interactive search of player_game_finder
# shows defense vs. position (team totals)

'''
import logging

import click

from nfl.tgf import TeamGameFinder

@click.command()
@click.option('-y', '--seas', default=None, type=click.IntRange(2010, 2021),
                 help='NFL season')
@click.option('-p', '--pos', type=click.Choice(['qb', 'wr', 'te', 'rb']),
                 default=None, help='Player position')
@click.option('-o', '--opp', type=str, default=None,
                 help='Team code')
@click.option('-t', '--thresh', type=click.FloatRange(0, 20), default=0,
                 help='Fantasy points threshold')
def run(seas, pos, opp, thresh):
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler("/tmp/tgf.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.ERROR)
    tgf = TeamGameFinder(seas, pos, opp, thresh)
    tgf.cmdloop()


if __name__ == '__main__':
    run()
