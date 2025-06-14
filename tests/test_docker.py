import OMPython
import pytest


@pytest.mark.skip(reason="This test would fail")
def test_docker():
    omcp = OMPython.OMCProcessDocker(docker="openmodelica/openmodelica:v1.16.1-minimal")
    om = OMPython.OMCSessionZMQ(omc_process=omcp)
    assert om.sendExpression("getVersion()") == "OpenModelica 1.16.1"

    omcpInner = OMPython.OMCProcessDockerContainer(dockerContainer=omcp.get_docker_container_id())
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
