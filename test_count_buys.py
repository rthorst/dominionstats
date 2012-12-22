#!/usr/bin/python
# -*- coding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError, e:
    import unittest

import count_buys
import dominioncards
import game
import name_merger
import parse_game

class TestBuyStats(unittest.TestCase):
    def test_merge_buy_stat(self):
        a = count_buys.BuyStat()
        b = count_buys.BuyStat()

        a.available.add_outcome(1)
        b.available.add_outcome(3)
        b.merge(a)
        self.assertEquals(b.available.mean(), 4.0/2.0)


    def test_merge_deck_buy_stats(self):
        a = count_buys.DeckBuyStats()
        b = count_buys.DeckBuyStats()

        a['Estate'].available.add_outcome(2)
        b['Estate'].available.add_outcome(0)

        self.assertEquals(a['Estate'].available.frequency(), 1)
        self.assertEquals(b['Estate'].available.frequency(), 1)
        b.merge(a)
        self.assertEquals(b['Estate'].available.frequency(), 2)


class TestFrontendUsage(unittest.TestCase):
    outpost_game = game.Game(parse_game.parse_game( \
            open('testing/testdata/game-20101015-094051-95e0a59e.html', 'r').read()))

    def test_single_game_overall_stats(self):
        stats = count_buys.DeckBuyStats()
        count_buys.accum_buy_stats([self.outpost_game], stats)

        # Harem bought by both players
        cstats = stats[dominioncards.Harem]
        self.assertEquals(cstats.available.freq, 2)
        self.assertEquals(cstats.any_gained.freq, 2)

        # Salvager only bought by winner
        cstats = stats[dominioncards.Salvager]
        self.assertEquals(cstats.available.freq, 2)
        self.assertEquals(cstats.any_gained.freq, 1)

        # Potion only bought by loser
        cstats = stats[dominioncards.Potion]
        self.assertEquals(cstats.available.freq, 2)
        self.assertEquals(cstats.any_gained.freq, 1)

        # Outpost only bought by loser
        cstats = stats[dominioncards.Outpost]
        self.assertEquals(cstats.available.freq, 2)
        self.assertEquals(cstats.any_gained.freq, 1)

        # Workshop not bought by either player
        cstats = stats[dominioncards.Workshop]
        self.assertEquals(cstats.available.freq, 2)
        self.assertEquals(cstats.any_gained.freq, 0)

        # Chapel not present in this game
        cstats = stats[dominioncards.Chapel]
        self.assertEquals(cstats.available.freq, 0)
        self.assertEquals(cstats.any_gained.freq, 0)


    def test_single_game_winner_stats(self):
        stats = count_buys.DeckBuyStats()
        targ_name = 'moop'
        match_name = lambda g, name: name_merger.norm_name(name) == targ_name
        count_buys.accum_buy_stats([self.outpost_game], stats, match_name)
        count_buys.add_effectiveness(stats, stats)

        # Harem bought by both players
        cstats = stats[dominioncards.Harem]
        self.assertEquals(cstats.available.freq, 1)
        self.assertEquals(cstats.any_gained.freq, 1)
        self.assertEquals(cstats.effect_with().freq, 1)
        self.assertEquals(cstats.effect_without().freq, 0)
        self.assertEquals(cstats.effectiveness_gain.freq, 1)

        # Salvager only bought by winner
        cstats = stats[dominioncards.Salvager]
        self.assertEquals(cstats.available.freq, 1)
        self.assertEquals(cstats.any_gained.freq, 1)
        self.assertEquals(cstats.effect_with().freq, 1)
        self.assertEquals(cstats.effect_without().freq, 0)
        self.assertEquals(cstats.effectiveness_gain.freq, 1)

        # Potion only bought by loser
        cstats = stats[dominioncards.Potion]
        self.assertEquals(cstats.available.freq, 1)
        self.assertEquals(cstats.any_gained.freq, 0)
        self.assertEquals(cstats.effect_with().freq, 0)
        self.assertEquals(cstats.effect_without().freq, 1)
        self.assertEquals(cstats.effectiveness_gain.freq, 0)

        # Outpost only bought by loser
        cstats = stats[dominioncards.Outpost]
        self.assertEquals(cstats.available.freq, 1)
        self.assertEquals(cstats.any_gained.freq, 0)
        self.assertEquals(cstats.effect_with().freq, 0)
        self.assertEquals(cstats.effect_without().freq, 1)
        self.assertEquals(cstats.effectiveness_gain.freq, 0)

        # Workshop not bought by either player
        cstats = stats[dominioncards.Workshop]
        self.assertEquals(cstats.available.freq, 1)
        self.assertEquals(cstats.any_gained.freq, 0)
        self.assertEquals(cstats.effect_with().freq, 0)
        self.assertEquals(cstats.effect_without().freq, 1)
        self.assertEquals(cstats.effectiveness_gain.freq, 0)

        # Chapel not present in this game
        cstats = stats[dominioncards.Chapel]
        self.assertEquals(cstats.available.freq, 0)
        self.assertEquals(cstats.any_gained.freq, 0)
        self.assertEquals(cstats.effect_with().freq, 0)
        self.assertEquals(cstats.effect_without().freq, 0)
        # There is no effectiveness_gain attribute because Chapel didn't exist


if __name__ == '__main__':
    unittest.main()
