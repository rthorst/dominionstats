#!/usr/bin/python

import codecs
import unittest

import game
import goals
import parse_game


def goals_for(game_id, player=None, goal_name=None):
    """Return the list of goals for the passed game id"""
    test_game = game.Game(parse_game.parse_game( \
            codecs.open('testing/testdata/'+game_id, encoding='utf-8').read()))
    found_goals = goals.check_goals(test_game)

    if player:
        found_goals = [g for g in found_goals if g['player'] == player]

    if goal_name:
        found_goals = [g for g in found_goals if g['goal_name'] == goal_name]

    return found_goals




class GoalTest(unittest.TestCase):
    """ Test cases for goals.
    """

    def validate_goal_for(self, game_id, player, goal_name):
        found_goals = goals_for(game_id, player, goal_name)
        self.assertEqual(1, len(found_goals),
                         'Failed to find {gn} for {p} in {gi}'.format(gn=goal_name,
                                                                      p=player,
                                                                      gi=game_id))


    def test_purple_pile_driver_alone(self):
        """Test purple pile driver goal in isolation.

        For example, is it awarded successfully when only the curses
        pile is acquired by a player.
        """

        self.validate_goal_for('game-20110803-135820-f9c87de6.html',
                               u'Sayron',
                               'PurplePileDriver')


    def test_purple_pile_driver_alone_v2(self):
        """Test purple pile driver goal in isolation.

        For example, is it awarded successfully when only the curses
        pile is acquired by a player.
        """

        self.validate_goal_for('game-20121201-103128-e6e30146.html',
                               u'Varsinor',
                               'PurplePileDriver')


    def test_purple_pile_driver_combo(self):
        """Test combos with purple and other pile driver goals.

        See if the purple pile driver is awarded successfully when
        both the curses pile and another are acquired by a player.
        """

        self.validate_goal_for('game-20130111-164348-84fd128e.html',
                               u'Wolphmaniac',
                               'PurplePileDriver')

        self.validate_goal_for('game-20130111-164348-84fd128e.html',
                                u'Wolphmaniac',
                                'DoublePileDriver')

if __name__ == '__main__':
    unittest.main()
