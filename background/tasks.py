# -*- coding: utf-8 -*-

""" Background tasks for Dominion stats
"""

from __future__ import absolute_import

from celery.utils.log import get_task_logger
import datetime

from background.celery import celery
from goals import calculate_goals
from parse_game import parse_and_insert
import isotropic
import utils


log = get_task_logger(__name__)



@celery.task
def parse_games(games, day):
    """Takes list of game ids and a game date and parses them out."""
    log.info("Parsing %d games for %s", len(games), day)

    connection = utils.get_mongo_connection()
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
    """ Takes a list of one or more days in the format "YYYYMMDD" or
    datetime.date, and generates tasks for each of the individual
    games that occurred on those days.

    Returns the number of individual games found on the specified days
    """
    game_count = 0
    db = utils.get_mongo_database()
    raw_games_col = db.raw_games
    raw_games_col.ensure_index('game_date')

    for day in days:
        if type(day) is datetime.date:
            day = day.strftime('%Y%m%d')
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

    connection = utils.get_mongo_connection()
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
    connection = utils.get_mongo_connection()
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


@celery.task(rate_limit='2/m')
def scrape_raw_games(date):
    """Download the specified raw game archive, store it in S3, and load it into MongoDB.

    date is a datetime.date object
    """
    db = utils.get_mongo_database()

    scraper = isotropic.IsotropicScraper(db)
    inserted = scraper.scrape_and_store_rawgames(date)
    if inserted > 0:
        # Also need to parse the raw games for the days where we
        # inserted new records.
        parse_days.delay([date])


@celery.task
def check_for_work():
    """Examine the state of the database and generate tasks for necessary work.

    This task is intended to be called on a regular basis, e.g., from
    a frequently run cron job. It is intended to scan through the
    database, identify what needs to be done to bring it to a current
    state, and then create the needed tasks.
    """

    connection = utils.get_mongo_connection()
    db = connection.test

    # Scrape isotropic for raw games
    for date in isotropic.dates_needing_scraping(db):
        scrape_raw_games.delay(date)
