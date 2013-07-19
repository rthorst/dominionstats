import pymongo
from keys import *

if __name__ == '__main__':
    c = pymongo.Connection()
    db = c.test
    games = db.games
    ct = 0
    print games.find({PLAYERS: 'rrenaud'})
    for g in games.find({PLAYERS: 'rrenaud'}).min({'_id': 'game-2011'}):
        print g['_id']

