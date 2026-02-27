import sys

import pytest

import OMPython

skip_on_windows = pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="OpenModelica Docker image is Linux-only; skipping on Windows.",
)

skip_python_older_312 = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="OMCPath(non-local) only working for Python >= 3.12.",
)


def test_OMCPath_OMCProcessLocal():
    omcs = OMPython.OMCSessionLocal()

    _run_OMCPath_checks(omcs)

    del omcs


@skip_on_windows
@skip_python_older_312
def test_OMCPath_OMCProcessDocker():
    omcs = OMPython.OMCSessionDocker(docker="openmodelica/openmodelica:v1.25.0-minimal")
    assert omcs.sendExpression("getVersion()") == "OpenModelica 1.25.0"

    _run_OMCPath_checks(omcs)

    del omcs


@pytest.mark.skip(reason="Not able to run WSL on github")
@skip_python_older_312
def test_OMCPath_OMCProcessWSL():
    omcs = OMPython.OMCSessionWSL(
        wsl_omc='omc',
        wsl_user='omc',
        timeout=30.0,
    )

    _run_OMCPath_checks(omcs)

    del omcs


def _run_OMCPath_checks(omcs: OMPython.OMCSessionABC):
    p1 = omcs.omcpath_tempdir()
    p2 = p1 / 'test'
    p2.mkdir()
    assert p2.is_dir()
    p3 = p2 / '..' / p2.name / 'test.txt'
    assert p3.is_file() is False
    assert p3.write_text('test')
    assert p3.is_file()
    assert p3.size() > 0
    p3 = p3.resolve().absolute()
    assert str(p3) == str((p2 / 'test.txt').resolve().absolute())
    assert p3.read_text() == "test"
    assert p3.is_file()
    assert p3.parent.is_dir()
    p3.unlink()
    assert p3.is_file() is False


def test_OMCPath_write_file(tmpdir):
    omcs = OMPython.OMCSessionLocal()

    data = "abc # \\t # \" # \\n # xyz"

    p1 = omcs.omcpath_tempdir()
    p2 = p1 / 'test.txt'
    p2.write_text(data=data)

    assert data == p2.read_text()

    del omcs
