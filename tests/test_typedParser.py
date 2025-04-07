from OMPython import OMTypedParser
import unittest

typeCheck = OMTypedParser.parseString


class TypeCheckTester(unittest.TestCase):
    def testNewlineBehaviour(self):
        pass

    def testBoolean(self):
        self.assertEqual(typeCheck('true'), True)
        self.assertEqual(typeCheck('false'), False)

    def testInt(self):
        self.assertEqual(typeCheck('2'), 2)
        self.assertEqual(type(typeCheck('1')), int)
        self.assertEqual(type(typeCheck('123123123123123123232323')), int)
        self.assertEqual(type(typeCheck('9223372036854775808')), int)

    def testFloat(self):
        self.assertEqual(type(typeCheck('1.2e3')), float)

    def testIdent(self):
        self.assertEqual(typeCheck('blabla2'), "blabla2")
        pass

    def testEmpty(self):
        self.assertEqual(typeCheck(''), None)
        pass

    def testStr(self):
        pass

    def testUnStringable(self):
        pass


if __name__ == '__main__':
    unittest.main()
