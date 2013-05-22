#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Parse raw goko game into JSON list of game documents."""

import bz2
import codecs
import collections
import datetime
import itertools
import logging
import logging.handlers
import multiprocessing
import os
import os.path
import pprint
import pymongo
import re
import sys

from dominioncards import get_card, CardEncoder, indexes, index_to_card
from game import Game
from keys import *
from utils import segments
import dominioncards
import game
import name_merger
import simplejson as json
import utils
import parse_common

RATING_SYSTEM_RE = re.compile('^Rating system: (.*)$')
GAME_OVER_RE = re.compile('^------------ Game Over ------------$')
EMPTY_LINE_RE = re.compile('^\s+$')
ENDGAME_VP_CHIP_RE = re.compile('^.* - victory point chips: (\d+)$')
ENDGAME_POINTS_RE = re.compile('^.* - total victory points: (\d+)$')
START_TURN_RE = re.compile('^---------- (.*): turn (.*?) (\[possessed\] )?----------$')
VP_CHIPS_RE = re.compile('receives (\d+) victory point chips')
HYPHEN_SPLIT_RE = re.compile('^(.*?) - (.*)$')
COMMA_SPLIT_RE = re.compile(', ')
NUMBER_CARD_RE = re.compile('\s*(\d+) (.*)')
BANE_RE = re.compile('^Bane card: (.*)$')
PLAYER_AND_START_DECK_RE = re.compile('^(.*) - starting cards: (.*)$')
TAKES_COINS_RE = re.compile('takes (\d+) coin')

KW_APPLIED = 'applied ' #applied Watchtower to place X on top of the deck
KW_TO_THE_SUPPLY = ' to the Supply'
KW_PLACE = 'place: '
KW_CARDS = 'cards: '
KW_PLAYS = 'plays '
KW_LOOKS_AT = 'looks at '
KW_GAINS = 'gains '
KW_RECEIVES = 'receives '
KW_RESIGNED = 'resigned'
KW_QUIT = 'quit'
KW_REVEALS_C = 'reveals: ' 
KW_REVEALS = 'reveals ' 
KW_DISCARDS = 'discards '
KW_DISCARDS_C = 'discards: '
KW_PLACES = 'places '
KW_BUYS = 'buys '
KW_GAINS = 'gains ' 
KW_DRAWS = 'draws ' 
KW_TRASHES = 'trashes ' 
KW_SHUFFLES = 'shuffles deck'
KW_PLACES = 'places ' 
KW_DURATION = 'duration '
KW_SETS_ASIDE = 'sets aside ' 
KW_TAKES_SET_ASIDE = 'takes set aside cards: '
KW_CHOOSES = 'chooses '
KW_EMBARGOES = 'embargoes '
KW_NAMES = 'names '
KW_CHOOSES_TWO_COINS = 'chooses two coins'
KW_RETURNS = 'returns ' 
KW_PIRATE_COIN = 'receives a pirate coin, now has '
KW_VP_CHIPS = 'victory point chips'
KW_TAKES = 'takes ' 

KEYWORDS = [locals()[w] for w in dict(locals()) if w.startswith('KW_')]

def parse_player_start_decks(log_lines):
    start_decks = []
    start_match = PLAYER_AND_START_DECK_RE.match(log_lines[0])
    while start_match:
        line=log_lines.pop(0)
        name = start_match.group(1)
        start_deck = indexes(capture_cards(start_match.group(2)))
        start_decks.append({NAME:name, START_DECK:start_deck})

        start_match = PLAYER_AND_START_DECK_RE.match(log_lines[0])
    return start_decks

def parse_supply(log_lines):
    line = log_lines.pop(0)
    supply_cards_text = line.split(', ')
    supply_cards_text[0] = supply_cards_text[0].replace('Supply cards: ','')
    supply_cards = []
    for card_name in supply_cards_text:
        try:
            card = get_card(card_name)
        except KeyError, exception:
            raise parse_common.ParsingError('%s is not a card in the supply!'
                                            % card_name)
        supply_cards.append(card.index)

    bane_match = BANE_RE.match(log_lines[0])
    if bane_match:
        try:
            bane_card = get_card(bane_match.groups()[0])
            log_lines.pop(0)
        except KeyError, exception:
            raise parse_common.ParsingError('%s is not a valid bane!'
                                            % card_name)
    return supply_cards

def parse_header(log_lines):
    """Parse the goko header. 
    
    It begins with the 'Game Setup' line and ends with the blank line before
    the first player's first turn.
    """

    # first line - header line
    line = log_lines.pop(0)
    assert('Game Setup' in line)
    
    # next - supply
    supply_cards = parse_supply(log_lines)

    # optionally, may say the game type. Old logs won't have this.
    rating_system_match = RATING_SYSTEM_RE.match(log_lines[0])
    if rating_system_match:
        rating_system = rating_system_match.group(1)
        line = log_lines.pop(0)
    else:
        rating_system = 'unknown'

    # Next N lines will give me the N players and their start decks
    start_decks = parse_player_start_decks(log_lines) 
    names_list = [d[NAME] for d in start_decks]

    # next 2N lines are the players shuffling their decks
    # and drawing their starting hands. Then one blank line. 
    log_lines[0:(len(names_list)*2+1)] = []

    return {START_DECKS:start_decks, PLAYERS:names_list, SUPPLY:supply_cards,
            RATING_SYSTEM:rating_system}

def validate_names(game_dict, dubious_check):
    """ Raise an exception for names that might screw up the parsing.
    This should happen in less than 1% of real games, but it's just easier
    to punt on annoying inputs that to make sure we get them right.
    """
    names = game_dict[PLAYERS]
    used_names = set()
    for name in names:
        if name in used_names:
            # unrecoverable!
            raise parse_common.BogusGameError('Duplicate name %s' % name)
        used_names.add(name)

    if len(names) <= 1 and dubious_check:
        # that's recoverable, so only raise error if checking dubious
        raise parse_common.BogusGameError('only one player')


def capture_cards(line, return_dict=False):
    """ Given a section of text from goko, extract the cards.

    line: string like 'plays 1 Silver, 3 Copper'
    returns: list of the card objects, eg, [Silver, Copper, Copper, Copper]
    """
    for kw in KEYWORDS:
        line=line.replace(kw, '')

    if return_dict:
        cards = {}
    else:
        cards = []
    card_sections = COMMA_SPLIT_RE.split(line)
    for sect in card_sections:
        multiple = NUMBER_CARD_RE.match(sect)
        if multiple:
            mult = int(multiple.group(1))
            sect = multiple.group(2)
        else:
            mult = 1

        try: 
            card = get_card(sect)
        except KeyError, exception:
            raise parse_common.ParsingError('Failed to find card in line: %s'
                                             % line)
        if return_dict:
            cards[str(card.index)]=mult
        else:
            cards.extend([card] * mult)
    return cards

def parse_turn(log_lines, trash_pile):
    """ Parse the information from a given turn.

    Maintain the trash pile. This is necessary for Forager money counting.

    Return a dict containing the following fields.  If any of the fields have
    a value that evaluates to False, do not keep it.

    name: player name.
    number: 1 indexed turn number.
    plays: List of cards played.
    buys: List of cards bought.
    gains: List of cards gained.
    trashes: List of cards trashed.
    returns: List of cards returned.
    ps_tokens: Number of pirate ship tokens gained.
    vp_tokens: Number of victory point tokens gained.
    money: Amount of money available during entire buy phase.
    opp: Dict keyed by opponent index in names_list, containing dicts with trashes/gains.
    """

    def _delete_if_exists(d, n):
        if n in d:
            del d[n]

    def fix_buys_and_gains(buys, gains):
        """Goko reports each buy and gain separately. This is correct, but
        having everything compatible with iso stats would be nice! So, here
        I 'fix' buys and gains so things which are bought and gained are 
        only reported once, in 'buys', and things which are bought but not
        gained (such as due to trader or possession) are not listed.
        """
        new_buys = []
        for buy in buys:
            if buy in gains:
                gains.remove(buy)
                new_buys.append(buy)
        return (new_buys, gains)

    ret = {PLAYS: [], RETURNS: [], GAINS: [], TRASHES: [], BUYS: []}
    durations = []
    turn_money = 0
    vp_tokens = 0
    ps_tokens = 0

    # Lots of stuff happens that goko doesn't report explicitly.
    wait_for_Forager_trashing = 0 # Forager trashing cards needs to give $
    
    # Spoils gets returned when played! Except when played twice via counterfeit
    counterfeiting_spoils = False 

    # Keeps track of the trash, for forager value
    thieving_from_trash = False 
    thieved_cards = []

    # Trashing a mining village CAN give $2. If I see a "trashed MV" line, does
    # it give me money? Yes, if the last thing played was an MV!
    trashing_mv_would_give_2 = False 

    opp_turn_info = collections.defaultdict(lambda: {GAINS: [], BUYS: [],
                                                     TRASHES: []})
    while True:
        line = log_lines.pop(0)
        print(line)
        turn_start = START_TURN_RE.match(line)

        # detect line which starts the turn, parse out turn number and player name
        if turn_start:
            ret[NAME] = turn_start.group(1)
            ret[NUMBER] = int(turn_start.group(2))
            if turn_start.group(3):
                ret[POSSESSION] = True
            else:
                ret[POSSESSION] = False
            continue

        # empty line ends the turn, clean up and return
        if EMPTY_LINE_RE.match(line):
            # Current goko log bug - does not report 1 VP from Bishop
            vp_tokens += ret[PLAYS].count(dominioncards.Bishop)

            if wait_for_Forager_trashing >= 1:
                turn_money += sum([d.is_treasure() for d in set(trash_pile)])
                wait_for_Forager_trashing = 0

            money = parse_common.count_money(ret[PLAYS], True) + \
                    turn_money + parse_common.count_money(durations, True)

            (buys, gains) = fix_buys_and_gains(ret[BUYS], ret[GAINS])

            ret[BUYS] = indexes(buys)
            ret[PLAYS] = indexes(ret[PLAYS])
            ret[RETURNS] = indexes(ret[RETURNS])
            ret[GAINS] = indexes(gains)
            ret[TRASHES] = indexes(ret[TRASHES])
            durations = indexes(durations)
            for opp in opp_turn_info.keys():
                _delete_if_exists(opp_turn_info[opp], 'buy_or_gain')
                parse_common.delete_keys_with_empty_vals(opp_turn_info[opp])

                d = opp_turn_info[opp]
                for k, v in d.iteritems():
                    if k==VP_TOKENS:
                        d[k] = v
                    else:
                        d[k] = indexes(v)

            ret.update({MONEY:money, VP_TOKENS: vp_tokens, 
                        PIRATE_TOKENS: ps_tokens, OPP: dict(opp_turn_info)})
            return ret

        # Have to count money from forager trashing two lines *after* 
        # Forager is played, since the trash happens after the play. 
        if wait_for_Forager_trashing == 2:
            wait_for_Forager_trashing = 1
        elif wait_for_Forager_trashing == 1:
            turn_money += sum([d.is_treasure() for d in set(trash_pile)])
            wait_for_Forager_trashing = 0


        player_and_rest = HYPHEN_SPLIT_RE.match(line)
        active_player = player_and_rest.group(1)
        action_taken = player_and_rest.group(2)

        if KW_PLAYS in action_taken:
            thieving_from_trash = False
            trashing_mv_would_give_2 = False 
            played = capture_cards(action_taken)
            ret[PLAYS].extend(played)

            # special cases - actions that don't get reported in the log 
            for play in played: 
                if play == dominioncards.Forager:
                    # Have to special-case forager money, it depends on the
                    # trash pile AFTER the next trashing event! Have to wait
                    # for it.  And clean up this variable if there was nothing
                    # in hand to trash and so the forager-trash never happens.
                    # This counter counts down how many lines to wait for the
                    # potential trashing event. 
                    if wait_for_Forager_trashing >= 1:
                        turn_money += sum([d.is_treasure()\
                                           for d in set(trash_pile)])
                    wait_for_Forager_trashing = 2
                    counterfeiting_spoils = False
                elif play == dominioncards.Counterfeit:
                    counterfeiting_spoils = True
                elif play == dominioncards.Spoils:
                    # Spoils always get returned on play...
                    # ...unless it's Counterfeited. 
                    if not counterfeiting_spoils:
                        ret[RETURNS].append(play)
                    else:
                        counterfeiting_spoils = False
                elif play == dominioncards.NobleBrigand or \
                        play == dominioncards.Thief or\
                        play == dominioncards.Rogue:
                    thieving_from_trash = True
                    counterfeiting_spoils = False
                    thieved_cards = []
                elif play == dominioncards.MiningVillage:
                    trashing_mv_would_give_2 = True
                    counterfeiting_spoils = False
            continue

        # Everything other than 'plays a spoils' means the next line 
        # after a Counterfeit isn't playing a spoils
        counterfeiting_spoils = False

        if KW_BUYS in action_taken:
            buys = capture_cards(action_taken)
            ret[BUYS].extend(buys)
            thieving_from_trash = False
            trashing_mv_would_give_2 = False 

            if dominioncards.NobleBrigand in buys:
                 thieving_from_trash = True
                 thieved_cards = []
            continue

        if KW_RETURNS in action_taken:
            ret[RETURNS].extend(capture_cards(action_taken))
            thieving_from_trash = False
            trashing_mv_would_give_2 = False 
            continue

        if KW_GAINS in action_taken:
            trashing_mv_would_give_2 = False 
            gained = capture_cards(action_taken)
            if active_player == ret[NAME]:
                ret[GAINS].extend(gained)
                if(thieving_from_trash):
                    for c in gained:
                        if c in thieved_cards:
                            trash_pile.remove(c)
                            thieved_cards.remove(c)
            else:
                opp_turn_info[active_player][GAINS].extend(gained)
            continue

        # Some old Goko logs mis-attribute pirate ship trashing. I'm not 
        # going to special-case all the various goko bugs that have since been
        # fixed, though. 
        if KW_TRASHES in action_taken:
            trashed = capture_cards(action_taken)
            while dominioncards.Fortress in trashed:
                trashed.remove(dominioncards.Fortress)

            if active_player == ret[NAME]:
                if dominioncards.MiningVillage in trashed and\
                   trashing_mv_would_give_2:
                    turn_money += 2

                if not ret[POSSESSION]:
                    ret[TRASHES].extend(trashed)
                    trash_pile.extend(trashed)
            else:
                opp_turn_info[active_player][TRASHES].extend(trashed)
                trash_pile.extend(trashed)
                if thieving_from_trash:
                    thieved_cards.extend(trashed)

            trashing_mv_would_give_2 = False
            continue

        if KW_DURATION in action_taken:
            durations.extend(capture_cards(action_taken))
            thieving_from_trash = False
            trashing_mv_would_give_2 = False
            continue

        if KW_CHOOSES_TWO_COINS in action_taken:
            turn_money += 2
            thieving_from_trash = False
            trashing_mv_would_give_2 = False
            continue

        if KW_PIRATE_COIN in action_taken:
            ps_tokens += 1
            thieving_from_trash = False
            trashing_mv_would_give_2 = False
            continue

        if KW_VP_CHIPS in action_taken:
            vp_chips_match = VP_CHIPS_RE.match(action_taken)
            vp_tokens += int(vp_chips_match.group(1))
            thieving_from_trash = False
            trashing_mv_would_give_2 = False
            continue

        match = TAKES_COINS_RE.match(action_taken)
        if match:
            turn_money += int(match.group(1))
            thieving_from_trash = False
            trashing_mv_would_give_2 = False
            continue

        # All remaining actions should be captured; the next few statements
        # are those which are not logged in any way (though they could be!)

        # They are separated by what keeping-track things they would interrupt:
        # Mining village trashing, Thief/Noble Brigand.

        if (KW_LOOKS_AT in action_taken or 
            KW_RECEIVES in action_taken or 
            KW_PLACES in action_taken or 
            KW_SETS_ASIDE in action_taken or 
            KW_TAKES in action_taken or
            KW_EMBARGOES in action_taken or 
            KW_NAMES in action_taken or 
            KW_TAKES_SET_ASIDE in action_taken):
            thieving_from_trash = False
            trashing_mv_would_give_2 = False
            continue

        if (KW_DRAWS in action_taken):
            thieving_from_trash = False
            continue

        if (KW_REVEALS in action_taken or 
            KW_REVEALS_C in action_taken or 
            KW_APPLIED in action_taken or 
            KW_DISCARDS in action_taken or 
            KW_DISCARDS_C in action_taken or 
            KW_CHOOSES in action_taken):
            trashing_mv_would_give_2 = False
            continue

            
        if (KW_SHUFFLES in action_taken):
            continue


        raise parse_common.BogusGameError('Line did not match any keywords!')


def parse_turns(log_lines):
    """
    Sequentially go through the log and parse the game, splitting it into turns.

    Also handle outpost and possession turns here.
    They require cross-turn information from the end of the *previous* turn.

    In the case of Outpost played during Possession turn, this will mark the 
    WRONG turn as being an outpost turn, but will still mark one of them. 
    """
    turns = [];
    trash_pile = [];
    
    previous_name = '' # for Possession
    while not GAME_OVER_RE.match(log_lines[0]):
        turn = parse_turn(log_lines, trash_pile)
        if turn[POSSESSION]:
            turn['pname'] = previous_name
        elif(len(turns) > 0 and turn[NAME] == turns[-1][NAME] and 
           not turn[POSSESSION] and not turns[-1][POSSESSION]):
            turn[OUTPOST] = True
            previous_name = turn[NAME]
        else:
            turn['turn_no'] = True
            previous_name = turn[NAME]
        turns.append(turn)

    log_lines.pop(0)
    return turns



def associate_turns_with_owner(game_dict, turns, dubious_check):
    """ Move each turn in turns to be a member of the corresponding player
    in game_dict.

    Remove the names from the turn, since it is redundant with the name
    on the player level dict."""
    name_to_owner = {}
    for idx, deck in enumerate(game_dict[DECKS]):
        name_to_owner[deck[NAME]] = deck
        deck[TURNS] = []

    order_ct = 0

    for idx, turn in enumerate(turns):
        owner = name_to_owner[turn[NAME]]
        owner[TURNS].append(turn)
        if not ORDER in owner:
            owner[ORDER] = idx + 1
            order_ct += 1
        del turn[NAME]

    if order_ct != len(game_dict[DECKS]) and dubious_check:
        # This may be okay! Only raise if dubious_check
        raise parse_common.BogusGameError('Did not find turns for all players')

def parse_endgame(log_lines):
    """
    Parses the endgame section of a goko log.
    Everything after the Game Over line. Puts results directly in the game dict.

    Cannot calculate game_end; the trash is not restated in the endgame section,
    so there isn't necessarily a way to know why the game ended without going 
    through the whole game. 
    """

    decks = []
    while not KW_PLACE in log_lines[0]:
        resigned = False
        line = log_lines.pop(0)
        hyphen_split_match = HYPHEN_SPLIT_RE.match(line)
        name = hyphen_split_match.group(1)

        if KW_RESIGNED in hyphen_split_match.group(2) or KW_QUIT in hyphen_split_match.group(2):
            resigned = True
            line = log_lines.pop(0)
            hyphen_split_match = HYPHEN_SPLIT_RE.match(line)
            name = hyphen_split_match.group(1)

        deck_comp = capture_cards(hyphen_split_match.group(2), True)

        line = log_lines.pop(0)
        vp_chip_match = ENDGAME_VP_CHIP_RE.match(line)
        if vp_chip_match:
            vp_tokens = int(vp_chip_match.group(1))
            line=log_lines.pop(0)
        else:
            vp_tokens = 0

        points_match = ENDGAME_POINTS_RE.match(line)
        total_vp = int(points_match.group(1))
        
        # line which says how many turns there were
        log_lines.pop(0)
        # blank line
        log_lines.pop(0)

        # Handle resignations here; give fake -1 point
        if resigned:
            total_vp = -1

        decks.append({NAME: name, POINTS: total_vp, RESIGNED: resigned,
                      DECK: deck_comp, VP_TOKENS: vp_tokens})
    return decks


def parse_game(game_str, dubious_check = False):
    """ Parse game_str into game dictionary.

    game_str: Entire contents of a log file from goko.
    dubious_check: If true, raise a BogusGame exception if the game is
      suspicious.

    returns a dict with the following fields:
      decks: A list of player decks, as documented in parse_endgame.
      start_decks: A list of player starting decks. Usually 7c3e. 
      supply: A list of cards in the supply.
      players: A list of normalized player names.
      game_end: List of cards exhausted that caused the game to end.
      resigned: True iff some player in the game resigned..
    """

    # Goko logs are not split into sections by an obvious separator
    # So analyze sequentially, by lines
    log_lines = game_str.split('\n')

    game_dict = parse_header(log_lines)
    # start_decks, players, and supply are now set

    validate_names(game_dict, dubious_check)
    game_dict[VETO] = {}

    turns = parse_turns(log_lines)
    decks = parse_endgame(log_lines)
    game_dict[DECKS] = decks
    associate_turns_with_owner(game_dict, turns, dubious_check)
    return game_dict
