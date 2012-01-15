from primitive_util import ListSlotPrimitiveConversion
from stats import MeanVarStat

class SmallGainStat(ListSlotPrimitiveConversion):
    __slots__ = ('win_given_any_gain', 
                 'win_given_no_gain',
                 'win_weighted_gain')

    def __init__(self):
        self.win_given_any_gain = MeanVarStat()
        self.win_given_no_gain = MeanVarStat()
        self.win_weighted_gain = MeanVarStat()

    def merge(self, other):
        self.win_given_any_gain.merge(other.win_given_any_gain)
        self.win_given_no_gain.merge(other.win_given_no_gain)
        self.win_weighted_gain.merge(other.win_weighted_gain)

    def avail(self):
        return self.win_given_any_gain.freq() + self.win_given_no_gain.freq()

    def __str__(self):
        return 'a <%s> n <%s> w <%s>' % (self.win_given_any_gain,
                                         self.win_given_no_gain,
                                         self.win_weighted_gain)

    def to_readable_primitive_object(self):
        ret = {}
        for name in self.__slots__:
            ret[name] = getattr(self, name).to_primitive_object()
        return ret
