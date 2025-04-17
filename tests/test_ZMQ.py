import OMPython
import unittest
import tempfile
import shutil
import os


class ZMQTester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ZMQTester, self).__init__(*args, **kwargs)
        self.simpleModel = """model M
  Real r = time;
end M;"""
        self.tmp = tempfile.mkdtemp(prefix='tmpOMPython.tests')
        self.origDir = os.getcwd()
        os.chdir(self.tmp)
        self.om = OMPython.OMCSessionZMQ()
        os.chdir(self.origDir)

    def __del__(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        del self.om

    def clean(self):
        del self.om
        self.om = None

    def testHelloWorld(self):
        self.assertEqual("HelloWorld!", self.om.sendExpression('"HelloWorld!"'))
        self.clean()

    def testTranslate(self):
        self.assertEqual(("M",), self.om.sendExpression(self.simpleModel))
        self.assertEqual(True, self.om.sendExpression('translateModel(M)'))
        self.clean()

    def testSimulate(self):
        self.assertEqual(True, self.om.sendExpression('loadString("%s")' % self.simpleModel))
        self.om.sendExpression('res:=simulate(M, stopTime=2.0)')
        self.assertNotEqual("", self.om.sendExpression('res.resultFile'))
        self.clean()

    def test_execute(self):
        self.assertEqual('"HelloWorld!"\n', self.om.execute('"HelloWorld!"'))
        self.assertEqual('"HelloWorld!"\n', self.om.sendExpression('"HelloWorld!"', parsed=False))
        self.assertEqual('HelloWorld!', self.om.sendExpression('"HelloWorld!"', parsed=True))
        self.clean()


if __name__ == '__main__':
    unittest.main()
