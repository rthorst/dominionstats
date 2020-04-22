#!/usr/bin/python

import logging
import logging.handlers
import os
import os.path
import pymongo
import re
import sys

import utils

from keys import *

parser = utils.incremental_date_range_cmd_line_parser()
find_id = re.compile('game-.*.html')

def process_file(filename, incremental, games_table, log):
    yyyymmdd = filename[:8]

    if incremental:
        contents = open('parsed_out/' + filename, 'r').read()
        if contents.strip() == '[]':
            log.warning("empty contents in %s (make parser not dump empty files?)", filename)
            return

        assert find_id.search(contents), (
            'could not get id from %s in file %s' % (contents[:100], filename))

        found_all = True
        for match in find_id.finditer(contents):
            g_id = match.group(0)
            query = {'_id': g_id}
            if games_table.find(query).count():
                continue
            else:
                found_all = False
        if found_all:
            log.info("Found all games in DB, deleting file %s", filename)
            os.system('rm parsed_out/%s'%filename)
            return
    
    cmd = ('mongoimport -h localhost parsed_out/%s -c '
           'games --jsonArray' % filename)
    print(cmd)
    os.system(cmd)


def main(args, log):

    if args.incremental:
        log.info("Performing incremental parsing from %s to %s", args.startdate, args.enddate)
    else:
        log.info("Performing non-incremental (re)parsing from %s to %s", args.startdate, args.enddate)

    games_table = pymongo.MongoClient().test.games
    games_table.ensure_index(PLAYERS)
    games_table.ensure_index(SUPPLY)
    data_files_to_load = os.listdir('parsed_out')
    data_files_to_load.sort()

    for fn in data_files_to_load:
        yyyymmdd = fn[:8]
        if not utils.includes_day(args, yyyymmdd):
            log.debug("Parsed games for %s available in the filesystem but not in date range, skipping", yyyymmdd)
            continue
        process_file(fn, args.incremental, games_table, log)


if __name__ == '__main__':
    args = utils.incremental_date_range_cmd_line_parser().parse_args()

    script_root = os.path.splitext(sys.argv[0])[0]

    # Create the basic logger
    #logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Log to a file
    fh = logging.handlers.TimedRotatingFileHandler(script_root + '.log', when='midnight')
    if args.debug:
        fh.setLevel(logging.DEBUG)
    else:
        fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Put logging output on stdout, too
    ch = logging.StreamHandler(sys.stdout)
    if args.debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    main(args, logger)
    
