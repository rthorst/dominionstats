#!/usr/bin/python

import pymongo
import collections
import operator
import goals
import incremental_scanner
import utils

if __name__ == '__main__':
    c = pymongo.Connection()
    goal_db = c.test.goals
    gstats_db = c.test.goal_stats
    all_goals = goals.goal_check_funcs.keys()
    total_pcount = collections.defaultdict(int)
    goal_scanner = incremental_scanner.IncrementalScanner('goals', c.test)
    stat_scanner = incremental_scanner.IncrementalScanner('goal_stats', c.test)

    parser = utils.incremental_max_parser()
    args = parser.parse_args()
    if not args.incremental:
        stat_scanner.reset()
        gstats_db.remove()

    if goal_scanner.get_max_game_id() == stat_scanner.get_max_game_id():
        print "Stats already set! Skip"
        exit(0)

    print 'all_goals', all_goals
    for goal_name in all_goals:
        found_goals = list(goal_db.find({'goals.goal_name': goal_name}))
        total = len(found_goals)
        print goal_name, total

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

