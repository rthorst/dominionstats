#!/bin/bash

# Exit immediately if any command returns non-zero
set -e

if [ $# -ne 1 ]
then
    echo Usage: multi_scrape.sh [goko logdir]
    echo Example: multi_scrape.sh 20130513
    exit -1
fi

BASE_ARCHIVE=http://archive-dominionlogs.goko.com/$1/

mkdir $1

# Give up after 900 seconds (-Qt), don't display progress statistics
# (-ns), display errors (-v), recurse into subdirectories (-r), but
# only one level deep (-l 1), only accept files with a txt suffix (-A
# txt).

# NOTE: If this runs in spurts (lots of traffic for a bit and then
# nothing, then lots again and then nothing, ...), or if it is timing
# out, it might be due to overloading the connection tracking tables
# on your network device (e.g., your cable modem router). Installing a
# squid proxy and configuring puf to use it (-y param) will eliminate
# this.
#
# TODO: Install local squid proxy and use it.

echo Retrieving the game logs
time puf -Qt 900 -ns -v -r -l 1 -A txt $BASE_ARCHIVE

echo Repackaging the game logs
time tar -cjf $1.tar.bz2 $1

echo Done
