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

    def __init__(self, maxlen=5, PhaseDict=None):
        self._initPhases(maxlen, PhaseDict)

    def _initPhases(self, maxlen=5, PhaseDict=None):
        # phases is a deque with the oldest on the left
        if PhaseDict is not None:
            self.PhaseDict = PhaseDict
        self._phases = deque(maxlen=maxlen)
        self.pushPhase()

    def pushPhase(self):
        top = self.PhaseDict()
        self._phases.append(top)
        self.top = top
        return top
    def popPhase(self):
        return self._phases.popleft()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Mapping API
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
        return self.top.update(*args, **kw)


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
        self.top[key] = value
    def __delitem__(self, key):
        for p in self._phases:
            p.pop(key, None)

    def get(self, key, default=None):
        NA = self._notAvailable
        res = self.top.get(key, NA)
        if res is not NA:
            return res

        self.faultKey(key)
        return default

    def pop(self, key, default=None):
        p = self.faultKey(key)
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
        p = self._findPhase(key)
        if p is None:
            return default
        res = p.pop(key)
        self.top[key] = res
        return res

