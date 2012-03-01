#!/usr/bin/python

import sys
sys.path.append('../')

import itertools
import simplejson as json
import card_info
import collections
import primitive_util
import math
import numpy
import numpy.linalg
import small_gain_stat
import stats
import scipy.optimize

numpy.set_printoptions(precision=3)

def read_ranks_file(fn):
    ret = []
    for line in open(fn):
        ret.append(line.strip().split(','))
    return ret

def read_stats(fn):
    parsed_stats = primitive_util.ConvertibleDefaultDict(
        lambda: primitive_util.ConvertibleDefaultDict(stats.MeanVarStat))
    raw_stats = json.load(open('card_stats.json'))
    parsed_stats.from_primitive_object(raw_stats)
    for k in parsed_stats:
        parsed_stats[k] = small_gain_stat.from_raw_stats_dict(parsed_stats[k])
    return parsed_stats

CARD_STATS = read_stats('card_stats.json')

def ranked_pairs(golden_ranks):
    for perm in golden_ranks:
        for lesser, greater in itertools.combinations(perm, 2):
            yield lesser, greater

def display_large_errors(ranker, golden_ranks):
    errors_by_card = collections.defaultdict(int)
    total_compares = collections.defaultdict(int)
    for lesser, greater in ranked_pairs(golden_ranks):
        total_compares[greater] += 1
        total_compares[lesser] += 1
        if ranker.score(greater) < ranker.score(lesser):
            errors_by_card[greater] -= 1
            errors_by_card[lesser] += 1

    def accuracy(card_pos_tuple):
        card = card_pos_tuple[0]
        return errors_by_card[card] / float(total_compares[card])
    sorted_errors = sorted(errors_by_card.items(), key=accuracy)

    def print_card(card_pos):
        c = card_pos[0]
        print c, ranker.extract_features(c)

    num_printed = 5
    print 'underrated'
    for ind in range(num_printed):
        print_card(sorted_errors[ind])
    print 'overrated'
    for ind in range(1, num_printed + 1):
        print_card(sorted_errors[-ind])

def ranking_errors(ranker, golden_ranks):
    bad_pairs, total_pairs = 0, 0
    for lesser, greater in ranked_pairs(golden_ranks):
        if ranker.score(greater) < ranker.score(lesser):
            bad_pairs += 1
        total_pairs += 1
    return float(bad_pairs) / total_pairs
    
def ranking_log_loss(ranker, golden_ranks):
    log_loss = 0
    for lesser, greater in ranked_pairs(golden_ranks):
        exp_score_diff = math.exp(
            ranker.score(lesser) - ranker.score(greater))
        prob = 1 / (1 + exp_score_diff)
        log_loss += math.log(prob)
    return log_loss

class Ranker:
    def __init__(self, extractors_with_weights):
        self.extractors = [e for e, _ in extractors_with_weights]
        self.weights = numpy.array([w for _, w in extractors_with_weights])
        self.features = numpy.zeros((len(card_info.card_names()),
                                     len(self.weights)))
        for ind, card in enumerate(card_info.card_names()):
            if card in card_info.EVERY_SET_CARDS:
                continue
            self.features[ind] = self.extract_features(card)

    def extract_features(self, card):
        features = numpy.zeros(len(self.extractors))
        for ind, extractor in enumerate(self.extractors):
            features[ind] = extractor(card)
        return features

    def score(self, card):
        return self.score_ind(card_info.card_index(card))

    def score_ind(self, card_ind):
        return numpy.dot(self.features[card_ind], self.weights)

def win_given_any_gain(card):
    return CARD_STATS[card].win_given_any_gain.mean()

def win_given_no_gain(card):
    return CARD_STATS[card].win_given_no_gain.mean()

def win_weighted_gain(card):
    return CARD_STATS[card].win_weighted_gain.mean()

def frequency_purchased(card):
    card_stat = CARD_STATS[card]
    return card_stat.win_weighted_gain.frequency() / (
        card_stat.win_given_any_gain.frequency() +
        card_stat.win_given_no_gain.frequency())

def frequency_weighted_win_margin(card):
    card_stat = CARD_STATS[card]
    return (frequency_purchased(card) * 
            card_stat.win_weighted_gain.mean() - 1)

def win_margin(card):
    card_stat = CARD_STATS[card]
    return float(card_stat.win_given_any_gain.mean() - 
                 card_stat.win_given_no_gain.mean())

def prob_win_margin(card):
    return (prob_any_gained(card) * win_margin(card))

def prob_any_gained(card):
    card_stat = CARD_STATS[card]
    wagf = float(card_stat.win_given_any_gain.frequency())
    wngf = card_stat.win_given_no_gain.frequency()
    return wagf / (wagf + wngf)

def log_odds_any_gained(card):
    p = prob_any_gained(card)
    if p >= .995:  # this happens due to oddness with tournament winnings
        return 1
    return math.log(p / (1 - p))

def trashing(card):
    return card_info.trashes(card)

def num_plus_actions(card):
    return card_info.num_plus_actions(card) 

def has_vp(card):
    return card_info.is_victory(card)

def is_reaction(card):
    return card_info.is_reaction(card)

class RankEvaluator:
    def __init__(self, ranker, rankings, acc_func):
        self.ranker = ranker
        self.rankings = rankings
        self.acc_func = acc_func

    def __call__(self, weights):
        self.ranker.weights = weights
        errors = self.acc_func(self.ranker, self.rankings)
        real_errors = ranking_errors(self.ranker, self.rankings)
        weight_penalty = .5
        print errors, real_errors
        return -errors + weight_penalty * numpy.linalg.norm(weights)

def main():
    rankings = read_ranks_file('qvist_rankings.txt')
    ranker = Ranker([
            #(win_margin, 1.287),
            #(prob_win_margin, 1),
            #(win_given_no_gain, -.05),
            #(win_weighted_gain, 20),
            #(frequency_purchased, .1),
            #(frequency_weighted_win_margin, .01),
            (win_given_any_gain, 30),
            (log_odds_any_gained, 1.3),
            (num_plus_actions, -1),
            (has_vp, -1.5),
            (is_reaction, 1.5),
            ])
    # this should really be doing cross validation
    rank_eval = RankEvaluator(ranker, rankings, ranking_log_loss)
    learned_weights = [ 52.926,   1.358,  -1.161,  -1.712,   1.626]
    ranker.weights = learned_weights
    learned_weights = scipy.optimize.fmin_bfgs(
        rank_eval, rank_eval.ranker.weights, gtol=1e-3)
    ranker.weights = learned_weights 
    print learned_weights
    display_large_errors(ranker, rankings)
 
    grouped_by_cost = collections.defaultdict(list)
    for card in card_info.card_names():
        grouped_by_cost[card_info.cost(card)].append(card)
    for cost, card_list in grouped_by_cost.iteritems():
        if len(card_list) >= 4:
            card_list.sort(key=ranker.score)
            #print cost, ','.join(card_list)
    

if __name__ == '__main__':
    main()
