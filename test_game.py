#!/usr/bin/python

from keys import *
import card
import codecs
import game
import parse_game
import unittest

class ScoreDeckTest(unittest.TestCase):
    def test_gardens(self):
        self.assertEquals(game.score_deck({'Gardens': 1, 'Copper': 9}), 1)
        self.assertEquals(game.score_deck({'Gardens': 2, 'Copper': 8}), 2)
        self.assertEquals(game.score_deck({'Gardens': 2, 'Copper': 7}), 0)

    def test_fairgrounds(self):
        self.assertEquals(game.score_deck({'Fairgrounds': 1,
                                           'Copper': 1,
                                           'Silver': 1,
                                           'Gold': 1,
                                           'Bank': 1}), 2)

    def test_duke(self):
        self.assertEquals(game.score_deck({'Duke': 2, 'Duchy': 2}), 10)

    def test_simple(self):
        self.assertEquals(game.score_deck({
                    'Curse': 1, 'Estate': 1, 'Duchy': 1,
                    'Province': 1, 'Colony': 1}), 19)

    def test_vineyards(self):
        self.assertEquals(game.score_deck({'Vineyard': 2, 'Jester': 3,
                                           'Fishing Village': 3}), 4)

def make_deck(name, points, win_points, order):
    return {NAME: name, POINTS: points, WIN_POINTS: win_points,
            DECK: {}, ORDER: order, TURNS: [],}

class WinLossTieTest(unittest.TestCase):
    def test_win_loss_tie_3p(self):
        g = game.Game(
            {DECKS: [make_deck('p1', 1, 1.5, 1),
                     make_deck('p2', 1, 1.5, 2),
                     make_deck('p3', 0, 0, 3),],
             SUPPLY: [], '_id': ''})
        self.assertEquals(game.TIE, g.win_loss_tie('p1', 'p2'))
        self.assertEquals(game.TIE, g.win_loss_tie('p2', 'p1'))
        self.assertEquals(game.WIN, g.win_loss_tie('p1', 'p3'))
        self.assertEquals(game.LOSS, g.win_loss_tie('p3', 'p1'))

class GameStateTest(unittest.TestCase):
    def _get_turn_labels(self, game_state_it):
        return [game_state_it.turn_label() for t in game_state_it]

    def test_turn_labels(self):
        # 'game-20101015-094051-95e0a59e.html' contains Outpost card
        outpost_game = game.Game(parse_game.parse_game( \
                open('testing/testdata/game-20101015-094051-95e0a59e.html', 'r').read()))
        turn_labels = self._get_turn_labels(outpost_game.game_state_iterator())
        for game_state in outpost_game.game_state_iterator():
            pass

class PlayerDeckTest(unittest.TestCase):
    def test_deck_composition(self):
        outpost_game = game.Game(parse_game.parse_game( \
                open('testing/testdata/game-20101015-094051-95e0a59e.html', 'r').read()))
        last_state = None
        game_state_iterator = outpost_game.game_state_iterator()
        for game_state in game_state_iterator:
            last_state = game_state
        for player_deck in outpost_game.get_player_decks():

            parsed_deck_comp = player_deck.Deck()
            computed_deck_comp = last_state.get_deck_composition(
                player_deck.name())

            for card in set(parsed_deck_comp.keys() +
                            computed_deck_comp.keys()):
                self.longMessage = True
                self.assertEqual(parsed_deck_comp.get(card, 0), computed_deck_comp.get(card, 0), card)


class ParsedGameStructureTest(unittest.TestCase):
    """ Test cases for game structures.
    """

    def test_game_with_dots_in_player_name(self):
        """ Test vetoes with names containing dots.
        """

        test_game = game.Game(parse_game.parse_game( \
                codecs.open('testing/testdata/game-20120415-072057-6d356cf1.html', encoding='utf-8').read()))
        last_state = None
        game_state_iterator = test_game.game_state_iterator()
        for game_state in game_state_iterator:
            last_state = game_state
        self.assertEquals(test_game.vetoes[str(test_game.all_player_names().index(u'nrggirl'))], int(card.PirateShip.index))
        self.assertEquals(test_game.vetoes[str(test_game.all_player_names().index(u'Mr.Penskee'))], int(card.Masquerade.index))


if __name__ == '__main__':
    unittest.main()
