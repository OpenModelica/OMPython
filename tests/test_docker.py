import OMPython
import unittest
import tempfile, shutil, os
import pytest

class DockerTester(unittest.TestCase):
  @pytest.mark.skip(reason="This test would fail")
  def testDocker(self):
    om = OMPython.OMCSession(docker="openmodelica/openmodelica:v1.16.1-minimal")
    assert(om.sendExpression("getVersion()") == "OpenModelica 1.16.1")
    omInner = OMPython.OMCSession(dockerContainer=om._dockerCid)
    assert(omInner.sendExpression("getVersion()") == "OpenModelica 1.16.1")
    om2 = OMPython.OMCSession(docker="openmodelica/openmodelica:v1.16.1-minimal", port=11111)
    assert(om2.sendExpression("getVersion()") == "OpenModelica 1.16.1")
    del(om2)
    del(omInner)
    del(om)
if __name__ == '__main__':
    unittest.main()
