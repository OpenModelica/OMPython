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

    tempdir = '/tmp'

    _run_OMCPath_checks(tempdir, om)

    del omcp
    del om


@skip_python_older_312
def test_OMCPath_local():
    om = OMPython.OMCSessionZMQ()

    # use different tempdir for Windows and Linux
    if sys.platform.startswith("win"):
        tempdir = 'C:/temp'
    else:
        tempdir = '/tmp'

    _run_OMCPath_checks(tempdir, om)

    del om


@pytest.mark.skip(reason="Not able to run WSL on github")
def test_OMCPath_WSL():
    omcp = OMPython.OMCProcessWSL(
        wsl_omc='omc',
        wsl_user='omc',
        timeout=30.0,
    )
    om = OMPython.OMCSessionZMQ(omc_process=omcp)

    tempdir = '/tmp'

    _run_OMCPath_checks(tempdir, om)

    del omcp
    del om


def _run_OMCPath_checks(tempdir: str, om: OMPython.OMCSessionZMQ):
    p1 = om.omcpath(tempdir).resolve().absolute()
    assert str(p1) == tempdir
    p2 = p1 / '..' / p1.name / 'test.txt'
    assert p2.is_file() is False
    assert p2.write_text('test')
    assert p2.is_file()
    p2 = p2.resolve().absolute()
    assert str(p2) == f"{tempdir}/test.txt"
    assert p2.read_text() == "test"
    assert p2.is_file()
    assert p2.parent.is_dir()
    assert p2.unlink()
    assert p2.is_file() is False
