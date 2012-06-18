#!/usr/bin/python

import sys
sys.path.append('..')
import card_info
import urllib
import simplejson as json
import time

def main():
    all_cards = ','.join(card_info.card_names())
    all_data = []
    for card in card_info.card_names()[1:]:
        url = ('http://councilroom.com/supply_win_api?'
               'targets=%s&interaction=%s' % (card, all_cards))
        time.sleep(.1)
        print card
        contents = urllib.urlopen(url).read()
        parsed_contents = json.loads(contents)
        all_data.extend(parsed_contents)
        print 'len data', len(all_data)
    open('card_conditional_data.json', 'w').write(json.dumps(all_data))
    

if __name__ == '__main__':
    main()
