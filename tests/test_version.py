"""Tests for OMPython._version."""

import importlib.metadata
from OMPython import _version


def test_version_module_resolves_installed_metadata():
    """When OMPython is installed, __version__ should come from
    importlib.metadata and never fall back to 'unknown'."""
    assert _version.__version__ != "unknown"
    assert isinstance(_version.__version__, str)
    assert _version.__version__ != ""


def test_get_version_matches_module_version():
    """get_version() should return the same value as __version__."""
    assert _version.get_version() == _version.__version__


def test_installed_metadata_matches_importlib(monkeypatch=None):
    """Sanity check: the resolved version matches what importlib.metadata
    reports directly, confirming the installed-metadata path is being used."""
    expected = importlib.metadata.version(_version.__package__ or "OMPython")
    assert _version.__version__ == expected


def test_resolve_version_falls_back_when_package_not_found(monkeypatch):
    """If importlib.metadata.version() raises PackageNotFoundError,
    _resolve_version() should fall back to reading pyproject.toml."""

    def raise_not_found(_name):
        raise importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(_version, "version", raise_not_found)

    result = _version._resolve_version()

    # Falls back to reading pyproject.toml; should not silently return
    # "unknown" unless pyproject.toml is genuinely missing/malformed.
    assert result != "unknown"
    assert isinstance(result, str)


def test_resolve_version_returns_unknown_if_pyproject_unreadable(monkeypatch):
    """If both importlib.metadata and the pyproject.toml fallback fail,
    _resolve_version() should return 'unknown' rather than raising."""

    def raise_not_found(_name):
        raise importlib.metadata.PackageNotFoundError

    def raise_file_not_found():
        raise FileNotFoundError

    monkeypatch.setattr(_version, "version", raise_not_found)
    monkeypatch.setattr(_version, "_read_version_from_pyproject", raise_file_not_found)

    result = _version._resolve_version()

    assert result == "unknown"


def test_read_version_from_pyproject_returns_string():
    """_read_version_from_pyproject() should return a non-empty string
    when pyproject.toml is present and well-formed."""
    result = _version._read_version_from_pyproject()
    assert isinstance(result, str)
    assert result != ""
