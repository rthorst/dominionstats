#!/usr/bin/python

from keys import *
import dominioncards
import codecs
import game
import parse_game
import unittest

class ScoreDeckTest(unittest.TestCase):
    def test_gardens(self):
        self.assertEquals(game.score_deck({dominioncards.Gardens: 1, dominioncards.Copper: 9}), 1)
        self.assertEquals(game.score_deck({dominioncards.Gardens: 2, dominioncards.Copper: 8}), 2)
        self.assertEquals(game.score_deck({dominioncards.Gardens: 2, dominioncards.Copper: 7}), 0)

    def test_fairgrounds(self):
        self.assertEquals(game.score_deck({dominioncards.Fairgrounds: 1,
                                           dominioncards.Copper: 1,
                                           dominioncards.Silver: 1,
                                           dominioncards.Gold: 1,
                                           dominioncards.Bank: 1}), 2)

    def test_duke(self):
        self.assertEquals(game.score_deck({dominioncards.Duke: 2, dominioncards.Duchy: 2}), 10)

    def test_simple(self):
        self.assertEquals(game.score_deck({
                    dominioncards.Curse: 1, dominioncards.Estate: 1, dominioncards.Duchy: 1,
                    dominioncards.Province: 1, dominioncards.Colony: 1}), 19)

    def test_vineyards(self):
        self.assertEquals(game.score_deck({dominioncards.Vineyard: 2, dominioncards.Jester: 3,
                                           dominioncards.FishingVillage: 3}), 4)

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
    outpost_game = game.Game(parse_game.parse_game( \
            open('testing/testdata/game-20101015-094051-95e0a59e.html', 'r').read()))

    def _get_turn_labels(self, game_state_it):
        return [game_state_it.turn_label() for t in game_state_it]

    def test_turn_labels(self):
        # 'game-20101015-094051-95e0a59e.html' contains Outpost card
        turn_labels = self._get_turn_labels(self.outpost_game.game_state_iterator())
        for game_state in self.outpost_game.game_state_iterator():
            pass

    def test_score(self):
        self.assertEquals(game.score_deck(self.outpost_game.get_player_deck('moop').deck),
                          42)
        self.assertEquals(game.score_deck(self.outpost_game.get_player_deck('qzhdad').deck),
                          30)


class PlayerDeckTest(unittest.TestCase):

    outpost_game = game.Game(parse_game.parse_game( \
            open('testing/testdata/game-20101015-094051-95e0a59e.html', 'r').read()))

    deck_changes_game = game.Game(parse_game.parse_game( \
            open('testing/testdata/game-20101015-024842-a866e78a.html', 'r').read()))


    def test_deck_composition(self):
        last_state = None
        game_state_iterator = self.outpost_game.game_state_iterator()
        for game_state in game_state_iterator:
            last_state = game_state
        for player_deck in self.outpost_game.get_player_decks():

            parsed_deck_comp = player_deck.Deck()
            computed_deck_comp = last_state.get_deck_composition(
                player_deck.name())

            for card in set(parsed_deck_comp.keys() +
                            computed_deck_comp.keys()):
                self.longMessage = True
                self.assertEqual(parsed_deck_comp.get(card, 0), computed_deck_comp.get(card, 0), card)

    def test_deck_changes_per_player(self):
        self.assertEquals(['Celicath', 'tafkal'], self.deck_changes_game.all_player_names())

        pd = self.deck_changes_game.get_player_decks()[0]
        self.assertEquals('Celicath', pd.name())
        pd = self.deck_changes_game.get_player_decks()[1]
        self.assertEquals('tafkal', pd.name())

        for changes in self.deck_changes_game.deck_changes_per_player():
            win_points = self.deck_changes_game.get_player_deck(changes.name).WinPoints()



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
        self.assertEquals(test_game.vetoes[str(test_game.all_player_names().index(u'nrggirl'))], int(dominioncards.PirateShip.index))
        self.assertEquals(test_game.vetoes[str(test_game.all_player_names().index(u'Mr.Penskee'))], int(dominioncards.Masquerade.index))


if __name__ == '__main__':
    unittest.main()
