
from fabric.api import *
import bz2
import codecs

import utils


def retrieve_test_game(game_id):
    """Store the raw game for the passed game id in the test data dir.
    """
    db = utils.get_mongo_database()
    raw_games_col = db.raw_games
    rawgame = raw_games_col.find_one({'_id': game_id})

    if rawgame is None:
        print('could not find game ' + game_id)
    else:
        contents = bz2.decompress(rawgame['text']).decode('utf-8')
        with codecs.open('testing/testdata/'+game_id, encoding='utf-8', mode='w') as f:
            f.write(contents)
