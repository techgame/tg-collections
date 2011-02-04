# -*- coding: utf-8 -*- vim: set ts=4 sw=4 expandtab:
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
##~ Copyright (C) 2002-2011  TechGame Networks, LLC.              ##
##~                                                               ##
##~ This library is free software; you can redistribute it        ##
##~ and/or modify it under the terms of the MIT style License as  ##
##~ found in the LICENSE file included with this distribution.    ##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

splitThreshold = 28
sentinal = object()

class HashArrayMappedTrie(object):
    hash = staticmethod(hash)
    null = sentinal
    root = None

    def __init__(self, root=None, null=sentinal):
        self.root = root
        self.null = null

    def __len__(self):
        r = int(self.null is not sentinal)
        if self.root is not None:
            r += len(self.root)
        return r

    def __contains__(self, key):
        return self.get(key, sentinal) is not sentinal

    def __getitem__(self, key):
        r = self.get(key, sentinal)
        if r is sentinal:
            raise LookupError(key)
        else: return r
    def __setitem__(self, key, value):
        self.assoc(key, value)
    def __delitem__(self, key):
        self.without(key)

    def get(self, key, default=None):
        if key is None:
            if self.null is sentinal:
                return default

        root = self.root
        if root is None:
            return False
        return root.find(0, hash(key), key, default)

    def without(self, key):
        if key is None:
            if self.null is not sentinal:
                del self.null

        root = self.root
        if root is not None:
            self.root = root.without(0, hash(key), key)

    def assoc(self, key, value):
        if key is None:
            self.null = value

        root = self.root
        added = []
        if root is None:
            root = BitmapIndexedNode(0, [])
        self.root = root.assoc(0, hash(key), key, value, added)


    def iterkeys(self):
        if self.null is not sentinal:
            yield None
        if self.root is not None:
            for k in self.root.iterkeys():
                yield k
    def itervalues(self):
        if self.null is not sentinal:
            yield self.null
        if self.root is not None:
            for v in self.root.itervalues():
                yield v
    def iteritems(self):
        if self.null is not sentinal:
            yield None, self.null
        if self.root is not None:
            for e in self.root.iteritems():
                yield e

    def iterNodes(self):
        if self.root is not None:
            yield self.root

    def walkNodes(self, end=-1):
        stack = list(self.iterNodes())
        while stack:
            top = stack.pop(end)
            stack.extend(top.iterNodes())
            yield top

HAMT = HashArrayMappedTrie


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class AbstractNode(object):
    def assoc(self, shift, keyHash, key, value, added):
        raise NotImplementedError('Subclass Responsibility: %r' % (self,))
    def without(self, shift, keyHash, key):
        raise NotImplementedError('Subclass Responsibility: %r' % (self,))
    def find(self, shift, keyHash, key, default):
        raise NotImplementedError('Subclass Responsibility: %r' % (self,))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ArrayNode(AbstractNode):
    """These act as branch nodes in the tree"""
    def __init__(self, count, children):
        self.count = count
        self.children = children

    def __repr__(self):
        nodeCount = sum(c is not None for c in self.children)
        return "<%s.%s nodes:%s/32 count:%s>"%(
            self.__class__.__module__, self.__class__.__name__, 
            nodeCount, self.count)

    def iterkeys(self):
        for node in self.children:
            if node is not None:
                for e in node.iterkeys():
                    yield e
    def itervalues(self):
        for node in self.children:
            if node is not None:
                for e in node.itervalues():
                    yield e
    def iteritems(self):
        for node in self.children:
            if node is not None:
                for e in node.iteritems():
                    yield e

    def iterNodes(self):
        return (node for node in self.children if node is not None)

    def assoc(self, shift, keyHash, key, value, added):
        idx = (keyHash >> shift) & 0x1f
        node = self.children[idx]
        children = self.children[:]
        if node is None:
            node = BitmapIndexedNode(0, []).assoc(shift+5, keyHash, key, value, added)
            self.children[idx] = node
            return self

        newNode = node.assoc(shift+5, keyHash, key, value, added)
        if newNode is not node:
            self.children[idx] = newNode
        return self

    def without(self, shift, keyHash, key):
        idx = (keyHash >> shift) & 0x1f
        node = self.children[idx]
        if node is None: return self
        newNode = node.without(shift+5, keyHash, key)
        if newNode is node:
            return self
        elif newNode is None:
            if self.coutn <= 8: # why 8?
                return self._pack(idx)

            self.children[idx] = newNode
            return self
        else:
            self.children[idx] = newNode
            return self

    def find(self, shift, keyHash, key, default):
        idx = (keyHash >> shift) & 0x1f
        node = self.children[idx]
        if node is not None:
            return node.find(shift+5, keyHash, key, default)

    def _pack(self, idx):
        bitmap = 0
        entries = []
        children = self.children
        for i in range(len(children),-1,-1):
            bitmap <<= 1
            if i != idx:
                node = children[i]
                if node is not None:
                    bitmap |= 1
                    entries.append(node)
        return BitmapIndexedNode(bitmap, entries)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class BitmapIndexedNode(AbstractNode):
    """These are the primary leaf nodes in the system"""
    def __init__(self, bitmap, entries):
        self.bitmap = bitmap
        self.entries = entries

    def __repr__(self):
        return "<%s.%s %s>"%(
            self.__class__.__module__, self.__class__.__name__, 
            bin(self.bitmap)[2:].zfill(32))

    def __len__(self):
        return sum(k is not sentinal for k in self.entries[::2])

    def iterkeys(self):
        e = self.entries
        for i in range(0, len(e), 2):
            if e[i] is not sentinal:
                yield e[i]

    def itervalues(self):
        e = self.entries
        for i in range(0, len(e), 2):
            if e[i] is not sentinal:
                yield e[i+1]

    def iteritems(self):
        e = self.entries
        for i in range(0, len(e), 2):
            if e[i] is not sentinal:
                yield (e[i], e[i+1])
            else:
                for kv in e[i+1].iteritems():
                    yield kv

    def iterNodes(self):
        e = self.entries
        for i in range(0, len(e), 2):
            if e[i] is sentinal:
                yield e[i+1]

    @classmethod
    def fromNode(klass, shift, keyHash, node):
        return klass(klass.bitPos(keyHash, shift), [None, node])

    @staticmethod
    def bitPos(keyHash, shift):
        return 1 << ((keyHash>>shift)&0x1f)

    @staticmethod
    def bitCount(i):
        return bin(i).count('1')

    def bitIndex(self, bit):
        i = self.bitmap & (bit-1)
        return bin(i).count('1')

    def _unpack(self, shift, keyHash, key, value, added):
        entries = self.entries
        nodes = [None]*32
        j = 0
        bitmap = self.bitmap
        for i in range(32):
            if (bitmap>>i) & 1:
                eKey = entries[j]
                eValue = entries[j+1]
                if eKey is not None: 
                    nodes[i] = BitmapIndexedNode(0, []).assoc(shift+5, hash(eKey), eKey, eValue, added)
                else: nodes[i] = eValue
                j += 2

        return ArrayNode(j/2, nodes)

    def assoc(self, shift, keyHash, key, value, added):
        bit = self.bitPos(keyHash, shift)
        idx = 2*self.bitIndex(bit)
        bitmap = self.bitmap
        if bitmap & bit:
            eKey = self.entries[idx]
            eValue = self.entries[idx+1]
            if eKey is sentinal:
                node = eValue.assoc(shift+5, keyHash, key, value, added)
                if node is not eValue:
                    self.entries[idx+1] = node
            elif key == eKey:
                if value != eValue:
                    self.entries[idx] = key
                    self.entries[idx+1] = value
            else:
                added.append(True)
                self.entries[idx] = sentinal
                self.entries[idx+1] = createNode(shift+5, eKey, eValue, keyHash, key, value)
            return self

        else:
            bc = self.bitCount(bitmap)
            if bc >= splitThreshold:
                return self._unpack(shift, keyHash, key, value, added)
            else:
                added.append(True)
                self.bitmap = bitmap|bit
                self.entries[idx:idx] = [key, value]
                return self

    def without(self, shift, keyHash, key):
        bit = self.bitPos(keyHash, shift)
        bitmap = self.bitmap
        if not bitmap & bit:
            return self
        idx = 2*self.bitIndex(bit)
        eKey = self.entries[idx]
        eValue = self.entries[idx+1]
        if eKey is sentinal:
            node = eValue.without(shift+5, keyHash, key)
            if node is eValue:
                return self
            if node != None:
                self.entries[idx+1] = node
                return self
            if bitmap == bit:
                return None
            else:
                self.bitmap = bitmap ^ bit
                del self.entries[idx:idx+2]
                return self

        elif eKey == key:
            self.bitmap = bitmap ^ bit
            del self.entries[idx:idx+2]
            return self

        return self

    def find(self, shift, keyHash, key, default):
        bit = self.bitPos(keyHash, shift)
        if not self.bitmap & bit:
            return default
        idx = 2*self.bitIndex(bit)
        eKey = self.entries[idx]
        eValue = self.entries[idx+1]
        if eKey is sentinal:
            return eValue.find(shift+5, keyHash, key, default)
        elif eKey == key:
            return eValue
        else:
            return default

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CollisionNode(AbstractNode):
    def __init__(self, keyHash, entries):
        self.keyHash = keyHash
        self.entries = entries

    def __repr__(self):
        return "<%s.%s %s>"%(
            self.__class__.__module__, self.__class__.__name__, 
            len(self.entries))

    def __len__(self):
        return len(self.entries)/2

    def iterkeys(self):
        return iter(self.entries[0::2])
    def itervalues(self):
        return iter(self.entries[1::2])
    def iteritems(self):
        return iter(zip(self.entries[0::2], self.entries[1::2]))

    def iterNodes(self):
        return iter([])

    def assoc(self, shift, keyHash, key, value, added):
        if (keyHash == self.keyHash):
            idx = self._findIndex(key)
            if idx is not None:
                self.entries[idx+1] = value
                return self

            added.append(True)
            self.entries.extend([key, value])
            return self

        node = BitmapIndexedNode.fromNode(shift, self.keyHash, self)
        return node.assoc(shift, keyHash, key, value, addded)

    def without(self, shift, keyHash, key):
        if (keyHash != self.keyHash):
            return self

        if len(self) > 1:
            del self.entries[idx:idx+2]
            return self
        return None

    def find(self, shift, keyHash, key, default):
        if (keyHash != self.keyHash):
            return default
        idx = self._findIndex(key)
        if idx is None:
            return default
        elif key == self.entries[idx]:
            return self.entries[idx+1]
        else: return default
    
    def _findIndex(self, key):
        idx = self.entries.index(key)
        if idx&1 == 0: # assure it is a key
            return idx

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def createNode(shift, k1, v1, k2Hash, k2, v2):
    k1Hash = hash(k1)
    if k1Hash == k2Hash:
        node = CollisionNode(k1Hash, [k1,v1,k2,v2])
    else:
        node = BitmapIndexedNode(0, [])
        node = node.assoc(shift, k1Hash, k1, v1, [])
        node = node.assoc(shift, k2Hash, k2, v2, [])
    return node

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__=='__main__':
    import os, random
    hashMap = HAMT()

    hashMap['answer'] = 42
    print 'answer' in hashMap
    print hashMap['answer']

    R = 4096
    items = [(str(i)+os.urandom(4).encode('hex'), i**2) for i in xrange(R)]
    hashMap = HAMT()
    for k,v in items:
        hashMap[k] = v

    print
    print 'filled!'
    for node in hashMap.walkNodes(): 
        print node

    if 1:
        for k,v in items[::3]:
            del hashMap[k]

        print
        print 'with holes!'
        for node in hashMap.walkNodes(): 
            print node

    if 0:
        for e in hashMap.iteritems(): 
            print e

