#!/usr/bin/python

# taken from 
# http://stackoverflow.com/questions/1060279/iterating-through-a-range-of-dates-in-python

import datetime
import glob
import logging
import os
import os.path
import subprocess
import sys
import tempfile
import time
import urllib
import utils

# if the size of the game log is less than this assume we got an error page
SMALL_FILE_SIZE = 5000 

DEBUG = False

GOOD = 0
MISSING = 1
ERROR = 2
DOWNLOADED = 3
REPACKAGED = 4

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
        print('removing small existing file', fn)
        os.unlink(fn)

def download_date(str_date, cur_date, saved_games_bundle):
    urls_by_priority = [
                        CouncilroomGamesCollectionUrl(cur_date),
                        IsotropicGamesCollectionUrl(cur_date),
                        ] 

    for url in urls_by_priority:
        if DEBUG:
            print('getting', saved_games_bundle, 'at', url)

        contents = urllib.urlopen(url).read()
        if len(contents) > SMALL_FILE_SIZE:
            if DEBUG:
                print('yay, success from', url, 'no more requests for', \
                    str_date, 'needed')
            open(saved_games_bundle, 'w').write(contents)
            return True
        elif DEBUG:
            print('request to', url, 'failed to find large file')
    return False

def unzip_date(directory, filename):
    os.chdir(directory)
    cmd = 'tar -xjvf %s >/dev/null 2>/dev/null'%filename
    if DEBUG:
        print(cmd)

    ret = os.system(cmd)
    if ret==0:
        os.system('chmod -R 755 .')
        code = True
    else:
        code = False
    os.chdir('..')
    return code


def repackage_filename(orig_archive_filename):
    return orig_archive_filename.replace(".all.tar.bz2", ".bz2.tar")
    

def repackage_archive(filename):
    """ Converts a .tar.bz2 file into a .bz2.tar file in the same directory.

    Game archives are distributed as .tar.bz2 (a bzip2-compressed tar
    archive). For speed of serving, we repackage them as .bz2.tar (a
    tar archive of bzip2-compressed HTML files). The .bz2.tar file is
    a good bit larger, but an individual file can be extracted,
    decompressed, and served to a client in tenths of a second instead
    of tens of seconds. At the same time, storage space is still
    dramatically smaller than a raw folder of uncompressed (or even
    compressed) HTML files.
    """

    orig_dir = os.getcwd()

    # Extract the existing file into a temporary folder
    directory_name = tempfile.mkdtemp()
    source_filename = os.path.abspath(filename)
    try:
        subprocess.check_call(["tar", "--auto-compress", "-C", directory_name,
                               "-xf", source_filename])
    except subprocess.CalledProcessError as e:  
        # Not handling this yet, just re-raise
        logging.warning("Unexpected return from tar >>{msg}<<".format(msg=e.output))
        raise

    # Compress all the game*.html files
    os.chdir(directory_name)
    game_files = glob.glob("game*.html")
    if len(game_files) > 0:
        try:
            subprocess.check_call(["bzip2"] + game_files)
        except subprocess.CalledProcessError as e:  #(retcode, cmd, output=output)
            # Not handling this yet, just re-raise
            logging.warning("Unexpected return from bzip >>{msg}<<".format(msg=e.output))
            raise
    else:
        os.chdir(orig_dir)
        os.removedirs(directory_name)
        return

    # Tar the results back to the directory where the original file
    # came from
    dest_filename = repackage_filename(source_filename)
    game_files = glob.glob("game*.html.bz2")
    try:
        subprocess.check_call(["tar", "--remove", "-cf", dest_filename+".part"] + game_files)
    except subprocess.CalledProcessError as e:  #(retcode, cmd, output=output)
        # Not handling this yet, just re-raise
        logging.warning("Unexpected return from tar >>{msg}<<".format(msg=e.output))
        raise

    os.rename(dest_filename + ".part", dest_filename)
    os.chdir(orig_dir)
    os.removedirs(directory_name)


def scrape_date(str_date, cur_date, passive=False):
    #directory = str_date
    games_short_name = str_date + '.all.tar.bz2'
    saved_games_bundle = games_short_name
    return_code = ERROR

    if utils.at_least_as_big_as(saved_games_bundle, SMALL_FILE_SIZE):
        if DEBUG:
            print('skipping because exists', str_date, saved_games_bundle, \
                'and not small (size=', os.stat(saved_games_bundle).st_size, ')')
        return_code = GOOD
    else:
        RemoveSmallFileIfExists(saved_games_bundle)

        if passive:
            return_code = MISSING

        elif not download_date(str_date, cur_date, saved_games_bundle):
            return_code = ERROR

        return_code = DOWNLOADED

    # Repackage an existing file, if found
    if utils.at_least_as_big_as(saved_games_bundle, SMALL_FILE_SIZE) and \
            not os.path.exists(repackage_filename(saved_games_bundle)):
        repackage_archive(saved_games_bundle)
        return_code = REPACKAGED

    return return_code


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
                print('skipping', str_date, 'because not in cmd line arg daterange')
            continue
        mon = time.strftime("%b%y", cur_date.timetuple())
        if mon != last_month:
            print(mon, cur_date.day*"  ")
            sys.stdout.flush()
            last_month = mon
        ret = scrape_date(str_date, cur_date, passive=args.passive)
        if ret==DOWNLOADED:
            print('o')
        elif ret==REPACKAGED:
            print('O')
        elif ret==ERROR:
            print('!')
        elif ret==MISSING:
            print('_')
        else:
            print('.')
        sys.stdout.flush()
    print("")
    os.chdir('../..')


if __name__=='__main__':
    scrape_games()
                        
