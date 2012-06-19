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
import pylab

def trim(acceptable_func, existing_matrix, existing_card_names):
    num_rows = 0
    for card in existing_card_names:
        if acceptable_func(card):
            num_rows += 1
    new_cards = []
    new_mat = np.zeros((num_rows, existing_matrix.shape[1]))
    for card, row in zip(existing_card_names, existing_matrix):
        if acceptable_func(card):            
            new_mat[len(new_cards)] = row
            new_cards.append(card)
    return new_mat, new_cards


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

    flattened_normed_data, card_names = trim(
        lambda x: (card_info.cost(x)[0] >= '5' or 
                   card_info.cost(x)[0] == '1' or 
                   card_info.cost(x)[0] == 'P') and not (
            x in card_info.EVERY_SET_CARDS or 
            card_info.cost(x)[0:2] == '*0'),
        flattened_normed_data, card_names)
    
    z = scipy.cluster.hierarchy.ward(flattened_normed_data)
    scipy.cluster.hierarchy.dendrogram(z, labels=card_names,
                                       orientation='left', leaf_font_size=4.5)
    pylab.savefig('expensive_group_win_prob.png', 
                  dpi=len(card_names) * 2.5, bbox_inches='tight')
                  

    # for i in range(N):
    #     dists_for_i = []
    #     for j in range(N):
    #         if i != j:
    #             dist = distance.cosine(
    #                 flattened_normed_data[i], flattened_normed_data[j])
    #             dists_for_i.append((dist, card_names[j]))
    #     dists_for_i.sort()
    #     print card_names[i], ':', ', '.join([n for (d, n) in dists_for_i][:10])
    

if __name__ == '__main__':
    main()
