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


# TODO: based on compatibility layer
def test_OMCPath_OMCSessionZMQ():
    om = OMPython.OMCSessionZMQ()

    _run_OMPath_checks(om)
    _run_OMPath_write_file(om)


def test_OMCPath_OMCSessionLocal():
    oms = OMPython.OMCSessionLocal()

    _run_OMPath_checks(oms)
    _run_OMPath_write_file(oms)


@skip_on_windows
@skip_python_older_312
def test_OMCPath_OMCSessionDocker():
    oms = OMPython.OMCSessionDocker(docker="openmodelica/openmodelica:v1.25.0-minimal")
    assert oms.get_version() == "OpenModelica 1.25.0"

    _run_OMPath_checks(oms)
    _run_OMPath_write_file(oms)


@pytest.mark.skip(reason="Not able to run WSL on github")
@skip_python_older_312
def test_OMCPath_OMCSessionWSL():
    oms = OMPython.OMCSessionWSL(
        wsl_omc='omc',
        wsl_user='omc',
        timeout=30.0,
    )

    _run_OMPath_checks(oms)
    _run_OMPath_write_file(oms)


@skip_python_older_312
def test_OMPathLocal_OMSessionRunner():
    oms = OMPython.OMSessionRunner()

    _run_OMPath_checks(oms)
    _run_OMPath_write_file(oms)


@skip_on_windows
@skip_python_older_312
def test_OMPathBash_OMSessionRunner():
    oms = OMPython.OMSessionRunner(
        ompath_runner=OMPython.OMPathRunnerBash,
    )

    _run_OMPath_checks(oms)
    _run_OMPath_write_file(oms)


@skip_on_windows
@skip_python_older_312
def test_OMPathBash_OMSessionRunner_Docker():
    oms_docker = OMPython.OMCSessionDocker(docker="openmodelica/openmodelica:v1.25.0-minimal")
    assert oms_docker.get_version() == "OpenModelica 1.25.0"

    oms = OMPython.OMSessionRunner(
        cmd_prefix=oms_docker.get_cmd_prefix(),
        ompath_runner=OMPython.OMPathRunnerBash,
    )

    _run_OMPath_checks(oms)
    _run_OMPath_write_file(oms)


@pytest.mark.skip(reason="Not able to run WSL on github")
@skip_python_older_312
def test_OMPathBash_OMSessionRunner_WSL():
    oms_docker = OMPython.OMCSessionWSL()
    assert oms_docker.get_version() == "OpenModelica 1.25.0"

    oms = OMPython.OMSessionRunner(
        cmd_prefix=oms_docker.get_cmd_prefix(),
        ompath_runner=OMPython.OMPathRunnerBash,
    )

    _run_OMPath_checks(oms)
    _run_OMPath_write_file(oms)


def _run_OMPath_checks(om: OMPython.OMSessionABC):
    p1 = om.omcpath_tempdir()
    p2 = p1 / 'test'
    p2.mkdir()
    assert p2.is_dir()
    p3 = p2 / '..' / p2.name / 'test.txt'
    assert p3.is_file() is False
    assert p3.write_text('test')
    assert p3.is_file()
    assert p3.size() > 0
    p3 = p3.resolve()
    assert str(p3) == str((p2 / 'test.txt').resolve())
    assert p3.read_text() == "test"
    assert p3.is_file()
    assert p3.parent.is_dir()
    p3.unlink()
    assert p3.is_file() is False


def _run_OMPath_write_file(om: OMPython.OMSessionABC):
    data = "abc # \\t # \" # \\n # xyz"

    p1 = om.omcpath_tempdir()
    p2 = p1 / 'test.txt'
    p2.write_text(data=data)

    assert data == p2.read_text()
