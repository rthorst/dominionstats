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

def ranking_accuracy(ranker, golden_ranks):
    good_pairs = 0
    total_pairs = 0
    
    for perm in golden_ranks:
        errors_by_card = collections.defaultdict(int)
        for lesser, greater in itertools.combinations(perm, 2):
            if ranker.score(greater) > ranker.score(lesser):
                good_pairs += 1
            else:
                errors_by_card[greater] -= 1
                errors_by_card[lesser] += 1
            total_pairs += 1
        sorted_errors = sorted(errors_by_card.items(), key = lambda x: x[1])
        def print_card(card_pos):
            c = card_pos[0]
            print c, card_pos[1], ranker.extract_features(c), perm.index(c)
        print_card(sorted_errors[0])
        print_card(sorted_errors[-1])
        print
    return float(good_pairs) / total_pairs

def ranking_margin_diff(ranker, golden_ranks):
    acc = 0
    qual_sum = 0
    for perm in golden_ranks:
        for item in perm:
            qual_sum += ranker.score(item)
    for lesser, greater in itertools.combinations(perm, 2):
        score_diff = (ranker.score(greater) - ranker.score(lesser)) / qual_sum
        exp_score_diff = math.exp(score_diff)
        exp_score_diff = min(exp_score_diff, 1)
        acc += score_diff
    return acc
    

class Ranker:
    def __init__(self, extractors_with_weights):
        self.extractors = [e for e, _ in extractors_with_weights]
        self.weights = numpy.array([w for _, w in extractors_with_weights])

    def extract_features(self, card):
        features = numpy.zeros(len(self.extractors))
        for ind, extractor in enumerate(self.extractors):
            features[ind] = extractor(card)
        return features

    def score(self, card):
        return numpy.dot(self.extract_features(card), self.weights)

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
        weights = weights / numpy.linalg.norm(weights)
        self.ranker.weights = weights
        acc = self.acc_func(self.ranker, self.rankings)
        real_acc = ranking_accuracy(self.ranker, self.rankings)
        print acc, real_acc
        return -acc

def main():
    rankings = read_ranks_file('qvist_rankings.txt')
    ranker = Ranker([
            #(win_margin, 1.287),
            #(prob_win_margin, 1),
            #(win_given_no_gain, -.05),
            #(win_weighted_gain, 1.0),
            #(frequency_purchased, .1),
            #(frequency_weighted_win_margin, .01),
            (win_given_any_gain, 2.5),
            (log_odds_any_gained, .05),
            (num_plus_actions, -.03),
            (has_vp, -.1),
            (is_reaction, .1),
            ])
    rank_eval = RankEvaluator(ranker, rankings, ranking_accuracy)
    print scipy.optimize.fmin(rank_eval, rank_eval.ranker.weights)
    # print ranking_accuracy(ranker, rankings)
    

if __name__ == '__main__':
    main()
