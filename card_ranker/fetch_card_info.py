#!/usr/bin/python

import urllib

contents = urllib.urlopen('http://councilroom.com/supply_win_api').read()
open('card_stats.json', 'w').write(contents)

