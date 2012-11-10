#!/usr/bin/python

import logging
import logging.handlers
import os
import os.path
import re
import sys

import utils

from keys import *


# Module-level logging instance
log = logging.getLogger(__name__)


INDEXES = {
    'games': [
        PLAYERS,
        SUPPLY,
        ],
    'raw_games': [
        'game_date',
        ],
    'goals': [
        'goals.player',
        ],
    }


def ensure_all_indexes(db):
    """Ensure all expected indexes are in place, for all tables"""
    for table_name, index_list in INDEXES.items():
        for index in index_list:
            log.info("Ensuring %s index for %s", index, table_name)
            db[table_name].ensure_index(index)


def main():
    con = utils.get_mongo_connection()
    ensure_all_indexes(con.test)


if __name__ == '__main__':
    args = utils.incremental_parser().parse_args()

    script_root = os.path.splitext(sys.argv[0])[0]

    # Create the basic logger
    #logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    # Log to a file
    fh = logging.handlers.TimedRotatingFileHandler(script_root + '.log', when='midnight')
    if args.debug:
        fh.setLevel(logging.DEBUG)
    else:
        fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # Put logging output on stdout, too
    ch = logging.StreamHandler(sys.stdout)
    if args.debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    main()
    
