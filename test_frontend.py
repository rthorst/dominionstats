#!/usr/bin/python

import unittest
import frontend

# TODO: This can't be tested until we split the data retrieval
# function out of GET... I had this in a local copy at one point when
# I created this test, but I apparently didn't check it in, so marking
# this as "skip" for now.

@unittest.skip("Needs implementation")
class PopularBuyPage(unittest.TestCase):
    def test_retrieve_data(self):
        page = frontend.PopularBuyPage()
        stats, player_buy_summary = page.retrieve_data()
        # TODO: Do some actual checking that this worked. For now, all
        # we know is that we didn't throw an exception.
        self.assertEquals(1, 1) 

        stats, player_buy_summary = page.retrieve_data('Larry')
        # TODO: Do some actual checking that this worked. For now, all
        # we know is that we didn't throw an exception.
        self.assertEquals(1, 1) 


class SupplyWinApi(unittest.TestCase):
    def test_retrieve_1_by_1(self):
        """Simple test with 1 target, 1 interaction, and unconditional stats"""
        swa = frontend.SupplyWinApi()
        query_dict = dict(
            dev="rrenaud",
            targets="Council Room",
            interaction="Farming Village",
            unconditional="true",
            )

        card_stats = swa.retrieve_data(query_dict)

        self.assertEquals(len(card_stats), 2)

        self.assertEquals(card_stats[0]['card_name'], 'Council Room')
        self.assertEquals(card_stats[0]['condition'][0], 'Farming Village')

        self.assertEquals(card_stats[1]['card_name'], 'Council Room')
        self.assertEquals(len(card_stats[1]['condition']), 0)

        json = swa.readable_json_card_stats(card_stats)
        self.assertEquals(json[0:14], '[{"card_name":')

    def test_retrieve_1_by_all(self):
        """Simple test with 1 target, empty interaction list, and unconditional stats"""
        swa = frontend.SupplyWinApi()
        query_dict = dict(
            dev="rrenaud",
            targets="Council Room",
            interaction="",
            unconditional="true",
            )

        card_stats = swa.retrieve_data(query_dict)

        self.assertEquals(len(card_stats), 1)

        self.assertEquals(card_stats[0]['card_name'], 'Council Room')
        self.assertEquals(len(card_stats[0]['condition']), 0)

        json = swa.readable_json_card_stats(card_stats)
        self.assertEquals(json[0:14], '[{"card_name":')

    def test_retrieve_all_by_bank(self):
        """Simple test with no target (def to all), Bank interaction, and unconditional stats"""
        swa = frontend.SupplyWinApi()
        query_dict = dict(
            dev="rrenaud",
            targets="",
            interaction="Bank",
            unconditional="true",
            )

        card_stats = swa.retrieve_data(query_dict)

        # Gets 288 entries back, because one for each of the 144
        # cards, plus the unconditioned version of each
        self.assertEquals(len(card_stats), 288)

        self.assertEquals(card_stats[0]['card_name'], 'Adventurer')

        json = swa.readable_json_card_stats(card_stats)
        self.assertEquals(json[0:14], '[{"card_name":')

    def test_retrieve_all_by_bag_of_gold(self):
        """Simple test with no target (def to all), Bag of Gold interaction, and unconditional stats.

        Note that Bag of Gold appears in the Cornucopia deck, which
        was published in 2011. The test database needs games where
        this card has been played before these tests will pass."""
        swa = frontend.SupplyWinApi()
        query_dict = dict(
            dev="rrenaud",
            targets="",
            interaction="Bag of Gold",
            unconditional="true",
            )

        card_stats = swa.retrieve_data(query_dict)

        # Gets 288 entries back, because one for each of the 144
        # cards, plus the unconditioned version of each
        self.assertEquals(len(card_stats), 288)

        self.assertEquals(card_stats[0]['card_name'], 'Adventurer')

        json = swa.readable_json_card_stats(card_stats)
        self.assertEquals(json[0:14], '[{"card_name":')


if __name__ == '__main__':
    unittest.main()
