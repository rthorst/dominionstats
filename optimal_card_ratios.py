#!/usr/bin/python
# -*- coding: utf-8 -*-

import utils
import pymongo
import incremental_scanner

class DBCardRatioTracker:
    def __init__(self, collection, incremental=True):
        self.collection = collection
        self.incremental = incremental
        self.data = {}
        if self.incremental:
            for entry in collection.find():
                self.data[entry['_id']] = entry

    def integrateResults(self, win_points, ratio_dict):
        for key in ratio_dict:
            if not self.data.has_key(key):
                self.data[key] = {'_id':key, 'stats':{}}
            stats = self.data[key]['stats']
            for ratio in ratio_dict[key]:
                ratio = str(ratio[0]) + ':' + str(ratio[1])
                if not stats.has_key(ratio):
                    stats[ratio] = [0, 0]
                stats[ratio][0] += win_points
                stats[ratio][1] += 1

    def save(self):
        if not self.incremental:
            self.collection.drop()
        for key in self.data.iterkeys():
            self.collection.update({'_id': key}, self.data[key], True)

class CardRatioTracker:
    def __init__(self, supply):
        self.card_counts = {}
        for card in [u'Estate', u'Duchy', u'Province', u'Curse', u'Copper', u'Silver', u'Gold'] + supply:
            self.card_counts[card] = 0
        self.card_counts[u'Estate'] = 3
        self.card_counts[u'Copper'] = 7

        self.ratios = {}
        for card1 in self.card_counts.iterkeys():
            for card2 in self.card_counts.iterkeys():
                if card1 != card2:
                    if card1 < card2:
                        c1, c2 = card1, card2
                    else:
                        c1, c2 = card2, card1
                    self.ratios[c1 + ':' + c2] = set([(self.card_counts[c1], self.card_counts[c2])])

    def adjustCardCount(self, card, adjustment):
        if not self.card_counts.has_key(card):
            return

        self.card_counts[card] += adjustment

        for card2 in self.card_counts.iterkeys():
            if card != card2:
                if card < card2:
                    c1, c2 = card, card2
                else:
                    c1, c2 = card2, card
                self.ratios[c1 + ':' + c2].add((self.card_counts[c1], self.card_counts[c2]))

    def getRatioDict(self):
        return self.ratios

def process_game(game):
    num_players = len(game['decks'])
    player_name_to_order = dict((deck['name'], deck['order'] - 1) for deck in game['decks'])
    order_to_turns = dict((deck['order'] - 1, deck['turns']) for deck in game['decks'])
    order_to_tracker = dict((x, CardRatioTracker(game['supply'])) for x in xrange(num_players))
    order_to_win_points = dict((deck['order'] - 1, deck['win_points']) for deck in game['decks'])
    current_player = 0
    next_turn_indexes = [0] * num_players

    while next_turn_indexes[current_player] < len(order_to_turns[current_player]):
        turn = order_to_turns[current_player][next_turn_indexes[current_player]]

        # turn order for Outpost and Possession can be tricky, so skip games with these for now
        if turn.has_key('plays'):
            for card in turn['plays']:
                if card == 'Outpost' or card == 'Possession':
                    return None

        if turn.has_key('buys'):
            for card in turn['buys']:
                order_to_tracker[current_player].adjustCardCount(card, 1)
        if turn.has_key('gains'):
            for card in turn['gains']:
                order_to_tracker[current_player].adjustCardCount(card, 1)
        if turn.has_key('trashes'):
            for card in turn['trashes']:
                order_to_tracker[current_player].adjustCardCount(card, -1)
        if turn.has_key('opp'):
            for opp_player_name in turn['opp'].iterkeys():
                opp_turn = turn['opp'][opp_player_name]
                opp_current_player = player_name_to_order[opp_player_name]
                if opp_turn.has_key('gains'):
                    for card in opp_turn['gains']:
                        order_to_tracker[opp_current_player].adjustCardCount(card, 1)
                if opp_turn.has_key('trashes'):
                    for card in opp_turn['trashes']:
                        order_to_tracker[opp_current_player].adjustCardCount(card, -1)

        next_turn_indexes[current_player] += 1
        current_player = (current_player + 1) % num_players

    return ((order_to_win_points[x], order_to_tracker[x].getRatioDict()) for x in xrange(num_players))

def main():
    parser = utils.incremental_max_parser()
    args = parser.parse_args()

    conn = pymongo.Connection()
    database = conn.test
    games = database.games
    collection = database.optimal_card_ratios

    scanner = incremental_scanner.IncrementalScanner('optimal_card_ratios', database)

    if not args.incremental:
        scanner.reset()

    db_tracker = DBCardRatioTracker(collection, args.incremental)

    print scanner.status_msg()

    total_checked = 0
    for game in utils.progress_meter(scanner.scan(games, {})):
        total_checked += 1

        result = process_game(game)
        if result != None:
            for win_points, ratio_dict in result:
                db_tracker.integrateResults(win_points, ratio_dict)

        if args.max_games >= 0 and total_checked >= args.max_games:
            break

    print scanner.status_msg()

    db_tracker.save()
    scanner.save()

if __name__ == '__main__':
    main()

