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

class NearestNeighborTable:
    def __init__(self, data, card_names, order_only):
        self.card_names = card_names
        self.dists_per_card = self.compute_pairwise_distances(data, order_only)
        thresholds = self.compute_group_thresholds()
        self.partitions_by_card = self.partition_according_to_thresholds(
            thresholds)

    def compute_pairwise_distances(self, data, order_only):
        dists_per_card = []
        N = len(data)
        for i in range(N):
            dists_for_i = []
            for j in range(N):
                if i != j:
                    dist = distance.cosine(data[i], data[j])
                    dists_for_i.append((dist, self.card_names[j]))
            dists_for_i.sort()
            if order_only:
                for j, (dist, other_card) in enumerate(dists_for_i):
                    dists_for_i[j] = (dist / 10000 + j, other_card)
            dists_per_card.append(dists_for_i)
        return dists_per_card

    def compute_group_thresholds(self):
        all_dists = []
        for dist in self.dists_per_card:
            all_dists.extend(d for d, c in dist)
        all_dists.sort()
        NUM_DISTS = len(all_dists)

        interesting_quantiles = [.005, .01, .02, .04]

        interesting_dist_thresholds = [
            all_dists[int(q * NUM_DISTS)] for q in 
            interesting_quantiles]
        interesting_dist_thresholds.append(all_dists[-1])
        return interesting_dist_thresholds

    def partition_according_to_thresholds(self, interesting_dist_thresholds):
        partitions_by_card = {} # dict[card] -> list_#parts(list(card))
        for card_name, dists_list in zip(self.card_names, 
                                         self.dists_per_card):
            card_partitions = [list() for i in xrange(len(
                        interesting_dist_thresholds))]
            for dist, ocard in dists_list:
                for idx, threshold in enumerate(interesting_dist_thresholds):
                    if dist < threshold:
                        card_partitions[idx].append(ocard)
                        break
            partitions_by_card[card_name] = card_partitions            
        return partitions_by_card

    def is_singleton(self, card):
        return not any(len(p) for p in self.partitions_by_card[card][:-1])

    def compute_card_order(self):
        unused, card_order = self.card_names[:], []
        # Arbitrarily pick hunting party as the first card.
        card_order.append('Hunting Party')
        unused.remove('Hunting Party')

        card_inds = {}
        for idx, card in enumerate(self.card_names):
            card_inds[card] = idx
        
        while unused:
            last_card = card_order[-1]
            for dist, card in self.dists_per_card[card_inds[last_card]]:
                if card in unused:
                    unused.remove(card)
                    card_order.append(card)
                    break
        return card_order

    def render_as_html(self):
        def linkable_name(name):
            return name.replace(' ', '').replace("'", '')
        def link_card(name):
             return '<a href="#%s">%s</a> ' % (linkable_name(name), name)
        ret = '<table border=1>'
                    
        for card_name in self.compute_card_order():
            partitions = self.partitions_by_card[card_name]
            ret += '<tr><td><a name=%s>%s</a></td>' % (
                linkable_name(card_name), link_card(card_name))
            printed_any = False
            for partition in partitions[:-1]:
                ret += '<td>'
                for other_card in partition:
                    printed_any = True
                    ret += link_card(other_card)
                ret += '</td>'
            ret += '<td>'
            if not printed_any:
                ret += link_card(partitions[-1][0])
            ret += '</td></tr>'
        ret += '</table>'
        return ret


def plot_points(X, names):
    x_min, x_max = np.min(X, 0), np.max(X, 0)
    X = (X - x_min) / (x_max - x_min)
    #if spread_min:
        #X = spread_points(X, spread_min):
    pylab.figure()
    for coords, name in itertools.izip(X, names):
        pylab.text(coords[0], coords[1], name)
    pylab.savefig('projected_cards.png')
    pylab.show()

def dump_json(coords, names, abbrevs, fn):
    output_contents = []
    for coord, name, abbrev in itertools.izip(coords, names, abbrevs):
        row = {}
        row['x'] = coord[0]
        row['y'] = coord[1]
        row['name'] = name
        row['abbrev'] = abbrev
        output_contents.append(row)
    import simplejson as json
    json.dump(output_contents, open(fn, 'w'))

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

    fixed_radius_nn_table = NearestNeighborTable(
        flattened_normed_data, card_names, False)
    open('fixed_radius_nn_table.html', 'w').write(
        fixed_radius_nn_table.render_as_html())
    knn_table = NearestNeighborTable(
        flattened_normed_data, card_names, True)
    open('knn_table.html', 'w').write(knn_table.render_as_html())

    # flattened_normed_data, card_names = trim(
    #     lambda x: not (card_info.cost(x)[0] >= '5' or 
    #                card_info.cost(x)[0] == '1' or 
    #                card_info.cost(x)[0] == 'P') and not (
    #         x in card_info.EVERY_SET_CARDS or 
    #         card_info.cost(x)[0:2] == '*0'),
    #     flattened_normed_data, card_names)
        
    #n_neighbors = 15
    #n_components = 2
    #iso_data = manifold.Isomap(15, 2).fit_transform(flattened_normed_data)
    abbrevs = map(card_info.abbrev, card_names)
    #plot_points(iso_data, abbrevs)
    # dump_json(iso_data, card_names, abbrevs, 'iso_card_coords.json')

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
