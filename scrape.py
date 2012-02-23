#!/usr/bin/python

# taken from 
# http://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python

import datetime
import time
import os
import urllib
import utils
import sys

# if the size of the game log is less than this assume we got an error page
SMALL_FILE_SIZE = 5000 

DEBUG = False

GOOD = 0
MISSING = 1
ERROR = 2
DOWNLOADED = 3

# make I should just adopt the isotropic format for consistency?
ISOTROPIC_FORMAT =   '%(year)d%(month)02d/%(day)02d/all.tar.bz2'
COUNCILROOM_FORMAT = '%(year)d%(month)02d%(day)02d/%(year)d%(month)02d%(day)02d.all.tar.bz2'

def FormatDate(fmt, cur_date):
    return fmt % {
        'year': cur_date.year, 'month': cur_date.month, 'day': cur_date.day
        }

def IsotropicGamesCollectionUrl(cur_date):
    host = 'http://dominion.isotropic.org/gamelog/'
    return host + FormatDate(ISOTROPIC_FORMAT, cur_date)

def CouncilroomGamesCollectionUrl(cur_date):
    host = 'http://councilroom.com/static/scrape_data/'
    return host + FormatDate(COUNCILROOM_FORMAT, cur_date)

def RemoveSmallFileIfExists(fn):
    if (os.path.exists(fn) and 
        os.stat(fn).st_size <= SMALL_FILE_SIZE):
        print 'removing small existing file', fn
        os.unlink(fn)

def download_date(str_date, cur_date):
    urls_by_priority = [CouncilroomGamesCollectionUrl(cur_date),
                        IsotropicGamesCollectionUrl(cur_date)] 

    for url in urls_by_priority:
        if DEBUG:
            print 'getting', saved_games_bundle, 'at', url

        contents = urllib.urlopen(url).read()
        if len(contents) > SMALL_FILE_SIZE:
            if DEBUG:
                print 'yay, success from', url, 'no more requests for', \
                    str_date, 'needed'
            open(saved_games_bundle, 'w').write(contents)
            return True
        elif DEBUG:
            print 'request to', url, 'failed to find large file'
    return False

def unzip_date(directory, filename):
    os.chdir(directory)
    cmd = 'tar -xjvf %s >/dev/null 2>/dev/null'%filename
    if DEBUG:
        print cmd

    ret = os.system(cmd)
    if ret==0:
        os.system('chmod -R 755 .')
        code = True
    else:
        code = False
    os.chdir('..')
    return code
    

def scrape_date(str_date, cur_date, passive=False):
    directory = str_date
    games_short_name = str_date + '.all.tar.bz2'
    saved_games_bundle = directory + '/' + games_short_name
    if utils.at_least_as_big_as(saved_games_bundle, SMALL_FILE_SIZE):
        if DEBUG:
            print 'skipping because exists', str_date, saved_games_bundle, \
                'and not small (size=', os.stat(saved_games_bundle).st_size, ')'
        return GOOD
    else:
        if not os.path.exists(directory):
            os.mkdir(directory)
        RemoveSmallFileIfExists(saved_games_bundle)

        if passive:
            return MISSING

        if download_date(str_date, cur_date):
            return ERROR

        time.sleep(5)
        if unzip_date(directory, games_short_name):
            return DOWNLOADED
        else:
            return ERROR

def scrape_games():
    parser = utils.incremental_date_range_cmd_line_parser()
    utils.ensure_exists('static/scrape_data')
    os.chdir('static/scrape_data')

    args = parser.parse_args()
    last_month = ''

    for cur_date in utils.daterange(datetime.date(2010, 10, 15), 
                                    datetime.date.today()):
        str_date = time.strftime("%Y%m%d", cur_date.timetuple())
        if not utils.includes_day(args, str_date):
            if DEBUG:
                print 'skipping', str_date, 'because not in cmd line arg daterange'
            continue
        mon = time.strftime("%b%y", cur_date.timetuple())
        if mon != last_month:
            print
            print mon, cur_date.day*"  ",
            sys.stdout.flush()
            last_month = mon
        ret = scrape_date(str_date, cur_date, passive=args.passive)
        if ret==DOWNLOADED:
            print 'o',
        elif ret==ERROR:
            print '!',
        elif ret==MISSING:
            print '_',
        else:
            print '.',
        sys.stdout.flush()
    print
    os.chdir('../..')


if __name__=='__main__':
    scrape_games()
                        
