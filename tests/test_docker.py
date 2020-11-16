import OMPython
import unittest
import tempfile, shutil, os

class DockerTester(unittest.TestCase):
  def testDocker(self):
    om = OMPython.OMCSessionZMQ(docker="openmodelica/openmodelica:v1.16.0-minimal")
    assert(om.sendExpression("getVersion()") == "OpenModelica 1.16.0")
    omInner = OMPython.OMCSessionZMQ(dockerContainer=om._dockerCid)
    assert(omInner.sendExpression("getVersion()") == "OpenModelica 1.16.0")
    del(omInner)
    del(om)
if __name__ == '__main__':
    unittest.main()
