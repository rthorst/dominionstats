""" Compute correlations between winning and some interesting events."""

from __future__ import division

import os

import analysis_util
import dominioncards
from game import Game
import incremental_scanner
import pymongo
import collections
import simplejson as json

from small_gain_stat import SmallGainStat
import utils


def card_supply_events(game_obj):
    yield ''
    for card1 in game_obj.get_supply():
        c1_index = str(card1.index)
        yield c1_index
        for card2 in game_obj.get_supply():
            c2_index = str(card2.index)
            if c1_index > c2_index:
                yield c1_index + ',' + c2_index

def month_events(game_obj):
    yield Game.get_date_from_id(game_obj.get_id())[:6]

def game_size_events(game_obj):
    yield str(len(game_obj.get_player_decks()))

events_func_label = '_events'
event_detectors = [(g[:-len(events_func_label)], eval(g))
                   for g in locals().keys() if g.endswith(events_func_label)]

def detect_events(game):
    """ Return a dict of lists, where the keys are event names, and the
    values are events of those type that occured in game."""
    ret = collections.defaultdict(list)
    for event_detector_name, detector in event_detectors:
        for event in detector(game):
            ret[event_detector_name].append(event)
    return ret

class EventAccumulator:
    """ A class for accumulating and serializing SmallGainStat for events."""
    def __init__(self):
        self.event_stats = collections.defaultdict(
            lambda: collections.defaultdict(SmallGainStat))
        
    def merge_stats(self, event_lists, key, gain_stat):
        for event_type_name, event_list in event_lists.iteritems():
            event_stats_collection = self.event_stats[event_type_name]
            for event in event_list:
                full_key = key + ';' + event
                per_card_stat = event_stats_collection[full_key]
                per_card_stat.merge(gain_stat)

    def update_db(self, mongo_db_inst):
        for event_type_name, stats_dict in self.event_stats.iteritems():
            mongo_collection = mongo_db_inst[event_type_name]
            for full_key, gain_stats_obj in sorted(stats_dict.iteritems()):
                existing_raw_obj = mongo_collection.find_one(
                    {'_id': full_key})
                if existing_raw_obj:
                    existing_stat = SmallGainStat()
                    existing_stat.from_primitive_object(
                        existing_raw_obj['vals'])
                    gain_stats_obj.merge(existing_stat)
                key_wrap_obj = {'vals': gain_stats_obj.to_primitive_object()}
                utils.write_object_to_db(key_wrap_obj, mongo_collection,
                                         full_key)

def accumulate_card_stats(games_stream, stats_accumulator, max_games=-1):
    ct = 0
    for game in games_stream:
        detected_events = detect_events(game)

        per_player_accum = game.cards_accumalated_per_player().iteritems()
        for player, accum_dict in per_player_accum:
            avail = analysis_util.available_cards(game, accum_dict.keys())
            win_points = game.get_player_deck(player).WinPoints()
            for card in avail:
                count = accum_dict.get(card, 0)
                small_gain_stat = SmallGainStat()
                if count:
                    small_gain_stat.win_given_any_gain.add_outcome(win_points)
                else:
                    small_gain_stat.win_given_no_gain.add_outcome(win_points)
                small_gain_stat.win_weighted_gain.add_many_outcomes(
                    win_points, count)
                card_index = str(card.index)
                stats_accumulator.merge_stats(detected_events, card_index,
                                              small_gain_stat)
        max_games -= 1
        if max_games == 0:
            break

def main():
    args = utils.incremental_max_parser().parse_args()

    c = pymongo.Connection()
    db = c.test
    scanner = incremental_scanner.IncrementalScanner('analyze2', db)

    if not args.incremental:
        scanner.reset()
        for collection_name, _ in event_detectors:
            db[collection_name].drop()

    print scanner.status_msg()
    games_stream = analysis_util.games_stream(scanner, c.test.games)
    accumulator = EventAccumulator()
    accumulate_card_stats(games_stream, accumulator, args.max_games)

    print 'saving to database'
    accumulator.update_db(db)
    scanner.save()
    print scanner.status_msg()
        

if __name__ == '__main__':
    main()
            
