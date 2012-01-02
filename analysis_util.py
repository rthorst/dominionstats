#!/usr/bin/python

import game
import utils

def games_stream(scanner, games_col):
    for raw_game in utils.progress_meter(
        scanner.scan(games_col, {}), 1000):
        yield game.Game(raw_game)

def available_cards(game_obj, gained_list):
    ret = set()
    ret.update(game_obj.get_supply())
    ret.update(gained_list)
    if 'Tournament' in ret:
        ret.update(card_info.TOURNAMENT_WINNINGS)
    return ret
    
