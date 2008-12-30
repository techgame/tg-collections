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

class MRUQueue(object):
    def __init__(self, count=5):
        self.dq = collections.deque()
        self.qpush(count)

    def __getitem__(self, key):
        return self.access(key)

    def __missing__(self, key):
        raise KeyError("Could not find entry for key: %r" % (key,))

    def access(self, key):
        """Similar to find, only moves the referenced item to the front of the list"""
        sentinal = object()
        item = self.popitem(key, sentinal)
        if item is sentinal:
            return self.__missing__(key)

        self.additem(key, item)
        return item

    def find(self, key, incIndex=False):
        sentinal = object()
        dq = self.dq
        for i, grp in enumerate(dq):
            item = grp.get(key, sentinal)
            if item is not sentinal:
                if incIndex:
                    return (i, grp, item) 
                else: return item
        else: return None

    def additem(self, key, item):
        self.dq[0][key] = item
    def popitem(self, key, default=None):
        sentinal = object()
        for grp in self.dq:
            item = grp.pop(key, sentinal)
            if item is not sentinal:
                return item 
        else: 
            return default

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def qrotate(self, count=1, merge=True):
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


