#!/usr/bin/python

import unittest

import dominioncards


class DominionCardsTest(unittest.TestCase):
    def test_openings(self):
        openings = dominioncards.opening_cards()
        self.assertEquals(len(openings), 140)

        # Valid opening cards

        # Cost 0
        self.assertIn(dominioncards.Copper, openings)

        # Cost 2
        self.assertIn(dominioncards.Chapel, openings)

        # Cost 3
        self.assertIn(dominioncards.Ambassador, openings)

        # Cost 4
        self.assertIn(dominioncards.Baron, openings)

        # Cost 5
        self.assertIn(dominioncards.Bazaar, openings)


        # Non-openings

        # Requires a potion, can't be an opening
        self.assertNotIn(dominioncards.Alchemist, openings)

        # Too expensive
        self.assertNotIn(dominioncards.Bank, openings)


    def test_initialization(self):
        """Test various ways of initializing card objects
        """
        card = dominioncards.get_card('Estate')
        self.assertEquals(card.singular, 'Estate')


        card = dominioncards.get_card('Card(Estate)')
        self.assertEquals(card.singular, 'Estate')


if __name__ == '__main__':
    unittest.main()
