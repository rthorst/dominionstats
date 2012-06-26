import itertools
import pymongo
import csv
import sys
import random
import copy
import pprint

def table_avg(table, level):
     return sum(level[player] for player in table) / len(table)

def imbalance(tables, level, avg):
    badness = 0
    for table in tables:
        avg_in_table = table_avg(table, level)
        badness += (avg_in_table - avg) ** 2
    return badness

def neighbors(tables):
    for ind1, ind2 in itertools.combinations(range(len(tables)), r = 2):
        for p1, p2 in itertools.product(tables[ind1][1:], 
                                        tables[ind2][1:]):
            new = copy.deepcopy(tables)
            new[ind1].remove(p1)
            new[ind2].remove(p2)
            new[ind1].append(p2)
            new[ind2].append(p1)
            yield new

def greedy_hillclimb(tables, level):
    avg = sum(level.values()) / float(len(level))
    cur_score = imbalance(tables, level, avg)
    last_score = 1e9
    while last_score != cur_score > 0:
        tables = min(neighbors(tables), key=lambda t: imbalance(t, level, avg))
        last_score = cur_score
        cur_score = imbalance(tables, level, avg)
        print cur_score
    return tables


if __name__ == '__main__':
    fn = 'DS_entrants.csv'
    names = []
    skip_first = True
    for record in csv.reader(open(fn)):
        if skip_first:
            skip_first = False
            continue
        names.append(record[1])
    level = {}
    c = pymongo.Connection()
    level_history_collection = c.test.leaderboard_history
    for name in names:
        level_info = level_history_collection.find_one({'_id': name})
        if level_info:
            last_level_info = level_info['history'][-1]
            level[name] = last_level_info[1] - last_level_info[2]
            if level[name] < 0:
                level[name] = 0
        else:
            level[name] = 0
    name_level_pairs = level.items()
    name_level_pairs.sort(key = lambda x: -x[1])
    top_seeds, others = [], []
    cut_off = len(name_level_pairs) / 4
    for ind, (name, _) in enumerate(name_level_pairs):
        if ind <= cut_off:
            top_seeds.append(name)
        else:
            others.append(name)
    random.shuffle(others)
    output_tables = [[top_seed] for top_seed in top_seeds]
    cur_place = len(top_seeds) - 1
    while len(others):
        output_tables[cur_place].append(others.pop())
        cur_place -= 1
        if cur_place < 0:
            cur_place = len(top_seeds) - 1
    output_tables = greedy_hillclimb(output_tables, level)
    for table in output_tables:
        for player in table:
            print player + ',',
        for player in table:
            print level[player],
        print table_avg(table, level)
            
        
