#!/usr/bin/python
# -*- coding: utf-8 -*-

""" The stats mdoule contains two objects for tracking distributions.

The MeanVarStat keeps a running total of frequence, mean, and variance of
a random variable.

DiffStat supports finding the difference between two MeanVarStat objects.
"""

import math

import primitive_util
import mergeable

class MeanVarStat(primitive_util.ListSlotPrimitiveConversion, 
                  mergeable.MergeableObject):
    __slots__ = ('freq', 'sum', 'sum_sq')
    
    def __init__(self, prior_freq=0, prior_sum=0, prior_sum_sq=0):
        self.freq = prior_freq
        self.sum = prior_sum
        self.sum_sq = prior_sum_sq

    def add_outcome(self, val):
        self.freq += 1
        self.sum += val
        self.sum_sq += val * val

    def add_many_outcomes(self, val, freq):
        self.freq += freq
        self.sum += val * freq
        self.sum_sq += val * val * freq

    def frequency(self):
        return self.freq

    def mean(self):
        return self.sum / self.freq

    def variance(self):
        if self.freq <= 1:
            return 1e10
        return (((self.sum_sq) - ((self.sum) ** 2) / (self.freq)) /
                (self.freq - 1))

    def std_dev(self):
        return self.variance() ** .5
 
    def sample_std_dev(self):
        return (self.variance() / (self.freq or 1)) ** .5

    def __add__(self, o):
        ret = MeanVarStat()
        ret.freq = self.freq + o.freq
        ret.sum = self.sum + o.sum
        ret.sum_sq = self.sum_sq + o.sum_sq
        return ret
    
    def __sub__(self, o):
        ret = MeanVarStat()
        ret.freq = self.freq - o.freq
        ret.sum = self.sum - o.sum
        ret.sum_sq = self.sum_sq - o.sum_sq
        return ret

    def mean_diff(self, o):
        return DiffStat(self, o)

    def render_interval(self, factor=2, sig_digits=2):
        if self.sample_std_dev() >= 10000:
            return u'-'
        return u'%.2f ± %.2f' % (self.mean(), factor * self.sample_std_dev())

    def __eq__(self, o):
        assert type(o) == MeanVarStat
        return (self.freq == o.freq and 
                self.sum == o.sum and
                self.sum_sq == o.sum_sq)

    def merge(self, obj):
        self.freq += obj.freq
        self.sum += obj.sum
        self.sum_sq += obj.sum_sq

    def __str__(self):
        return '%s, %s, %s' % (self.freq, self.sum, self.sum_sq)

class DiffStat(object):
    """
    Statistics about the difference in means of two distributions.
    """
    def __init__(self, mvs1, mvs2):
        self.mvs1 = mvs1
        self.mvs2 = mvs2

    @property
    def freq(self):
        return self.mvs1.freq

    def render_interval(self, factor=2, sig_digits=2):
        if self.sample_std_dev() >= 10000:
            return u'-'
        return u'%.2f ± %.2f' % (self.mean(), factor * self.sample_std_dev())
        
    def render_std_devs(self):
        if not self.freq:
            return u'-'
        return u'%.2f' % (self.mean() / self.sample_std_dev())

    def mean(self):
        return self.mvs1.mean() - self.mvs2.mean()

    def sample_std_dev(self):
        return math.hypot(self.mvs1.sample_std_dev(), 
                          self.mvs2.sample_std_dev())

    def mean_diff(self, o):
        return DiffStat(self, o)

