# -*- coding: utf-8 -*-

""" Background tasks for Dominion stats
"""

from __future__ import absolute_import

from background.celery import celery
from celery import current_task
from celery.utils.log import get_task_logger
import pymongo

from parse_game import parse_and_insert
from goals import calculate_goals
import utils


log = get_task_logger(__name__)



@celery.task
def add(x, y):
    return x + y


@celery.task
def mul(x, y):
    return x * y


@celery.task
def xsum(numbers):
    return sum(numbers)


@celery.task
def power(x, y):
    return x ** y


@celery.task
def parse_game(game):
    log.info("Parsing %s", game)


@celery.task
def parse_games(games, day):
    log.info("Parsing %d games for %s", len(games), day)

    connection = pymongo.Connection('councilroom.mccllstr.com')
    db = connection.test
    raw_games_col = db.raw_games
    parsed_games_col = db.games
    parse_error_col = db.parse_error

    raw_games = []
    for game_id in games:
        game = raw_games_col.find_one({'_id': game_id})
        if game:
            raw_games.append(game)
        else:
            log.warning('Found nothing for game id %s', game_id)
    
    return parse_and_insert(log, raw_games, parsed_games_col, parse_error_col, day)


@celery.task
def parse_days(days):
    """ Takes a list of one or more days in the format "YYYYMMDD", and
    generates tasks for each of the individual games that occurred on
    those days.

    Returns the number of individual games found on the specified days
    """
    game_count = 0
    connection = pymongo.Connection('councilroom.mccllstr.com')
    db = connection.test
    raw_games_col = db.raw_games
    raw_games_col.ensure_index('game_date')

    for day in days:
        games_to_parse = raw_games_col.find({'game_date': day}, {'_id': 1})

        if games_to_parse.count() < 1:
            log.info('no games to parse in %s', day)
            continue

        game_count += games_to_parse.count()
        log.info('%s games to parse in %s', games_to_parse.count(), day)
        for chunk in utils.segments([x['_id'] for x in games_to_parse], 100):
            parse_games.delay(chunk, day)

    return game_count


@celery.task
def calc_goals(game_ids, day):
    """ Calculate the goals achieved in the passed list of games """
    log.info("Calculating goals for %d game IDs from %s", len(game_ids), day)

    connection = pymongo.Connection('councilroom.mccllstr.com')
    db = connection.test
    games_col = db.games
    goals_col = db.goals
    goals_error_col = db.goals_error

    games = []
    for game_id in game_ids:
        game = games_col.find_one({'_id': game_id})
        if game:
            games.append(game)
        else:
            log.warning('Found nothing for game id %s', game_id)

    return calculate_goals(log, games, goals_col, goals_error_col, day)


@celery.task
def calc_goals_for_days(days):
    """ Takes a list of one or more days in the format "YYYYMMDD", and
    generates task that calculate the goals achieved in each of the
    individual games that occurred on those days.

    Returns the number of individual games found on the specified days
    """
    game_count = 0
    connection = pymongo.Connection('councilroom.mccllstr.com')
    db = connection.test
    games_col = db.games
    games_col.ensure_index('game_date')

    for day in days:
        games_to_process = games_col.find({'game_date': day}, {'_id': 1})

        if games_to_process.count() < 1:
            log.info('no games to parse in %s', day)
            continue

        game_count += games_to_process.count()
        log.info('%s games to parse in %s', games_to_process.count(), day)
        for chunk in utils.segments([x['_id'] for x in games_to_process], 100):
            calc_goals.delay(chunk, day)

    return game_count
