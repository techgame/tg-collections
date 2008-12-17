#!/usr/bin/env python
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import bisect

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class IntervalList(object):
    def __init__(self, *args):
        self._ranges = []
        if args:
            if len(args) == 2:
                args = [args]
            elif isinstance(args[0], (int, float)):
                args = [(args,)]
            self.update(*args)

    @classmethod
    def fromRangeList(klass, rangeList):
        self = klass()
        self._ranges[:] = [(r1,r0) for r0,r1 in rangeList]
        return self
    def asRangeList(self):
        return [(r0,r1) for r1,r0 in self._ranges]

    def update(self, *args):
        args = list(args)
        while args:
            arg = args.pop(0)
            if isinstance(arg, (int, float)):
                raise ValueError("Cannot pass raw values to update")
            elif isinstance(arg, IntervalList):
                args[0:0] = list(arg.findRange())
            elif isinstance(arg, tuple):
                self.add(*arg)
            else:
                args[0:0] = list(arg)

    def copyRange(self, rstart=None, rstop=None):
        r = self.__class__()
        r.update(self.findRange(rstart, rstop))
        return r
    def copy(self):
        return self.copyRange(None, None)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __repr__(self):
        k = ' '.join(('[%s,%s)'%(r0,r1+1) for r1,r0 in self._ranges))
        return '<%s %s>' % (self.__class__.__name__, k)

    def __len__(self):
        n = 0
        for r1, r0 in self._ranges:
            n += r1-r0+1
        return n

    def __contains__(self, value):
        le = self.entryFor(value)[1]
        return bool(le)

    def __iter__(self):
        return self.iterRange(None, None)

    def iterRange(self, rstart=None, rstop=None):
        for r0, r1 in self.findRange(rstart, rstop):
            for v in xrange(r0, r1):
                yield v

    def iterBlocks(self, rstart=None, rstop=None):
        for r0, r1 in self.findRange(rstart, rstop):
            yield range(r0,r1)

    def findRange(self, rstart=None, rstop=None):
        lst = self._ranges
        if not lst: return 

        if rstart is not None:
            s0 = self.entryFor(rstart)[0]
        else: s0 = slice(0,1)

        if rstop is not None:
            s1 = self.entryFor(rstop)[0]
        else: s1 = slice(-1,len(lst))

        for r1, r0 in lst[s0]:
            if rstart is not None:
                r0 = rstart
            yield (r0,r1+1)

        for r1, r0 in lst[s0.stop:s1.start]:
            yield (r0,r1+1)

        for r1, r0 in lst[s1]:
            if rstop is not None:
                r1 = rstop
            yield (r0,r1+1)

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

    def clear(self):
        del self._ranges[:]

    def add(self, r0, r1=None):
        if r1 is None: 
            r1 = r0+1
        elif r0>r1:
            return

        s0, le0 = self.entryFor(r0-1)
        s1, le1 = self.entryFor(r1)

        if s0.start <= s1.start:
            if le0: r0 = le0[0][1]
            if le1: r1 = le1[-1][0]+1

            lm = [(r1-1, r0)]
            sr = slice(s0.start, s1.stop)
            self._ranges[sr] = self._rfilter(lm)

    def remove(self, r0, r1=None):
        if r1 is None: 
            r1 = r0+1
        elif r0>r1:
            return

        s0, le0 = self.entryFor(r0)
        s1, le1 = self.entryFor(r1)
        if s0.start <= s1.start:
            lm = []
            if le0: lm.append((r0-1, le0[0][1]))
            if le1: lm.append((le1[-1][0], r1))

            sr = slice(s0.start, s1.stop)
            self._ranges[sr] = self._rfilter(lm)

    def removeAfter(self, r0):
        s0, le0 = self.entryFor(r0)
        lm = []
        if le0: lm.append((r0-1, le0[0][1]))
        sr = slice(s0.start, None)
        self._ranges[sr] = self._rfilter(lm)

    def removeBefore(self, r1):
        s1, le1 = self.entryFor(r1)
        lm = []
        if le1: lm.append((le1[-1][0], r1))
        sr = slice(None, s1.stop)
        self._ranges[sr] = self._rfilter(lm)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__=='__main__':
    if 0:
        rl = IntervalList(10, 20)
        rl.remove(15, 25)
        rl.remove(45, 125)
        rl.remove(5, 9)

        map(rl.remove, [10, 13])

        print rl
        print list(rl)

    if 1:
        rl = IntervalList()
        rl.add(0,10)
        rl.add(90,100)
        rl.add(25, 75)
        rl.remove(35, 65)

        print rl
        print
        print 'findRange: [5,95)'
        print list(rl.findRange(5, 95))

        print
        print 'block: [5,95)'
        print list(rl.iterBlocks(5, 95))

        print
        print 'iterRange: [5,95)'
        print list(rl.iterRange(5, 95))

        print 
        print 'iterBlocks:'
        print list(rl.iterBlocks())
        print 
        print 'iter:'
        print list(rl)

    if 1:
        irl = rl.copyRange(7, 93)

        print
        print 'irl:'
        print irl

        print
        print 'irl findRange:'
        print list(irl.findRange())

        print
        print 'irl block:'
        print list(irl.iterBlocks())


