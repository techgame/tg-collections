##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
##~ Copyright (C) 2002-2009  TechGame Networks, LLC.              ##
##~                                                               ##
##~ This library is free software; you can redistribute it        ##
##~ and/or modify it under the terms of the BSD style License as  ##
##~ found in the LICENSE file included with this distribution.    ##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import collections

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_sentinal = object()

class MRUDict(object):
    def __init__(self, count=5):
        if not isinstance(count, list):
            dq = [{} for x in xrange(count)]
        else: dq = count
        self.dq = collections.deque(dq)

    def __missing__(self, key):
        raise KeyError("No entry for key: %r" % (key,))

    def copy(self, slice=None):
        dq = list(self.dq)
        if slice is not None:
            dq = dq[slice]
        return self.__class__(dq)

    def access(self, key):
        """Similar to find, only moves the referenced item to the front of the list"""
        item = self.pop(key, _sentinal)
        if item is _sentinal:
            return self.__missing__(key)

        self.add(key, item)
        return item

    def find(self, key, default=None, incIndex=False):
        dq = self.dq
        for i, grp in enumerate(dq):
            item = grp.get(key, _sentinal)
            if item is not _sentinal:
                if incIndex:
                    return (i, grp, item) 
                else: return item
        if incIndex:
            return (None, None, default)
        else: return default

    def add(self, key, item):
        self.dq[0][key] = item
    def pop(self, key, *args):
        for grp in self.dq:
            item = grp.pop(key, _sentinal)
            if item is not _sentinal:
                return item 

        if args: return args[0]

        raise KeyError("No entry for key: %r" % (key,))
    remove = pop

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def qmerge(self, count=1, merge=True):
        dq = self.dq
        if len(dq) <= 1: 
            return

        r = self.popright(count, merge)
        self.qpushleft(count)
        return r

    def qpushleft(self, count=1):
        dq = self.dq
        for x in xrange(count):
            dq.appendleft({})
    def qpush(self, count=1):
        dq = self.dq
        for x in xrange(count):
            dq.append({})

    def qpopleft(self, count=1, merge=True):
        dq = self.dq
        r = {}
        for x in xrange(count):
            if r: r.update(dq.popleft())
            else: r = dq.popleft()

        if merge:
            if dq: dq[0].update(r)
            else: dq.appendleft(r)
        return r

    def qpop(self, count=1, merge=True):
        dq = self.dq
        r = {}
        for x in xrange(count):
            if r: r.update(dq.pop())
            else: r = dq.pop()

        if merge:
            if dq: dq[-1].update(r)
            else: dq.append(r)
        return r


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Dict-like interface
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __len__(self):
        return sum((len(e) for e in self.dq), 0)
    def __iter__(self):
        for grp in self.dq:
            for e in grp:
                yield e

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.copy(key)
        return self.access(key)
    def __setitem__(self, key, value):
        self.add(key, value)
    def __delitem__(self, key, value):
        self.pop(key)

    def update(self, *args, **kw):
        return self.dq[0].update(*args, **kw)

    def get(self, key, default):
        return self.find(key, default, False)

    def keys(self):
        r = []
        for grp in self.dq:
            r.extend(grp.keys())
        return r
    def iterkeys(self):
        for grp in self.dq:
            for e in grp.iterkeys():
                yield e

    def values(self):
        r = []
        for grp in self.dq:
            r.extend(grp.values())
        return r
    def itervalues(self):
        for grp in self.dq:
            for e in grp.itervalues():
                yield e

    def items(self):
        r = []
        for grp in self.dq:
            r.extend(grp.items())
        return r
    def iteritems(self):
        for grp in self.dq:
            for e in grp.iteritems():
                yield e

