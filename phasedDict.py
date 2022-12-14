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

import itertools
from collections import deque

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PhasedDict(object):
    PhaseDict = dict

    def __init__(self, phaseMaxLen=5, PhaseDict=None):
        self._initPhases(phaseMaxLen, PhaseDict)

    _phases = None
    def _initPhases(self, phaseMaxLen=5, PhaseDict=None):
        # phases is a deque with the oldest on the left
        if PhaseDict is not None:
            self.PhaseDict = PhaseDict

        self.phaseMaxLen = phaseMaxLen
        self.pushPhase()

    def pushPhase(self):
        top = self.PhaseDict()
        self._phases.append(top)
        return top
    def popPhase(self):
        return self._phases.popleft()

    def getPhaseMaxLen(self):
        return self._phaseMaxLen
    def setPhaseMaxLen(self, phaseMaxLen):
        self._phaseMaxLen = phaseMaxLen
        self._phases = deque(self._phases or [], phaseMaxLen)
    phaseMaxLen = property(getPhaseMaxLen, setPhaseMaxLen)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Mapping API
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _topPhase(self):
        return self._phases[-1]
    _top = property(_topPhase)

    def clear(self):
        self._phases.clear()
        self.pushPhase()

    def copy(self):
        """Iterpreted as a dictionary copy, not a PhasedDict copy"""
        r = dict()
        for p in self._phases:
            r.update(p)
        return r

    def update(self, *args, **kw):
        self._top.update(*args, **kw)
        self.filterKeyDuplicates()

    def __len__(self):
        return sum(len(p) for p in self._phases)
    def __iter__(self):
        return self.iterkeys()
    def __contains__(self, key):
        return self.get(key, None) is not None
    def has_key(self, key):
        return self.get(key, None) is not None
    def setdefault(self, key, default):
        NA = self._notAvailable
        res = self.get(key, NA)
        if res is NA:
            self[key] = res = default
        return res

    def keys(self): 
        return list(self.iterkeys())
    def iterkeys(self):
        r = (p.iterkeys() for p in self._phases)
        return itertools.chain(*r)

    def values(self): 
        return list(self.itervalues())
    def itervalues(self):
        r = (p.itervalues() for p in self._phases)
        return itertools.chain(*r)

    def items(self): 
        return list(self.iteritems())
    def iteritems(self):
        r = (p.iteritems() for p in self._phases)
        return itertools.chain(*r)

    _notAvailable = object() # sentinal meaning "not available"
    def __getitem__(self, key):
        NA = self._notAvailable
        res = self.get(key, NA)
        if res is NA:
            res = self.__missing__(key)
        return res
    def __setitem__(self, key, value):
        self._top[key] = value
        iterPhases = reversed(self._phases)
        iterPhases.next() # skip top
        for p in iterPhases:
            p.pop(key, None)
    def __delitem__(self, key):
        for p in self._phases:
            p.pop(key, None)

    def __missing__(self, key):
        raise KeyError(key)

    def get(self, key, default=None):
        NA = self._notAvailable
        res = self._top.get(key, NA)
        if res is not NA:
            return res

        self.faultKey(key)
        return default

    def pop(self, key, default=None):
        p = self.findPhase(key)
        if p is None:
            return default
        return p.pop(key)

    def popitem(self):
        for p in self._phases:
            if len(p): break
        return p.popitem()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def findPhase(self, key):
        for p in self._phases:
            if key in p:
                return p
        else: return None

    def faultKey(self, key, default=None):
        p = self.findPhase(key)
        if p is None:
            return default
        res = p.pop(key)
        self._top[key] = res
        return res

    def filterKeyDuplicates(self):
        allKeys = set()
        for p in reversed(self._phases):
            pk = set(p.keys())
            for k in (allKeys & pk):
                del p[k]
            allKeys.update(pk)

