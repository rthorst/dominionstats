 #!/usr/bin/python

"""Standard update script to keep data up-to-date."""

import celery
import collections
import datetime
import logging
import time

import analyze
import background.tasks
import count_buys
import dominionstats.utils.log
import load_leaderboard
import optimal_card_ratios
import run_trueskill
import scrape_leaderboard
import utils


# Module-level logging instance
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def summarize_task_status(c):
    """Return a string summarize the state of the task and its children"""
    return "{tot_tasks} subtasks: {detail}".format(tot_tasks=sum(c.values()),
                                                   detail=str(c))


def watch_and_log(signature, log_interval=15):
    """Invoke the celery task via the passed signature, wait for it an
    all its children to complete, and log progress along the way."""
    task_name = signature.task
    log.info("Calling background task %s", task_name)

    async_result = signature.apply_async()

    all_done = False
    while not all_done:
        # Wait for the log_interval, then check the status
        time.sleep(log_interval)

        c = collections.Counter()
        try:
            # Setting intermediate to False should cause the
            # IncompleteStream exception to be thrown if the task and
            # its children aren't all complete.
            for parent, child in async_result.iterdeps(intermediate=False):
                c[child.state] += 1
            all_done = True
        except celery.exceptions.IncompleteStream:
            log.info("Waiting for %s: %s", task_name, summarize_task_status(c))

    log.info("Done with background task %s: %s", task_name, summarize_task_status(c))
    return async_result


def main(parsed_args):
    """Primary update cycle"""

    # Scrape and load the data from isotropic, proceeding from the
    # current day backwards, until no games are inserted
    log.info("Starting scrape for raw games")
    for date in utils.daterange(datetime.date(2010, 10, 15),
                                datetime.date.today(), reverse=True):
        log.info("Scraping for %s", date)
        async_result = watch_and_log(background.tasks.scrape_raw_games.s(date))
        inserted = async_result.get()

        if inserted is None:
            log.info("Nothing processed for %s", date)
        elif inserted == 0:
            log.info("No games inserted for %s", date)
            break

    # Invoke the analyze script
    log.info("Starting analyze")
    analyze.main(parsed_args)

    # Check for goals
    log.info("Starting search for goals acheived")
    for date in utils.daterange(datetime.date(2010, 10, 15),
                                datetime.date.today(), reverse=True):
        log.info("Searching for goals on %s", date)
        async_result = watch_and_log(background.tasks.calc_goals_for_days.s([date]))
        inserted = async_result.get()

        if inserted == 0:
            log.info("No games parsed for goals on %s", date)
            break

    # Check for game_stats
    log.info("Starting game_stats summarization")
    for date in utils.daterange(datetime.date(2010, 10, 15),
                                datetime.date.today(), reverse=True):
        log.info("Summarizing games on %s", date)
        async_result = watch_and_log(background.tasks.summarize_game_stats_for_days.s([date]))
        inserted = async_result.get()

        if inserted == 0:
            log.info("No new games summarized on %s", date)
            break

    # Invoke the count_buys script
    log.info("Counting buys")
    count_buys.main(parsed_args)

    # Invoke the run_trueskill script
    log.info("Calculating trueskill")
    run_trueskill.main(parsed_args)

    # Invoke the optimal_card_ratios script
    log.info("Calculating optimal card ratios")
    optimal_card_ratios.main(parsed_args)

    # Invoke the scrape_leaderboard script
    log.info("Scraping the leaderboard")
    scrape_leaderboard.main()

    # Invoke the load_leaderboard script
    log.info("Loading the leaderboard")
    load_leaderboard.main()


if __name__ == '__main__':
    parser = utils.incremental_max_parser()
    args = parser.parse_args()
    dominionstats.utils.log.initialize_logging(args.debug)
    main(args)
