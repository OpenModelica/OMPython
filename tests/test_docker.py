import OMPython
import unittest
import pytest


class DockerTester(unittest.TestCase):
    @pytest.mark.skip(reason="This test would fail")
    def testDocker(self):
        omcp = OMPython.OMCProcessDocker(docker="openmodelica/openmodelica:v1.16.1-minimal")
        om = OMPython.OMCSessionZMQ(omc_process=omcp)
        assert om.sendExpression("getVersion()") == "OpenModelica 1.16.1"

        omcpInner = OMPython.OMCProcessDocker(dockerContainer=om._dockerCid)
        omInner = OMPython.OMCSessionZMQ(omc_process=omcpInner)
        assert omInner.sendExpression("getVersion()") == "OpenModelica 1.16.1"

        omcp2 = OMPython.OMCProcessDocker(docker="openmodelica/openmodelica:v1.16.1-minimal", port=11111)
        om2 = OMPython.OMCSessionZMQ(omc_process=omcp2)
        assert om2.sendExpression("getVersion()") == "OpenModelica 1.16.1"

        del omcp2
        del om2

        del omcpInner
        del omInner

        del omcp
        del om


if __name__ == '__main__':
    unittest.main()
