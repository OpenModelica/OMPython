import OMPython
import pytest


@pytest.mark.skip(reason="This test would fail")
def test_docker():
    om = OMPython.OMCSessionZMQ(docker="openmodelica/openmodelica:v1.16.1-minimal")
    assert om.sendExpression("getVersion()") == "OpenModelica 1.16.1"
    omInner = OMPython.OMCSessionZMQ(dockerContainer=om._dockerCid)
    assert omInner.sendExpression("getVersion()") == "OpenModelica 1.16.1"
    om2 = OMPython.OMCSessionZMQ(docker="openmodelica/openmodelica:v1.16.1-minimal", port=11111)
    assert om2.sendExpression("getVersion()") == "OpenModelica 1.16.1"
    del om2
    del omInner
    del om
