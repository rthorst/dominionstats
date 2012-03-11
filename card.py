import csv
import os

_cardlist_reader = csv.DictReader(open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'card_info/card_list.csv')))
_CARDS = {}

# Returns value of string if the value is unambiguous, otherwise the default
def int_or_no_int(string, default):
    try:
        return int(string)
    except ValueError, e:
        return default

class Card: 
    def __init__(self, cardlist_row):
        for key, value in cardlist_row.iteritems():
            prop = str.lower(key)
            setattr(self, prop, value)

    def pluralize(self, freq):
        return self.singular if freq == 1 else self.plural

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

_init()

def get_card(name):
    return _CARDS[name]

TOURNAMENT_WINNINGS = ['Princess', 'Diadem', 'Followers', 
                       'Trusty Steed', 'Bag of Gold']

EVERY_SET_CARDS = ['Estate', 'Duchy', 'Province',
                   'Copper', 'Silver', 'Gold', 'Curse']

#OPENING_CARDS = [card for card in _card_info_rows
#                 if cost(card) in ('0', '2', '3', '4', '5')]
#OPENING_CARDS.sort()

def sane_title(card):
    return card.title().replace("'S", "'s").replace(' Of ', ' of ').strip()

def card_index(singular):
    return _card_index[singular]

def card_names():
    return _card_names

def card_var_names():
    return _card_var_names


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
