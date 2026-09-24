"""Version information for OMPython.

Resolves the installed package version via importlib.metadata when
OMPython is installed (pip install, editable install, etc.), and falls
back to reading pyproject.toml directly when running from a source
tree with no installed metadata available.
"""

import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

_FALLBACK_VERSION = "unknown"


def _read_version_from_pyproject() -> str:
    """Return the package version from the pyproject.toml file.

    Raises:
        FileNotFoundError: if pyproject.toml cannot be found.
        KeyError: if the version is not statically defined (e.g. dynamic versioning is used).
    """
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with open(pyproject_path, "rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)
    return pyproject["project"]["version"]


def _resolve_version() -> str:
    try:
        return version(__package__ or "OMPython")
    except PackageNotFoundError:
        pass

    try:
        return _read_version_from_pyproject()
    except (FileNotFoundError, KeyError):
        return _FALLBACK_VERSION


def get_version() -> str:
    """Return the OMPython version string."""
    return __version__


__version__ = _resolve_version()
