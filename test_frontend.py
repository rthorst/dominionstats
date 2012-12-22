#!/usr/bin/python

import unittest
import frontend

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


if __name__ == '__main__':
    unittest.main()
