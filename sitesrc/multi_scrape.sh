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

# Give up after 600 seconds (-Qt), don't display progress statistics
# (-ns), display errors (-v), recurse into subdirectories (-r), but
# only one level deep (-l 1), only accept files with a txt suffix (-A
# txt).
echo Retrieving the game logs
time puf -Qt 600 -ns -v -r -l 1 -A txt $BASE_ARCHIVE

echo Repackaging the game logs
time tar -cjf $1.tar.bz2 $1

echo Done
