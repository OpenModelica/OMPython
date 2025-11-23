import sys
import pytest
import OMPython

skip_on_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="OpenModelica Docker image is Linux-only; skipping on Windows.",
)


@skip_on_windows
def test_docker():
    omcs = OMPython.OMCSessionDocker(docker="openmodelica/openmodelica:v1.25.0-minimal")
    assert omcs.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    omcsInner = OMPython.OMCSessionDockerContainer(dockerContainer=omcs.get_docker_container_id())
    assert omcsInner.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    omcs2 = OMPython.OMCSessionDocker(docker="openmodelica/openmodelica:v1.25.0-minimal", port=11111)
    assert omcs2.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    del omcs2

    del omcsInner

    del omcs
