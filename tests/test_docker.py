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
    omversion = omcs.sendExpression("getVersion()")
    assert isinstance(omversion, str) and omversion.startswith("OpenModelica")

    omcsInner = OMPython.OMCSessionDockerContainer(dockerContainer=omcs.get_docker_container_id())
    omversion = omcsInner.sendExpression("getVersion()")
    assert isinstance(omversion, str) and omversion.startswith("OpenModelica")

    omcs2 = OMPython.OMCSessionDocker(docker="openmodelica/openmodelica:v1.25.0-minimal", port=11111)
    omversion = omcs2.sendExpression("getVersion()")
    assert isinstance(omversion, str) and omversion.startswith("OpenModelica")

    del omcs2

    del omcsInner

    del omcs
