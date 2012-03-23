import csv
import os

_cardlist_reader = csv.DictReader(open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'card_info/card_list.csv')))
_CARDS = {}
_INDEXED = {}

# Returns value of string if the value is unambiguous, otherwise the default
def int_or_no_int(string, default):
    try:
        return int(string)
    except ValueError, e:
        return default

def PythonifyName(name):
    return ''.join([n for n in name if n not in [' ', "'", '-']])

class Card: 
    def __init__(self, cardlist_row):
        for key, value in cardlist_row.iteritems():
            prop = str.lower(key)
            setattr(self, prop, value)

    def pluralize(self, freq):
        return self.singular if freq == 1 else self.plural

    def sane_title(self):
        return self.singular.replace("'S", "'s").replace(' Of ', ' of ').strip()

    def is_treasure(self):
        return self.treasure == '1'

    def is_reaction(self):
        return self.reaction == '1'

    def is_victory(self):
        return self.victory == '1'

    def is_action(self):
        return self.action == '1'

    def is_attack(self):
        return self.attack == '1'

    def vp_per_card(self):
        return int_or_no_int(self.vp, 0)

    def money_value(self):
        return int_or_no_int(self.coins, 0)

    def trashes(self):
        return int_or_no_int(self.trash, 1)

    def num_plus_actions(self):
        return int_or_no_int(self.actions, 1)

    def get_expansion(self):
        return self.expansion

    def __repr__(self):
        return self.singular

    def __eq__(self, other):
        return self.singular==other

    def __hash__(self):
        return self.singular.__hash__()

    def num_copies_per_game(self, num_players):
        if self.is_victory():
            if num_players >= 3:
                return 12
            return 8
        card_name = str(card)
        if card_name == 'Curse':
            return 10 * (num_players - 1)
        return {'Potion': 16,
                'Platinum': 12,
                'Gold': 30,
                'Silver': 40,
                'Copper': 60
                }.get(card_name, 10)

def _init():
    for cardlist_row in _cardlist_reader:
        singular = cardlist_row['Singular']
        plural = cardlist_row['Plural']
        c = Card(cardlist_row)
        _CARDS[singular] = c
        _CARDS[plural] = c
        _INDEXED[ int(c.index) ] = c

_init()

def all_cards():
    return _INDEXED.values()

for c in all_cards():
    pname = PythonifyName(c.singular)
    vars()[ pname ] = c

def get_card(name):
    return _CARDS[name]

def index_to_card(index):
    return _INDEXED[index]

TOURNAMENT_WINNINGS = [Princess, Diadem, Followers, TrustySteed, BagofGold]

EVERY_SET_CARDS = [Estate, Duchy, Province, Copper, Silver, Gold, Curse]


def opening_cards():
    return [card for card in all_cards()
            if card.cost in ('0', '2', '3', '4', '5')].sort()

def indexes(cards):
    return [int(card.index) for card in cards]

import simplejson as json
class CardEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Card):
            return int(obj.index)
        return obj

    def encode(self, obj):
        if isinstance(obj, Card):
            return json.JSONEncoder.encode(self, str(obj.index))
        return json.JSONEncoder.encode(self, obj)
