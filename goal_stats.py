#!/usr/bin/python

import collections
import logging
import logging.handlers
import operator
import os
import os.path
import pymongo
import sys
import time

import goals
import incremental_scanner
import utils


# Module-level logging instance
log = logging.getLogger(__name__)

def main(args):
    c = utils.get_mongo_connection()
    goal_db = c.test.goals
    gstats_db = c.test.goal_stats
    all_goals = goals.goal_check_funcs.keys()
    total_pcount = collections.defaultdict(int)
    goal_scanner = incremental_scanner.IncrementalScanner('goals', c.test)
    stat_scanner = incremental_scanner.IncrementalScanner('goal_stats', c.test)

    if not args.incremental:
        log.warning('resetting scanner and db')
        stat_scanner.reset()
        gstats_db.remove()

    log.info("Starting run: %s", stat_scanner.status_msg())

    # TODO: The following logic doesn't work now that goal calculation doesn't happen with a scanner.
    # if goal_scanner.get_max_game_id() == stat_scanner.get_max_game_id():
    #     log.info("Stats already set! Skip")
    #     exit(0)

    log.info('all_goals %s', all_goals)
    for goal_name in all_goals:
        log.info("Working on %s", goal_name)
        found_goals = list(goal_db.find({'goals.goal_name': goal_name}))
        total = len(found_goals)
        log.info("Found %d instances of %s", total, goal_name)

        pcount = collections.defaultdict(int)
        for goal in found_goals:
            player = goal['goals'][0]['player']
            pcount[player] += 1
            total_pcount[player] += 1

        psorted = sorted(pcount.iteritems(), key=operator.itemgetter(1), 
                         reverse=True)
        top = []
        leaders = 0
        i = 0
        while leaders < 3 and i < len(psorted):
            (player, count) = psorted[i]
            players = [player]
            i += 1
            while i < len(psorted) and psorted[i][1] == count:
                players.append(psorted[i][0])
                i += 1
            leaders += len(players)
            top.append((players, count))
			
        mongo_val = {'_id': goal_name, 'count': total, 'top': top}
        gstats_db.save(mongo_val)

    stat_scanner.set_max_game_id(goal_scanner.get_max_game_id())
    stat_scanner.save()
    log.info("Ending run: %s", stat_scanner.status_msg())


if __name__ == '__main__':
    args = utils.incremental_max_parser().parse_args()

    script_root = os.path.splitext(sys.argv[0])[0]

    # Configure the logger
    log.setLevel(logging.DEBUG)

    # Log to a file
    fh = logging.handlers.TimedRotatingFileHandler(script_root + '.log',
                                                   when='midnight')
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

    main(args)
