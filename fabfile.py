
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

def install_build_deps():
    """Install Debian/Ubuntu packages that are needed to install/build
    the Python packages specified in the pip requirements files.

    We're working under the assumption (proven correct so far, but not
    guaranteed) that the build dependencies for the Debian equivalent
    of the python package are sufficient to build the latest version
    of the package from pypi.
    """
    local('sudo apt-get build-dep python-matplotlib')
    local('sudo apt-get build-dep python-sklearn')
