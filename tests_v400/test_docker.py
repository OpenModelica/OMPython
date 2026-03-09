import sys
import pytest
import OMPython

skip_on_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="OpenModelica Docker image is Linux-only; skipping on Windows.",
)


@skip_on_windows
def test_docker():
    omcp = OMPython.OMCProcessDocker(docker="openmodelica/openmodelica:v1.25.0-minimal")
    om = OMPython.OMCSessionZMQ(omc_process=omcp)
    assert om.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    omcpInner = OMPython.OMCProcessDockerContainer(dockerContainer=omcp.get_docker_container_id())
    omInner = OMPython.OMCSessionZMQ(omc_process=omcpInner)
    assert omInner.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    omcp2 = OMPython.OMCProcessDocker(docker="openmodelica/openmodelica:v1.25.0-minimal", port=11111)
    om2 = OMPython.OMCSessionZMQ(omc_process=omcp2)
    assert om2.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    del omcp2
    del om2

    del omcpInner
    del omInner

    del omcp
    del om
