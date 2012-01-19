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

    def integrateResults(self, tracker_type, win_points, final_ratio_dict):
        for key in final_ratio_dict:
            if key not in self.data:
                self.data[key] = {'_id':key}
            if tracker_type not in self.data[key]:
                self.data[key][tracker_type] = {}
            stats = self.data[key][tracker_type]
            for ratio in final_ratio_dict[key]:
                ratio = str(ratio[0]) + ':' + str(ratio[1])
                if ratio not in stats:
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

    def getCardRatios(self):
        ratios = {}
        for card1 in self.card_counts.iterkeys():
            for card2 in self.card_counts.iterkeys():
                if card1 != card2:
                    if card1 < card2:
                        c1, c2 = card1, card2
                    else:
                        c1, c2 = card2, card1
                    ratios[c1 + ':' + c2] = set([(self.card_counts[c1], self.card_counts[c2])])
        return ratios

class FinalCardRatioTracker(CardRatioTracker):
    def __init__(self, supply):
        CardRatioTracker.__init__(self, supply)

    def adjustCardCount(self, card, adjustment):
        if card not in self.card_counts:
            return

        self.card_counts[card] += adjustment

    def getRatioDict(self):
        return CardRatioTracker.getCardRatios(self)

class ProgressiveCardRatioTracker(CardRatioTracker):
    def __init__(self, supply):
        CardRatioTracker.__init__(self, supply)
        self.card_counts[u'Estate'] = 3
        self.card_counts[u'Copper'] = 7
        self.ratios = self.getCardRatios()

    def adjustCardCount(self, card, adjustment):
        if card not in self.card_counts:
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
    win_points = dict((deck['order'] - 1, deck['win_points']) for deck in game['decks'])

    decks = dict((deck['order'] - 1, deck['deck']) for deck in game['decks'])
    final_trackers = dict((x, FinalCardRatioTracker(game['supply'])) for x in xrange(num_players))
    for current_player in xrange(num_players):
        for card, count in decks[current_player].iteritems():
            final_trackers[current_player].adjustCardCount(card, count)

    tricky_turns = False
    for deck in game['decks']:
        for turn in deck['turns']:
            if 'plays' in turn:
                for card in turn['plays']:
                    if card == 'Outpost' or card == 'Possession':
                        tricky_turns = True

    if not tricky_turns:
        turns = dict((deck['order'] - 1, deck['turns']) for deck in game['decks'])
        progressive_trackers = dict((x, ProgressiveCardRatioTracker(game['supply'])) for x in xrange(num_players))
        current_player = 0
        next_turn_indexes = [0] * num_players
        while next_turn_indexes[current_player] < len(turns[current_player]):
            turn = turns[current_player][next_turn_indexes[current_player]]
            if 'buys' in turn:
                for card in turn['buys']:
                    progressive_trackers[current_player].adjustCardCount(card, 1)
            if 'gains' in turn:
                for card in turn['gains']:
                    progressive_trackers[current_player].adjustCardCount(card, 1)
            if 'trashes' in turn:
                for card in turn['trashes']:
                    progressive_trackers[current_player].adjustCardCount(card, -1)
            if 'opp' in turn:
                for opp_player_name in turn['opp'].iterkeys():
                    opp_turn = turn['opp'][opp_player_name]
                    opp_current_player = player_name_to_order[opp_player_name]
                    if 'gains' in opp_turn:
                        for card in opp_turn['gains']:
                            progressive_trackers[opp_current_player].adjustCardCount(card, 1)
                    if 'trashes' in opp_turn:
                        for card in opp_turn['trashes']:
                            progressive_trackers[opp_current_player].adjustCardCount(card, -1)
            next_turn_indexes[current_player] += 1
            current_player = (current_player + 1) % num_players

    retval = []
    for x in xrange(num_players):
        row = []
        row.append(win_points[x])
        row.append(final_trackers[x].getRatioDict())
        if tricky_turns:
            row.append(None)
        else:
            row.append(progressive_trackers[x].getRatioDict())
        retval.append(row)
    return retval

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
        for win_points, final_ratio_dict, progressive_ratio_dict in result:
            if final_ratio_dict:
                db_tracker.integrateResults('final', win_points, final_ratio_dict)
            if progressive_ratio_dict:
                db_tracker.integrateResults('progressive', win_points, progressive_ratio_dict)

        if args.max_games >= 0 and total_checked >= args.max_games:
            break

    print scanner.status_msg()

    db_tracker.save()
    scanner.save()

if __name__ == '__main__':
    main()

