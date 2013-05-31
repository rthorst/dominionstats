#!/bin/bash

if [ $# -ne 1 ]
then
    echo Usage: multi_scrape.sh [goko logdir]
    echo Example: multi_scrape.sh 20130513
    exit -1
fi

BASE=http://archive-dominionlogs.goko.com/$1/
THREADS=20

wget --header='Accept-Encoding: gzip' $BASE -O- | zcat | perl -lne 'print "$1" if /href="(.*?txt)"/' > _all

if [ `cat _all | wc -l` -gt 0 ]
then
    cat _all | split -l 100 - _index.
    ls _index.* | xargs -n 1 -P $THREADS wget --base=$BASE --header='Accept-Encoding: gzip' -i
    rm _index.*
    echo "Decompressing"
fi

#rm _all_bz2 
#touch _all_bz2

for x in `cat _all`
do
    mv $x $x.gz
    gunzip $x.gz
    #tar cjf $x.bz2 $x 
    #echo $x.bz2 >> _all_bz2
done

tar cjf $1.all.tar.bz2 -T _all
#tar cf $1.bz2.tar -T _all_bz2


for x in `cat _all` #_all_bz2`
do
    rm $x
done

rm _all
#rm _all_1z2

