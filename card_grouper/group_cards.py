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
import scipy.spatial.distance as distance

def main():
    ARCH = 'Archivist'
    card_data = json.load(open('card_conditional_data.json'))
    card_names = card_info.card_names()
    card_names.remove(ARCH)
    card_inds = {}
    for ind, card_name in enumerate(card_names):
        card_inds[card_name] = ind
    N = len(card_inds)
    
    # cluster based on gain prob, win rate given any gained, 
    # avg gained per game, and win rate per gain
    M = 4
    grouped_data = np.zeros((N, M, N))
    for card_row in card_data:
        card_name = card_row['card_name']
        condition = card_row['condition'][0]
        if card_name == ARCH or condition == ARCH:
            continue
        assert len(card_row['condition']) == 1
        if card_name == condition:
            continue
        i = card_inds[card_name]
        j = card_inds[condition]
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
    
    #z = scipy.cluster.hierarchy.ward(flattened_normed_data)
    #scipy.cluster.hierarchy.dendrogram(z, labels=card_names)

    for i in range(N):
        dists_for_i = []
        for j in range(N):
            if i != j:
                dist = distance.cosine(
                    flattened_normed_data[i], flattened_normed_data[j])
                dists_for_i.append((dist, card_names[j]))
        dists_for_i.sort()
        print card_names[i], ':', ', '.join([n for (d, n) in dists_for_i][:10])
    

if __name__ == '__main__':
    main()
