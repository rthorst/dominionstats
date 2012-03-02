#!/usr/bin/python

import os
import pymongo
import re
import sys

import argparse
import utils

from keys import *

parser = utils.incremental_date_range_cmd_line_parser()
find_id = re.compile('game-.*.html')

def process_file(filename, incremental, games_table):
    yyyymmdd = filename[:8]

    if incremental:
        contents = open('parsed_out/' + filename, 'r').read()
        if contents.strip() == '[]':
            print "empty contents (make parser not dump empty files?)", \
                  filename
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
            print "Found all games in DB, deleting file"
            os.system('rm parsed_out/%s'%filename)
            return
    
    cmd = ('mongoimport -h localhost parsed_out/%s -c '
           'games --jsonArray' % filename)
    print cmd
    os.system(cmd)


def main():
    args = parser.parse_args()
    games_table = pymongo.Connection().test.games
    games_table.ensure_index(PLAYERS)
    games_table.ensure_index(SUPPLY)
    data_files_to_load = os.listdir('parsed_out')
    data_files_to_load.sort()

    for fn in data_files_to_load:
        yyyymmdd = fn[:8]
        if not utils.includes_day(args, yyyymmdd):
            print 'skipping', fn, 'because not in range'
            continue
        process_file(fn, args.incremental, games_table)

if __name__ == '__main__':
    main()
