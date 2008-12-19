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

import unittest
from TG.collections.rangeIntervals import RangeIntervals

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestRangeListBase(unittest.TestCase):
    def testRemoveOutliers(self):
        rl = RangeIntervals(10, 20)
        self.assertEqual(list(rl), range(10,20))
        self.assertEqual(bool(rl), True)
        self.assertEqual(len(rl), 10)

        rl.remove(15, 25)
        self.assertEqual(list(rl), range(10,15))

        rl.remove(45, 125)
        self.assertEqual(list(rl), range(10,15))

        rl.remove(5, 9)
        self.assertEqual(list(rl), range(10,15))
        self.assertEqual(bool(rl), True)
        self.assertEqual(len(rl), 5)

        rl.remove(10)
        self.assertEqual(list(rl), range(11,15))
        rl.remove(13)
        self.assertEqual(list(rl), [11,12,14])
        rl.remove(14)
        self.assertEqual(list(rl), [11,12])
        rl.remove(12)
        self.assertEqual(list(rl), [11])
        self.assertEqual(bool(rl), True)
        self.assertEqual(len(rl), 1)

        rl.remove(11)
        self.assertEqual(list(rl), [])
        self.assertEqual(bool(rl), False)
        self.assertEqual(len(rl), 0)

    def testCopyRange(self):
        rl = RangeIntervals()
        rl.add(0,10)
        rl.add(90,100)
        rl.add(25, 75)
        rl.remove(35, 65)

        irl = rl.copyRange(7, 93)

        self.assertNotEqual(list(rl), list(irl))
        self.assertNotEqual(rl.ranges(), irl.ranges())
        self.assertEqual(rl.ranges()[1:-1], irl.ranges()[1:-1])

        self.assertEqual(rl.ranges()[0], (0,10))
        self.assertEqual(irl.ranges()[0], (7,10))

        self.assertEqual(rl.ranges()[-1], (90,100))
        self.assertEqual(irl.ranges()[-1], (90, 93))

        self.assertEqual(rl.blocks(), [range(*a) for a in rl.ranges()])
        self.assertEqual(irl.blocks(), [range(*a) for a in irl.ranges()])

    def testIterRanges(self):
        rl = RangeIntervals()
        rl.add(0,10)
        rl.add(90,100)
        rl.add(25, 75)
        rl.remove(35, 65)

        self.assertEqual(rl.ranges(5,95), [(5, 10), (25, 35), (65, 75), (90, 95)])
        self.assertEqual(rl.ranges(30,70), [(30, 35), (65, 70)])
        self.assertEqual(rl.ranges(30,None), [(30, 35), (65, 75), (90,100)])
        self.assertEqual(rl.ranges(None,70), [(0,10), (25, 35), (65, 70)])

    def testRemove(self):
        rl = RangeIntervals(10, 20)
        self.assertEqual(rl.ranges(), [(10, 20)])
        self.assertEqual(list(rl), range(10, 20))

        rl.remove(13,17)
        self.assertEqual(rl.ranges(), [(10,13), (17, 20)])
        self.assertEqual(list(rl), range(10, 13)+range(17,20))

        self.assertEqual(rl, rl - (13, 17))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestRangeListSets(unittest.TestCase):
    rl0 = RangeIntervals([(0,10), (20, 30)])
    rl1 = RangeIntervals([(-3, 2), (8,12), (18, 22), (28, 34)])

    def testUnion(self):
        rl0 = self.rl0.copy(); rl1 = self.rl1.copy()

        result = (rl0 | rl1)
        self.assertEqual(result.ranges(), [(-3, 12), (18, 34)])
        self.assertEqual(rl0.ranges(), self.rl0.ranges())

        rl0 |= rl1
        self.assertEqual(rl0.ranges(), result.ranges())
        self.assertNotEqual(rl0.ranges(), self.rl0.ranges())

    def testIntersection(self):
        rl0 = self.rl0.copy(); rl1 = self.rl1.copy()

        result = (rl0 & rl1)
        self.assertEqual(result.ranges(), [(0, 2), (8,10), (20,22), (28, 30)])
        self.assertEqual(rl0.ranges(), self.rl0.ranges())

        rl0 &= rl1
        self.assertEqual(rl0.ranges(), result.ranges())
        self.assertNotEqual(rl0.ranges(), self.rl0.ranges())

    def testDifference(self):
        rl0 = self.rl0.copy(); rl1 = self.rl1.copy()

        result = (rl0 - rl1)
        self.assertEqual(result.ranges(), [(2, 8), (22, 28)])
        self.assertEqual(rl0.ranges(), self.rl0.ranges())

        rl0 -= rl1
        self.assertEqual(rl0.ranges(), result.ranges())
        self.assertNotEqual(rl0.ranges(), self.rl0.ranges())

    def testSymmetricDifference(self):
        rl0 = self.rl0.copy(); rl1 = self.rl1.copy()

        result = (rl0 ^ rl1)
        self.assertEqual(result.ranges(), [(-3, 0), (2, 8), (10, 12), (18, 20), (22, 28), (30, 34)])
        crosscheck = (rl0 | rl1) - (rl0 & rl1)
        self.assertEqual(result.ranges(), crosscheck.ranges())

        self.assertEqual(rl0.ranges(), self.rl0.ranges())

        rl0 ^= rl1
        self.assertEqual(rl0.ranges(), result.ranges())
        self.assertNotEqual(rl0.ranges(), self.rl0.ranges())

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Unittest Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__=='__main__':
    unittest.main()

