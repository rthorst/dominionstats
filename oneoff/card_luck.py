import common
import sys
sys.path.append('..')
import trueskill.trueskill as ts

import random

def main():
    games = common.parse_games()
    table = ts.SkillTable()

    for g in games:
        if random.random() < .5:
            continue
        scores_names = zip([g.margin, 0], g.names)
        scores_names.sort(reverse = True)
        print scores_names[0][1], ':', table.get_mu(scores_names[0][1]), ':',
        print scores_names[1][1], ':', table.get_mu(scores_names[1][1]), ':',
        team_results = [([n], [1.0], idx) for idx, (s, n) 
                        in enumerate(scores_names)]
        prob = ts.update_trueskill_team(team_results, table)
        print prob, ':', ','.join(g.supply)
    

if __name__ == '__main__':
    main()
