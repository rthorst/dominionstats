#!/usr/bin/python

import pymongo
import sys
import pprint
import argparse
import utils
import copy

parser = utils.incremental_date_range_cmd_line_parser()

KEYS = ['decks', 'deck', 'name', 'order', 'points', 'resigned', 'turns', 'buys', 'gains', 'trashes', 'money', 'plays', 'game_end', 'players', 'supply', 'vp_tokens', 'win_points', 'opp']

def replace(mmap, key, array):
    mmap[key] = [array.index(card) for card in mmap[key]]

def replace_keys(mmap, key, array):
    nmap = {}
    for (mkey, value) in mmap[key].iteritems():
        nmap[ array.index(mkey) ] = value
    mmap[key] = nmap

def remap(mmap, array):
    keys = mmap.keys()
    for key in keys:
        if key not in array:
            continue
        mmap[ array.index(key) ] = mmap[key]
        del mmap[key]

def compress(game):
    cards = game['supply'] + ['Copper', 'Silver', 'Gold', 'Estate', 'Duchy', 'Province']
    for deck in game['decks']:
        replace_keys(deck, 'deck', cards)
        for turn in deck['turns']:
            replace(turn, 'buys', cards)
            replace(turn, 'plays', cards)
            if 'opp' in turn:
                for name, smap in turn['opp'].iteritems():
                    for n in smap:
                        replace(smap, n, cards)
                    remap(smap, KEYS)
            remap(turn, KEYS)
        remap(deck, KEYS)

    replace(game, 'game_end', cards)
    remap(game, KEYS)
    
    pprint.pprint(game)
    return game

def decompress(game):
    return game

def main():
    args = parser.parse_args()
    games_table = pymongo.Connection().test.games
    original = games_table.find_one({'_id': 'game-20120211-222425-fe513e0f.html'})
    compressed = compress(copy.deepcopy(original))
    decompressed = decompress(copy.deepcopy(compressed))
    print len(str(original))
    print len(str(compressed))
    print len(str(decompressed))
    print original==decompressed


if __name__ == '__main__':
    main()
