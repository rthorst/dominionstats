#!/usr/bin/python

import sys
sys.path.append('..')
import card_info
import scipy.cluster
from sklearn import preprocessing
import scipy.cluster.hierarchy 
import numpy as np
import simplejson as json
from stats import MeanVarStat
from collections import defaultdict

def main():
    card_data = json.load(open('card_conditional_data.json'))
    N = len(card_info.card_names())
    
    # cluster based on gain prob, win rate given any gained, 
    # avg gained per game, and win rate per gain
    M = 4
    grouped_data = np.zeros((N, M, N))
    for card_row in card_data:
        card_name = card_row['card_name']
        condition = card_row['condition'][0]
        assert len(card_row['condition']) == 1
        if card_name == condition:
            continue
        i = card_info.card_index(card_name)
        j = card_info.card_index(condition)
        stats = card_row['stats']
        def parse(key):
            ret = MeanVarStat()
            ret.from_primitive_object(stats[key])
            return ret
        wgag = parse('win_given_any_gain')
        wgng = parse('win_given_no_gain')
        wwg = parse('win_weighted_gain')
        total_games = wgag.frequency() + wgng.frequency()
        grouped_data[i][0][j] = wgag.frequency() / total_games
        grouped_data[i][1][j] = wgag.mean()
        #grouped_data[i][2][j] = wwg.frequency() / total_games
        # grouped_data[i][3][j] = wwg.mean()

    for i in range(N):
        for j in range(M):
            s = sum(grouped_data[i][j])
            # make the self data == avg
            grouped_data[i][j][i] = s / (N - 1)

    for i in range(N):
        for j in range(M):
            grouped_data[i][j] = preprocessing.scale(grouped_data[i][j])
    
    flattened_normed_data = np.zeros((N, N * M))
    for i in range(N):
        flattened = grouped_data[i].flatten()
        assert len(flattened) == N * M, '%d != %d' % (len(flattened), N * M)
        flattened_normed_data[i] = flattened
    
    z = scipy.cluster.hierarchy.ward(flattened_normed_data)
    scipy.cluster.hierarchy.dendrogram(z, labels=card_info.card_names())
    
    

if __name__ == '__main__':
    main()
