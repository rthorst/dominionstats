"""Figure out per-player statistics in advance"""

import logging

from name_merger import norm_name
import dominionstats.utils.log
import game
import keys
import utils


# Module-level logging instance
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def calculate_game_stats(games, game_stats):
    """ Save game statistics for each game and player

    games: List of games to analyze, each in dict format
    game_stats: Destination MongoDB collection
    """
    log.debug("Beginning to analyze game statistics for %d games", len(games))
    game_stats.ensure_index(keys.NAME)
    for game_dict in games:
        game_val = game.Game(game_dict)
        g_id = game_dict['_id']
        date = game_dict['game_date']
        supply = game_dict[keys.SUPPLY]

        for p in get_game_stat_entries(game_val, g_id, date, supply):
            game_stats.save(p)
            

def get_game_stat_entries(game_val, g_id, date, supply):
    ret = []
    if game_val.dubious_quality():
        return ret
    all_p = game_val.all_player_names()
    for full_name in all_p:
        m = {}
        name = norm_name(full_name)
        m['_id'] = "%s/%s" % (g_id, name)
        m[keys.NAME] = name
        m[keys.PLAYERS] = [p for p in all_p if p != full_name]
        m['game_date'] = date

        pd = game_val.get_player_deck(full_name)
        m[keys.WIN_POINTS] = pd.WinPoints()
        m[keys.RESULT] = game_val.win_loss_tie(full_name)
        m[keys.ORDER] = pd.TurnOrder()
        m[keys.SUPPLY] = supply
        ret.append(m)

    return ret


def main(args):
    db = utils.get_mongo_database()
    games = db.games
    game_stats = db.game_stats

    for player_name in args.players:
        log.debug("Processing top level player name %s", player_name)
        norm_target_player = norm_name(player_name)
        games_coll = games.find({keys.PLAYERS: norm_target_player})

        calculate_game_stats(list(games_coll), game_stats)


if __name__=='__main__':
    parser = utils.base_parser()
    parser.add_argument(
        '--players', nargs='+',
        help='Check only the player(s) specified')
    parsed_args = parser.parse_args()
    dominionstats.utils.log.initialize_logging(parsed_args.debug)
    main(parsed_args)
