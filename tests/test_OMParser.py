from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from builtins import int

from OMPython import OMParser

import unittest

typeCheck = OMParser.typeCheck


class TypeCheckTester(unittest.TestCase):
    def testNewlineBehaviour(self):
        pass

    def testBoolean(self):
        self.assertEqual(typeCheck('TRUE'), True)
        self.assertEqual(typeCheck('True'), True)
        self.assertEqual(typeCheck('true'), True)
        self.assertEqual(typeCheck('FALSE'), False)
        self.assertEqual(typeCheck('False'), False)
        self.assertEqual(typeCheck('false'), False)

    def testInt(self):
        self.assertEqual(typeCheck('2'), 2)
        self.assertEqual(type(typeCheck('1')), int)
        self.assertEqual(type(typeCheck('123123123123123123232323')), int)
        self.assertEqual(type(typeCheck('9223372036854775808')), int)

    def testFloat(self):
        self.assertEqual(type(typeCheck('1.2e3')), float)

    # def testDict(self):
    #     self.assertEqual(type(typeCheck('{"a": "b"}')), dict)

    def testStr(self):
        pass

    def testUnStringable(self):
        pass


if __name__ == '__main__':
    unittest.main()
