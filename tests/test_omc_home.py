"""
Where OMCSessionLocal looks for OpenModelica: omhome, version, OPENMODELICAHOME, OPENMODELICAHOME_<version>, PATH.
No omc is started, the installations are directories with an empty bin/omc.
"""

import pathlib

import pytest

import OMPython
from OMPython.om_session_omc import omc_home_versions, omc_version_env_name

RELEASE = "OPENMODELICAHOME_1_27_0"
MAINTENANCE = "OPENMODELICAHOME_1_27_0_5_g0123456789"
NIGHTLY_OLD = "OPENMODELICAHOME_1_28_0_dev_900_gaaaaaaaaaa"
NIGHTLY = "OPENMODELICAHOME_1_28_0_dev_1962_g6e348e217c"


def omc_home_get(environ, omhome=None, version=None):
    # staticmethod, no session is created
    return OMPython.OMCSessionLocal._omc_home_get(omhome=omhome, version=version, environ=environ)


def install(tmp_path: pathlib.Path, name: str) -> str:
    home = tmp_path / name
    (home / "bin").mkdir(parents=True)
    (home / "bin" / "omc").touch()
    return str(home)


@pytest.fixture
def environ(tmp_path):
    return {name: install(tmp_path, name) for name in (NIGHTLY_OLD, RELEASE, NIGHTLY, MAINTENANCE)}


def test_version_env_name():
    assert omc_version_env_name("1.27.0") == RELEASE
    assert omc_version_env_name("v1.27.0") == RELEASE
    assert omc_version_env_name("1.28.0-dev-1962-g6e348e217c") == NIGHTLY
    assert omc_version_env_name("1.27") == "OPENMODELICAHOME_1_27"


def test_versions_newest_first(environ, tmp_path):
    environ["OPENMODELICAHOME"] = environ[RELEASE]
    environ["OPENMODELICAHOME_1_30_0"] = str(tmp_path / "uninstalled")
    environ["PATH"] = "/usr/bin"
    assert list(omc_home_versions(environ=environ)) == [NIGHTLY, NIGHTLY_OLD, MAINTENANCE, RELEASE]


def test_versions_number_not_string_order(tmp_path):
    names = ["OPENMODELICAHOME_1_9_0", "OPENMODELICAHOME_1_27_0", "OPENMODELICAHOME_1_100_0"]
    environ = {name: install(tmp_path, name) for name in names}
    assert list(omc_home_versions(environ=environ)) == list(reversed(names))


def test_omhome_wins(environ):
    assert omc_home_get(environ, omhome="/some/where", version="1.27.0") == pathlib.Path("/some/where")


def test_version(environ):
    assert omc_home_get(environ, version="1.27.0") == pathlib.Path(environ[RELEASE])
    assert omc_home_get(environ, version="v1.27.0") == pathlib.Path(environ[RELEASE])
    assert omc_home_get(environ, version="1.28.0-dev-900-gaaaaaaaaaa") == pathlib.Path(environ[NIGHTLY_OLD])


def test_version_start(environ):
    # the newest one that starts with the given version
    assert omc_home_get(environ, version="1.28") == pathlib.Path(environ[NIGHTLY])
    assert omc_home_get(environ, version="1.28.0-dev") == pathlib.Path(environ[NIGHTLY])
    assert omc_home_get(environ, version="1") == pathlib.Path(environ[NIGHTLY])
    # the given version is used if it is installed, 1.27.0-5-g0123456789 is not picked
    assert omc_home_get(environ, version="1.27") == pathlib.Path(environ[MAINTENANCE])
    assert omc_home_get(environ, version="1.27.0") == pathlib.Path(environ[RELEASE])


def test_version_start_is_not_a_string_prefix(environ):
    # 1.2 is not 1.27
    with pytest.raises(OMPython.OMSessionException, match="OPENMODELICAHOME_1_2"):
        omc_home_get(environ, version="1.2")


def test_version_not_installed(environ):
    with pytest.raises(OMPython.OMSessionException) as excinfo:
        omc_home_get(environ, version="1.26.0")
    assert "OPENMODELICAHOME_1_26_0" in str(excinfo.value)
    # the installed versions are listed
    assert RELEASE in str(excinfo.value) and NIGHTLY in str(excinfo.value)

    with pytest.raises(OMPython.OMSessionException, match="Installed versions: none"):
        omc_home_get({}, version="1.26.0")


def test_default_openmodelicahome(environ):
    environ["OPENMODELICAHOME"] = environ[RELEASE]
    assert omc_home_get(environ) == pathlib.Path(environ[RELEASE])


def test_default_openmodelicahome_only():
    # no versioned installations: the path is used as it is, as before
    assert omc_home_get({"OPENMODELICAHOME": "/opt/openmodelica"}) == pathlib.Path("/opt/openmodelica")


def test_default_openmodelicahome_of_uninstalled_version(environ, tmp_path):
    environ["OPENMODELICAHOME"] = str(tmp_path / "uninstalled")
    assert omc_home_get(environ) == pathlib.Path(environ[NIGHTLY])


def test_default_newest_version(environ):
    assert omc_home_get(environ) == pathlib.Path(environ[NIGHTLY])


def test_default_path(tmp_path):
    home = install(tmp_path, "onpath")
    (pathlib.Path(home) / "bin" / "omc").chmod(0o755)
    assert omc_home_get({"PATH": str(pathlib.Path(home) / "bin")}) == pathlib.Path(home)


def test_not_found(tmp_path):
    with pytest.raises(OMPython.OMSessionException, match="Cannot find OpenModelica executable"):
        omc_home_get({"PATH": str(tmp_path)})


def test_names_are_case_insensitive(tmp_path):
    # Windows keeps the case the variable was created with
    home = install(tmp_path, "home")
    assert omc_home_get({"OpenModelicaHome_1_27_0": home}, version="1.27.0") == pathlib.Path(home)
