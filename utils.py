#!/usr/bin/python

import ConfigParser
import argparse
import datetime
import logging
import logging.handlers
import os
import pymongo
import time

import primitive_util


# Module-level logging instance
logger = logging.getLogger(__name__)


# http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
def segments(lis, chunk_size):
    """ Return an iterator over sublists whose size matches chunk_size. """
    for i in xrange(0, len(lis), chunk_size):
        yield lis[i:i + chunk_size]


def get_aws_credentials():
    """Retrieve the AWS credentials from the config file

    Returned in a dict, so you can make a call like:

        boto.s3.connection.S3Connection(**utils.get_aws_credentials())
    """
    config = ConfigParser.ConfigParser()
    config.read('conf.ini')

    return {'aws_access_key_id': config.get('aws', 'aws_access_key_id'),
            'aws_secret_access_key': config.get('aws', 'aws_secret_access_key')}


def get_mongo_connection():
   mongo_connection = 'localhost'

   try:
      config = ConfigParser.ConfigParser()
      config.read('conf.ini')

      mongo_connection = config.get('mongo', 'connection')
   #FIXME: this is too broad
   except:
      pass

   return pymongo.Connection(mongo_connection)

# Should I read once somewhere and cache?  I guess when
#   we have more config things.
def get_mongo_database():
   connection = get_mongo_connection()

   db = None
   try:
      config = ConfigParser.ConfigParser()
      config.read('conf.ini')

      db = connection[config.get('mongo', 'database')]
   except:
      db = connection['test']

   return db


def get_bad_leaderboard_dates():
    """Return a list of leaderboard dates that should be skipped

    List comes from the conf.ini file, as a multi-line entry under:

    [leaderboard]
    known bad dates = 2011-11-24
        2011-11-25
        2011-11-26
        2011-11-27
        2011-11-28
    """

    try:
        config = ConfigParser.ConfigParser()
        config.read('conf.ini')
        bad_dates = str(config.get('leaderboard', 'known bad dates')).strip().splitlines()
    except:
        logger.exception("Got exception, using default list")
        bad_dates = ['2011-11-24', '2011-11-25', '2011-11-26', '2011-11-27',
                     '2011-11-28', '2011-11-29', '2011-11-30', '2011-12-01',
                     '2011-12-02', '2011-12-03', '2011-12-04', '2012-06-08', ]

    return bad_dates


def read_object_from_db(obj, collection, _id):
   prim = collection.find_one({'_id': _id})
   if prim:
      obj.from_primitive_object(prim)

def write_object_to_db(obj, collection, _id):
    prim = primitive_util.to_primitive(obj)
    prim['_id'] = _id
    collection.save(prim)

def ensure_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def at_least_as_big_as(path, min_file_size):
    if not os.path.exists(path):
        return False
    return os.stat(path).st_size >= min_file_size


def daterange(start_date, end_date, reverse=False):
    """Returns a generator that produces the datetime.date() objects
    that are between start_date (inclusive) and end_date (exclusive).

    Normally returns dates in the natural order between start_date and
    end_date, but when reverse=True is passed, the sequence will be
    reversed.
    """
    if end_date >= start_date:
        step = 1
    else:
        step = -1

    sequence = range(0, (end_date - start_date).days, step)
    if reverse:
        sequence = reversed(sequence)

    for n in sequence:
        yield start_date + datetime.timedelta(n)


def base_parser():
    """Root command line parser for scripts"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False, help='Output debug detail')
    return parser

def incremental_parser():
    """Command line parser for scripts that handle the --noincremental arg"""
    parser = base_parser()
    parser.add_argument('--noincremental', action='store_false',
                        dest='incremental')
    return parser

def incremental_max_parser():
   parser = incremental_parser()
   parser.add_argument('--max_games', default=-1, type=int)
   return parser

def incremental_date_range_cmd_line_parser():
    parser = incremental_parser()
    # 20101015 is the first day with standard turn labels
    parser.add_argument('--startdate', default='20101015')
    parser.add_argument('--enddate', default='99999999')
    parser.add_argument('--passive', action='store_true')
    return parser

def includes_day(args, str_yyyymmdd):
    assert len(str_yyyymmdd) == 8, '%s not 8 chars' % str_yyyymmdd
    return args.startdate <= str_yyyymmdd <= args.enddate

def progress_meter(iterable, log=logger, chunksize=1000):
    """ Logs progress through iterable at chunksize intervals."""
    scan_start = time.time()
    since_last = time.time()
    for idx, val in enumerate(iterable):
        if idx % chunksize == 0 and idx > 0:
            log.info("Iteration: %5d; avg rate: %7.1f/s; inst rate: %7.1f/s",
                     idx,
                     idx / (time.time() - scan_start),
                     chunksize / (time.time() - since_last))
            since_last = time.time()
        yield val


# See http://code.activestate.com/recipes/498245-lru-and-lfu-cache-decorators/
import collections
import functools

def lru_cache(maxsize=100):
    '''Least-recently-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    '''
    def decorating_function(user_function):
        cache = collections.OrderedDict()    # order: least recent to most recent

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            key = args
            if kwds:
                key += tuple(sorted(kwds.items()))
            try:
                result = cache.pop(key)
                wrapper.hits += 1
            except KeyError:
                result = user_function(*args, **kwds)
                wrapper.misses += 1
                if len(cache) >= maxsize:
                    cache.popitem(0)    # purge least recently used cache entry
            cache[key] = result         # record recent use of this key
            return result
        wrapper.hits = wrapper.misses = 0
        return wrapper
    return decorating_function
