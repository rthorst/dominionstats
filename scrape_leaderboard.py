#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os
import datetime
import httplib
import StringIO
import gzip
import bz2
import utils

output_directory = 'static/leaderboard/'

def get_date_of_last_cached_leaderboard():
    filename_pattern = re.compile('^(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)\.html\.bz2$')
    filenames = os.listdir(output_directory)
    filenames.sort(reverse=True)

    for filename in filenames:
        match = filename_pattern.search(filename)
        if not match:
            continue
        return datetime.date(int(match.group('year')), int(match.group('month')), int(match.group('day')))

    # return the day before the first day on http://bggdl.square7.ch/leaderboard/
    return datetime.date(2011, 3, 10)

def get_date_of_current_isotropic_leaderboard():
    conn = httplib.HTTPConnection('dominion.isotropic.org')
    conn.request('HEAD', '/leaderboard/')
    res = conn.getresponse()
    headers = dict(res.getheaders())
    conn.close()

    if res.status == 200:
        # just after midnight Pacific time, GMT will have the same calendar date as Pacific time
        # so, we can ignore the hour, minute, and second
        return datetime.datetime.strptime(headers['last-modified'], '%a, %d %b %Y %H:%M:%S %Z').date()

# originally from http://bggdl.square7.ch/leaderboard/
def scrape_leaderboard_from_online_cache(date):
    conn = httplib.HTTPConnection('councilroom.com', timeout=30)
    conn.request('GET', '/static/leaderboard/' + str(date) + '.html.bz2')
    res = conn.getresponse()
    data = res.read()
    conn.close()

    if res.status == 200:
        f = open(output_directory + str(date) + '.html.bz2', 'w')
        f.write(data)
        f.close()
        return True
    elif res.status == 404:
        # doesn't exist, but pretend we got it
        return True
    else:
        return False

def scrape_leaderboard_from_isotropic(date):
    conn = httplib.HTTPConnection('dominion.isotropic.org', timeout=30)
    conn.request('GET', '/leaderboard/', headers={'Accept-Encoding': 'gzip'})
    res = conn.getresponse()
    gzipped_data = res.read()
    conn.close()

    if res.status == 200:
        f = gzip.GzipFile(fileobj=StringIO.StringIO(gzipped_data))
        data = f.read()
        f.close()

        data = bz2.compress(data)

        f = open(output_directory + str(date) + '.html.bz2', 'w')
        f.write(data)
        f.close()

        return True
    else:
        return False

def main():
    utils.ensure_exists(output_directory)

    date_of_last_cached_leaderboard = get_date_of_last_cached_leaderboard()
    print 'date of the last cached leaderboard is', date_of_last_cached_leaderboard

    date_of_current_isotropic_leaderboard = get_date_of_current_isotropic_leaderboard()
    if date_of_current_isotropic_leaderboard is None:
        print 'could not determine the date of the current isotropic leaderboard, so please try again later'
        return
    print 'date of the current isotropic leaderboard is', date_of_current_isotropic_leaderboard

    one_day_delta = datetime.timedelta(1)
    date = date_of_last_cached_leaderboard + one_day_delta
    success = True
    num_times_unsuccessful_in_a_row = 0

    while date <= date_of_current_isotropic_leaderboard:
        print
        print date

        if date == date_of_current_isotropic_leaderboard:
            print 'scraping from isotropic'
            success = scrape_leaderboard_from_isotropic(date)
        else:
            print 'scraping from online cache'
            success = scrape_leaderboard_from_online_cache(date)

        if success:
            print 'successful'
            num_times_unsuccessful_in_a_row = 0
            date += one_day_delta
        else:
            num_times_unsuccessful_in_a_row += 1
            print 'unsuccessful', num_times_unsuccessful_in_a_row, 'time(s) in a row'
            if num_times_unsuccessful_in_a_row < 3:
                print 'retrying...'
            else:
                print 'reached max unsuccessful attempts in a row, so please try again later'
                break

if __name__ == '__main__':
    main()

