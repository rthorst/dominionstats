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


class SupplyWinApi(unittest.TestCase):
    def test_parts_of_GET(self):
        swa = frontend.SupplyWinApi()
        query_dict = dict(
            dev="rrenaud",
            targets="Council Room,Embassy,Envoy,Library,Margrave,Menagerie,Nobles,Rabble,Smithy,Torturer",
            interaction="Farming Village,Fishing Village,Hamlet,Mining Village,Native Village,Shanty Town,Village,Walled Village,Worker's Village",
            unconditional="true",
            )

        # query_dict supports the following options.
        # targets: optional comma separated list of card names that want 
        #   stats for, if empty/not given, use all of them
        # interaction: optional comma separated list of cards that we want to
        #   condition the target stats on.
        # nested: optional param, if given present, also get second order
        #   contional stats.
        # unconditional: opt param, if present, also get unconditional stats.
        targets = query_dict.get('targets', '').split(',')
        if sum(len(t) for t in targets) == 0:
            targets = dominioncards.all_cards()

        target_inds = map(swa.str_card_index, targets)
        interaction_tuples = swa.interaction_card_index_tuples(query_dict)
        card_stats = swa.fetch_conditional_stats(target_inds, 
                                                  interaction_tuples)
        json = swa.readable_json_card_stats(card_stats)



if __name__ == '__main__':
    unittest.main()
