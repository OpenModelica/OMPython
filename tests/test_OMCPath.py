import sys
import OMPython
import pytest

skip_on_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="OpenModelica Docker image is Linux-only; skipping on Windows.",
)

skip_python_older_312 = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="OMCPath only working for Python >= 3.12 (definition of pathlib.PurePath).",
)


@skip_on_windows
@skip_python_older_312
def test_OMCPath_docker():
    omcp = OMPython.OMCProcessDocker(docker="openmodelica/openmodelica:v1.25.0-minimal")
    om = OMPython.OMCSessionZMQ(omc_process=omcp)
    assert om.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    p1 = om.omcpath('/tmp')
    assert str(p1) == "/tmp"
    p2 = p1 / 'test.txt'
    assert str(p2) == "/tmp/test.txt"
    assert p2.write_text('test')
    assert p2.read_text() == "test"
    assert p2.is_file()
    assert p2.parent.is_dir()
    assert p2.unlink()
    assert p2.is_file() is False

    del omcp
    del om


@skip_python_older_312
def test_OMCPath_local():
    om = OMPython.OMCSessionZMQ()

    p1 = om.omcpath('/tmp')
    assert str(p1) == "/tmp"
    p2 = p1 / 'test.txt'
    assert str(p2) == "/tmp/test.txt"
    assert p2.write_text('test')
    assert p2.read_text() == "test"
    assert p2.is_file()
    assert p2.parent.is_dir()
    assert p2.unlink()
    assert p2.is_file() is False

    del om


if __name__ == '__main__':
    test_OMCPath_docker()
    print('DONE')
