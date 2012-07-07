#!/usr/bin/python

import sys
sys.path.append('..')

from collections import defaultdict
from sklearn import manifold, decomposition
from sklearn import preprocessing
from sklearn.metrics import euclidean_distances
from stats import MeanVarStat
import card_info
import itertools
import numpy as np
import pylab
import scipy.cluster
import scipy.cluster.hierarchy 
import scipy.spatial.distance as distance
import simplejson as json

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

# http://forum.dominionstrategy.com/index.php?topic=647.msg8951#msg8951
bonus_feature_funcs = [
    lambda x: 2 * card_info.coin_cost(x),
    lambda x: 3 * card_info.potion_cost(x),
    lambda x: 3 * card_info.num_plus_actions(x),
    lambda x: 4 * card_info.num_plus_cards(x),
    lambda x: 4 * card_info.is_action(x),
    lambda x: 4 * card_info.is_victory(x),
    lambda x: 4 * card_info.is_treasure(x),
    lambda x: 5 * card_info.is_attack(x),
    lambda x: 1 * card_info.is_reaction(x),
    lambda x: 2 * card_info.vp_per_card(x),
    lambda x: 1 * card_info.money_value(x),
    lambda x: 1 * card_info.num_plus_buys(x),
    # 1 * gains (remodel, upgrade, workshop, ...)
    lambda x: 1 * max(card_info.trashes(x), 5)
    # 6 * pollute (can add to other deck)
    # 3 * combo (conspirator, peddler, ...
    # 3 * special (goons, gardens, uniqueness in general)
    # 3 * discard (militia, minion, 
    # 1 * cycle (vault, cellar, .. )
    # 100 * win rate
    ]

def get_bonus_vec(card_name):
    bonus_vec = np.zeros(len(bonus_feature_funcs))
    for j, feature_func in enumerate(bonus_feature_funcs):
        bonus_vec[j] = feature_func(card_name)
    bonus_vec = bonus_vec * 0.1
    return bonus_vec

def dendro_plot(normed_data, card_names):
    z = scipy.cluster.hierarchy.ward(normed_data)
    scipy.cluster.hierarchy.dendrogram(z, labels=card_names,
                                       orientation='left', leaf_font_size=4.5,
                                       )
    pylab.savefig('expensive_group_win_prob.png', 
                  dpi=len(card_names) * 2.5, bbox_inches='tight')

def nearest_neighbor_table():
    all_dists = []
    dists_per_card = []
    for i in range(N):
        dists_for_i = []
        for j in range(N):
            if i != j:
                dist = distance.cosine(
                    flattened_normed_data[i], flattened_normed_data[j])
                dists_for_i.append((dist, card_names[j]))
                all_dists.append(dist)
        dists_for_i.sort()
        dists_per_card.append(dists_for_i)
        # print card_names[i], ':', ', '.join([n for (d, n) in dists_for_i][:10])
    all_dists.sort()
    VERY_CLOSE_IND = int(len(all_dists) * .005)
    CLOSE_IND = int(len(all_dists) * .01)
    MAYBE_CLOSE_IND = int(len(all_dists) * .02)
    
    VERY_CLOSE_DIST = all_dists[VERY_CLOSE_IND]
    CLOSE_DIST = all_dists[CLOSE_IND]
    MAYBE_CLOSE_DIST = all_dists[MAYBE_CLOSE_IND]
    for card_name, dists_list in zip(card_names, dists_per_card):
        prev_dist = 0
        print card_name, ';',
        for dist, other_card in dists_list:
            if prev_dist <= VERY_CLOSE_DIST < dist:
                print '|',
            if prev_dist <= CLOSE_DIST < dist:
                print '||',
            if prev_dist <= MAYBE_CLOSE_DIST < dist:
                print '|||',
            if dist <= MAYBE_CLOSE_DIST or prev_dist == 0:
                print other_card,
            prev_dist = dist
        print

def plot_points(X, names):
    x_min, x_max = np.min(X, 0), np.max(X, 0)
    X = (X - x_min) / (x_max - x_min)
    pylab.figure()
    for coords, name in itertools.izip(X, names):
        pylab.text(coords[0], coords[1], name)
    pylab.savefig('projected_cards.png')
    pylab.show()

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

    flattened_normed_data = np.zeros((N, 
                                      2 * N * M + len(bonus_feature_funcs)))
    for i in range(N):
        bonus_vec = get_bonus_vec(card_names[i])
        v1, v2 = [], []
        for j in range(M):
            for k in range(N):
                v1.append(grouped_data[i][j][k])
                v2.append(grouped_data[k][j][i])
        v1, v2 = np.array(v1), np.array(v2)
        catted = np.concatenate((v1 * 1 , v2 * 0 , 0 *bonus_vec))
        flattened_normed_data[i] = catted

    flattened_normed_data, card_names = trim(
        lambda x: not (card_info.cost(x)[0] >= '5' or 
                   card_info.cost(x)[0] == '1' or 
                   card_info.cost(x)[0] == 'P') and not (
            x in card_info.EVERY_SET_CARDS or 
            card_info.cost(x)[0:2] == '*0'),
        flattened_normed_data, card_names)
        
    n_neighbors = 15
    n_components = 2
    iso_data = manifold.Isomap(10, 2).fit_transform(flattened_normed_data)
    plot_points(iso_data, card_names)

    # clf = manifold.LocallyLinearEmbedding(n_neighbors=n_neighbors, 
    #                                       n_components=n_components,
    #                                       method='hessian')
    # lle_data = clf.fit_transform(flattened_normed_data)
    # plot_points(lle_data, card_names)
    
    # pca_data = decomposition.RandomizedPCA(
    #     n_components=2).fit_transform(flattened_normed_data)
                                           
    # plot_points(pca_data, card_names)
    

if __name__ == '__main__':
    main()
