import collections

GameTup = collections.namedtuple('GameTup', ['margin',  'supply', 'names'])

def parse_games(limit = -1):
    games = []
    for line_idx, line in enumerate(open('margin.txt', 'r')):
        if line_idx == limit:
            break
        try:
            split_line = line.strip().split(':')
            if len(split_line) > 3:
                continue
            names = split_line[1]
            split_names = names.split(',')
            if len(split_names) != 2:
                continue
            games.append((GameTup(float(split_line[0]),
                                  split_line[2].split(','),
                                  split_names)))
        except IndexError:
            print line        
    return games
