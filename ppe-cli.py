#!/usr/bin/env python3

'''

# ppe-cli.py
# interactive search of playerprofiler

'''

import logging
import click
from nfl.ppe import PlayerProfilerExplorer


@click.command()
@click.option('-h', '--path', type=str, default='/tmp',
                 help='Save path')
@click.option('-f', '--file_name', type=str,
                 help='Path for pp lookup json file')
@click.option('-c', '--cache_name', type=str, default='pgf-cli',
                 help='Name for cache')
def run(path, file_name, cache_name):
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler(f"{path}/tgf.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.ERROR)
    ppe = PlayerProfilerExplorer(file_name, cache_name=cache_name)
    ppe.cmdloop()


if __name__ == '__main__':
    run()
