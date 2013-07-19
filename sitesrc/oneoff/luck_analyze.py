#!/usr/bin/python
# -*- coding: utf-8 -*-

import collections
import math
import sys
sys.path.append('..')
import stats

def main():
    confusion_stats = collections.defaultdict(stats.MeanVarStat)
    for idx, line in enumerate(open('card_luck1.txt')):
        try:
            contents = line.split(':')
            prob = float(contents[4])
            cards = contents[5].split(',')
            confusion = -math.log(prob)
            for card in cards:
                card = card.strip()
                confusion_stats[card].add_outcome(confusion)
        except IndexError:
            break
    confusion_stats = confusion_stats.items()
    confusion_stats.sort(key = lambda x: x[1].mean())
    for card, stat in confusion_stats:
        print card, stat.render_interval(sig_digits=3)
        

if __name__ == '__main__':
    main()
