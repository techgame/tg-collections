##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
##~ Copyright (C) 2002-2010  TechGame Networks, LLC.              ##
##~                                                               ##
##~ This library is free software; you can redistribute it        ##
##~ and/or modify it under the terms of the MIT style License as  ##
##~ found in the LICENSE file included with this distribution.    ##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import bisect
from itertools import chain

def chain_iterable(iterable):
    return chain(*iterable)
chain_iterable = getattr(chain, 'from_iterable', chain_iterable)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RangeIntervalsBase(object):
    def __init__(self, *args):
        self._ranges = []

        if args:
            # mimic the interface of xrange
            if len(args) in [1,2] and all(isinstance(a, (long, int, float)) for a in args):
                if len(args) == 1:
                    args = [(0, args[0])]
                else:
                    args = [tuple(args)]
            self.update(*args)

    def __repr__(self):
        k = ' '.join(('[%s,%s)'%(r0,r1+1) for r1,r0 in self._ranges))
        return '<%s %s>' % (self.__class__.__name__, k)

    def __cmp__(self, other):
        if not isinstance(other, RangeIntervalsBase):
            other = RangeIntervalsBase(other)
        return cmp(self.ranges(), other.ranges())

    def __getstate__(self):
        return self._ranges
    def __setstate__(self, ranges):
        self._ranges = ranges

    @classmethod
    def fromRanges(klass, ranges):
        self = klass()
        self._ranges[:] = [(r1-1,r0) for r0,r1 in ranges]
        return self
    def ranges(self, rstart=None, rend=None):
        return list(self.findRanges(rstart, rend))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def update(self, *args):
        args = list(args)
        while args:
            arg = args.pop(0)
            if isinstance(arg, (long, int, float)):
                raise ValueError("Cannot pass raw values to update")
            elif isinstance(arg, RangeIntervalsBase):
                args[0:0] = list(arg.findRanges())
            elif (isinstance(arg, (tuple, list)) 
                    and (len(arg) in [1,2]) 
                    and all(isinstance(a, (long, int, float)) for a in arg)):
                self.add(*arg)
            else:
                args[0:0] = list(arg)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def copyRange(self, rstart=None, rstop=None):
        r = self.__class__()
        r.update(self.findRanges(rstart, rstop))
        return r
    def copy(self):
        return self.copyRange(None, None)

    __copy__ = copy # For the copy module
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __len__(self):
        n = len(self._ranges) # account for +1 on each item
        for r1, r0 in self._ranges:
            n += r1-r0
        return n
    def rangeLen(self):
        return [(1+r1-r0) for r1, r0 in self._ranges]

    def __contains__(self, value):
        le = self.entryFor(value)[1]
        return bool(le)

    def __iter__(self):
        return self.iter()
    def iter(self, rstart=None, rstop=None):
        return chain_iterable(xrange(r0, r1) for r0, r1 in self.findRanges(rstart, rstop))

    def blocks(self, rstart=None, rstop=None):
        return list(self.iterBlocks(rstart, rstop))
    def iterBlocks(self, rstart=None, rstop=None):
        for r0, r1 in self.findRanges(rstart, rstop):
            yield range(r0,r1)

    def findRanges(self, rstart=None, rstop=None):
        lst = self._ranges
        if not lst: return 

        if rstart is None:
            rstart = self.minValue()
        s0 = self.entryFor(rstart)[0]

        if rstop is None:
            rstop = self.maxValue()+1
        s1 = self.entryFor(rstop)[0]

        for r1, r0 in lst[s0]:
            if rstart is not None:
                r0 = rstart
            yield (r0,r1+1)

        if s0 == s1: return

        for r1, r0 in lst[s0.stop:s1.start]:
            yield (r0,r1+1)

        for r1, r0 in lst[s1]:
            if rstop is not None:
                r1 = rstop
            else: r1 = r1 + 1
            yield (r0,r1)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def entryFor(self, r):
        lst, i0 = self._bisectFor(r)
        i1 = i0
        if i0 < len(lst):
            eMax, eMin = lst[i0]
            if eMin <= r <= eMax:
                i1 = i0+1
        s = slice(i0, i1)
        return s, lst[s]

    _bisect = staticmethod(bisect.bisect_left)
    def _bisectFor(self, r):
        lst = self._ranges
        return lst, self._bisect(lst, (r,))
    def _rfilter(self, lm):
        return [e for e in lm if e[0] >= e[1]]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def minValue(self):
        for r1,r0 in self._ranges[:1]:
            return r0
    def maxValue(self):
        for r1,r0 in self._ranges[-1:]:
            return r1

    def clear(self):
        del self._ranges[:]

    def add(self, r0, r1=None):
        if r1 is None: r1 = r0+1
        return self._addRange(r0, r1, False)

    def remove(self, r0, r1=None):
        if r1 is None: r1 = r0+1
        return self._removeRange(r0, r1, False)

    def pop(self, r0=None, r1=None):
        if r0 is None: r0 = self.minValue()
        if r1 is None: r1 = r0 + 1
        elif r0>r1: return
        return self._removeRange(r0, r1, True)

    def removeAfter(self, r0):
        return self._removeRange(r0, None, False)
    def popAfter(self, r0):
        return self._removeRange(r0, None, True)

    def removeBefore(self, r1):
        return self._removeRange(None, r1, False)
    def popBefore(self, r1):
        return self._removeRange(None, r1, True)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _addRange(self, r0, r1, pop=True):
        s0, le0 = self.entryFor(r0-1)
        s1, le1 = self.entryFor(r1)

        if s0.start > s1.start: 
            return [] if pop else None

        if le0: r0 = le0[0][1]
        if le1: r1 = le1[-1][0]+1

        lm = [(r1-1, r0)]
        sr = slice(s0.start, s1.stop)
        result = self._ranges[sr] if pop else None
        self._ranges[sr] = self._rfilter(lm)
        return result

    def _removeRange(self, r0=None, r1=None, pop=True):
        s0, le0 = self.entryFor(r0)
        s1, le1 = self.entryFor(r1)

        if s0.start > s1.start: 
            return [] if pop else None

        lm = []
        if le0: lm.append((r0-1, le0[0][1]))
        if le1: lm.append((le1[-1][0], r1))

        sr = slice(s0.start, s1.stop)
        result = self._ranges[sr] if pop else None
        self._ranges[sr] = self._rfilter(lm)
        return result

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RangeIntervals(RangeIntervalsBase):
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Set-like interface
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __or__(self, other):
        """Return the union of two RangeIntervals as a new RangeIntervals.

        (I.e. all elements that are in either RangeIntervals.)
        """
        return self.union(other)

    def union(self, other):
        """Return the union of two RangeIntervals as a new RangeIntervals.

        (I.e. all elements that are in either RangeIntervals.)
        """
        result = self.copy()
        result.union_update(other)
        return result

    def __ior__(self, other):
        """Update a RangeIntervals with the union of itself and another."""
        self.union_update(other)
        return self

    def union_update(self, other):
        """Update a RangeIntervals with the union of itself and another."""
        self.update(other)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Intersection
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __and__(self, other):
        """Return the intersection of two RangeIntervals as a new RangeIntervals.

        (I.e. all elements that are in both RangeIntervals.)
        """
        return self.intersection(other)

    def intersection(self, other):
        """Return the intersection of two RangeIntervals as a new RangeIntervals.

        (I.e. all elements that are in both RangeIntervals.)
        """
        result = self.copy()
        result.intersection_update(other)
        return result

    def __iand__(self, other):
        """Update a RangeIntervals with the intersection of itself and another."""
        self.intersection_update(other)
        return self

    def intersection_update(self, other):
        """Update a RangeIntervals with the intersection of itself and another."""
        if not isinstance(other, RangeIntervalsBase):
            other = RangeIntervalsBase(other)

        pr1 = None
        for r0, r1 in other.findRanges():
            self.remove(pr1, r0)
            pr1 = r1
        self.remove(pr1, None)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Difference
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def  __sub__(self, other):
        """Return the difference of two RangeIntervals as a new RangeIntervals.

        (I.e. all elements that are in this RangeIntervals and not in the other.)
        """
        return self.difference(other)

    def difference(self, other):
        """Return the difference of two RangeIntervals as a new RangeIntervals.

        (I.e. all elements that are in this RangeIntervals and not in the other.)
        """
        result = self.copy()
        result.difference_update(other)
        return result

    def __isub__(self, other):
        """Remove all elements of another RangeIntervals from this RangeIntervals."""
        self.difference_update(other)
        return self

    def difference_update(self, other):
        """Remove all elements of another RangeIntervals from this RangeIntervals."""
        if not isinstance(other, RangeIntervalsBase):
            other = RangeIntervalsBase(other)

        for r0, r1 in other.findRanges():
            self.remove(r0, r1)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Symmetric Difference
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __xor__(self, other):
        """Return the symmetric difference of two RangeIntervals as a new RangeIntervals.

        (I.e. all elements that are in exactly one of the RangeIntervals.)
        """
        return self.symmetric_difference(other)

    def symmetric_difference(self, other):
        """Return the symmetric difference of two RangeIntervals as a new RangeIntervals.

        (I.e. all elements that are in exactly one of the RangeIntervals.)
        """
        result = self.copy()
        result.symmetric_difference_update(other)
        return result

    def __ixor__(self, other):
        """Update a RangeIntervals with the symmetric difference of itself and another."""
        self.symmetric_difference_update(other)
        return self

    def symmetric_difference_update(self, other):
        """Update a RangeIntervals with the symmetric difference of itself and another."""
        if not isinstance(other, RangeIntervalsBase):
            other = RangeIntervalsBase(other)

        for r0, r1 in other.findRanges():
            nsRanges = list(self.findRanges(r0, r1))
            self.add(r0, r1)
            for n0, n1 in nsRanges:
                self.remove(n0, n1)

