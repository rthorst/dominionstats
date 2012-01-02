#!/usr/bin/python

import unittest
import stats

class RandomVariableStat(unittest.TestCase):
    def test_simple(self):
        d = stats.MeanVarStat()
        d.add_outcome(2.)                  # freq = 1, sum = 2, sum_sq = 4
        d.add_outcome(3.)                  # freq = 2, sum = 5, sum_sq = 13
        self.assertEquals(d.frequency(), 2)
        self.assertEquals(d.mean(), 2.5)
        self.assertEquals(d.variance(), (13 - 25. / 2) / 1) 

    def test_merge(self):
        a = stats.MeanVarStat()
        b = stats.MeanVarStat()

        a.add_outcome(1)
        b.add_outcome(1)
        
        b.merge(a)

        self.assertEquals(b.frequency(), 2)


if __name__ == '__main__':
    unittest.main()
