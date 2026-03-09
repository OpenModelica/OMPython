# -*- coding: utf-8 -*-
"""
Definition of an OM session just executing a compiled model executable (Runner).
"""

from __future__ import annotations

import abc
import logging
import pathlib
import subprocess
import sys
import tempfile
from typing import Any, Optional, Type

from OMPython.om_session_abc import (
    OMPathABC,
    OMSessionABC,
    OMSessionException,
)

# define logger using the current module name as ID
logger = logging.getLogger(__name__)

# due to the compatibility layer to Python < 3.12, the OM(C)Path classes must be hidden behind the following if
# conditions. This is also the reason for OMPathABC, a simple base class to be used in ModelicaSystem* classes.
# Reason: before Python 3.12, pathlib.PurePosixPath can not be derived from; therefore, OMPathABC is not possible
if sys.version_info < (3, 12):
    OMPathRunnerABC = OMPathABC
    OMPathRunnerLocal = OMPathABC
    OMPathRunnerBash = OMPathABC

else:
    class OMPathRunnerABC(OMPathABC, metaclass=abc.ABCMeta):
        """
        Base function for OMPath definitions *without* OMC server
        """

        def _path(self) -> pathlib.Path:
            return pathlib.Path(self.as_posix())

    class _OMPathRunnerLocal(OMPathRunnerABC):
        """
        Implementation of OMPathABC which does not use the session data at all. Thus, this implementation can run
        locally without any usage of OMC.

        This class is based on OMPathABC and, therefore, on pathlib.PurePosixPath. This is working well, but it is not
        the correct implementation on Windows systems. To get a valid Windows representation of the path, use the
        conversion via pathlib.Path(<OMCPathDummy>.as_posix()).
        """

        def is_file(self, *, follow_symlinks=True) -> bool:
            """
            Check if the path is a regular file.
            """
            del follow_symlinks

            return self._path().is_file()

        def is_dir(self, *, follow_symlinks: bool = True) -> bool:
            """
            Check if the path is a directory.
            """
            del follow_symlinks

            return self._path().is_dir()

        def is_absolute(self) -> bool:
            """
            Check if the path is an absolute path.
            """
            return self._path().is_absolute()

        def read_text(self, encoding=None, errors=None, newline=None) -> str:
            """
            Read the content of the file represented by this path as text.
            """
            del encoding, errors, newline

            return self._path().read_text(encoding='utf-8')

        def write_text(self, data: str, encoding=None, errors=None, newline=None):
            """
            Write text data to the file represented by this path.
            """
            del encoding, errors, newline

            if not isinstance(data, str):
                raise TypeError(f"data must be str, not {data.__class__.__name__}")

            return self._path().write_text(data=data, encoding='utf-8')

        def mkdir(self, mode=0o777, parents: bool = False, exist_ok: bool = False) -> None:
            """
            Create a directory at the path represented by this class.

            The argument parents with default value True exists to ensure compatibility with the fallback solution for
            Python < 3.12. In this case, pathlib.Path is used directly and this option ensures, that missing parent
            directories are also created.
            """
            del mode

            self._path().mkdir(parents=parents, exist_ok=exist_ok)

        def cwd(self) -> OMPathABC:  # pylint: disable=W0221 # is @classmethod in the original; see pathlib.PathBase
            """
            Returns the current working directory as an OMPathABC object.
            """
            return type(self)(self._path().cwd().as_posix(), session=self._session)

        def unlink(self, missing_ok: bool = False) -> None:
            """
            Unlink (delete) the file or directory represented by this path.
            """
            self._path().unlink(missing_ok=missing_ok)

        def resolve(self, strict: bool = False) -> OMPathABC:
            """
            Resolve the path to an absolute path. This is done based on available OMC functions.
            """
            path_resolved = self._path().resolve(strict=strict)
            return type(self)(path_resolved, session=self._session)

        def size(self) -> int:
            """
            Get the size of the file in bytes - implementation based on pathlib.Path.
            """
            if not self.is_file():
                raise OMSessionException(f"Path {self.as_posix()} is not a file!")

            path = self._path()
            return path.stat().st_size

    class _OMPathRunnerBash(OMPathRunnerABC):
        """
        Implementation of OMPathABC which does not use the session data at all. Thus, this implementation can run
        locally without any usage of OMC. The special case of this class is the usage of POSIX bash to run all the
        commands. Thus, it can be used in WSL or docker.

        This class is based on OMPathABC and, therefore, on pathlib.PurePosixPath. This is working well, but it is not
        the correct implementation on Windows systems. To get a valid Windows representation of the path, use the
        conversion via pathlib.Path(<OMCPathDummy>.as_posix()).
        """

        def is_file(self, *, follow_symlinks=True) -> bool:
            """
            Check if the path is a regular file.
            """
            del follow_symlinks

            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'test -f "{self.as_posix()}"']

            try:
                subprocess.run(cmdl, check=True)
                return True
            except subprocess.CalledProcessError:
                return False

        def is_dir(self, *, follow_symlinks: bool = True) -> bool:
            """
            Check if the path is a directory.
            """
            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'test -d "{self.as_posix()}"']

            try:
                subprocess.run(cmdl, check=True)
                return True
            except subprocess.CalledProcessError:
                return False

        def is_absolute(self) -> bool:
            """
            Check if the path is an absolute path.
            """

            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'case "{self.as_posix()}" in /*) exit 0;; *) exit 1;; esac']

            try:
                subprocess.check_call(cmdl)
                return True
            except subprocess.CalledProcessError:
                return False

        def read_text(self, encoding=None, errors=None, newline=None) -> str:
            """
            Read the content of the file represented by this path as text.
            """
            del encoding, errors, newline

            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'cat "{self.as_posix()}"']

            result = subprocess.run(cmdl, capture_output=True, check=True)
            if result.returncode == 0:
                return result.stdout.decode('utf-8')
            raise FileNotFoundError(f"Cannot read file: {self.as_posix()}")

        def write_text(self, data: str, encoding=None, errors=None, newline=None) -> int:
            """
            Write text data to the file represented by this path.
            """
            del encoding, errors, newline

            if not isinstance(data, str):
                raise TypeError(f"data must be str, not {data.__class__.__name__}")

            data_escape = self._session.escape_str(data)

            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'printf %s "{data_escape}" > "{self.as_posix()}"']

            try:
                subprocess.run(cmdl, check=True)
                return len(data)
            except subprocess.CalledProcessError as exc:
                raise IOError(f"Error writing data to file {self.as_posix()}!") from exc

        def mkdir(self, mode=0o777, parents: bool = False, exist_ok: bool = False) -> None:
            """
            Create a directory at the path represented by this class.

            The argument parents with default value True exists to ensure compatibility with the fallback solution for
            Python < 3.12. In this case, pathlib.Path is used directly and this option ensures, that missing parent
            directories are also created.
            """
            del mode

            if self.is_file():
                raise OSError(f"The given path {self.as_posix()} exists and is a file!")
            if self.is_dir() and not exist_ok:
                raise OSError(f"The given path {self.as_posix()} exists and is a directory!")
            if not parents and not self.parent.is_dir():
                raise FileNotFoundError(f"Parent directory of {self.as_posix()} does not exists!")

            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'mkdir -p "{self.as_posix()}"']

            try:
                subprocess.run(cmdl, check=True)
            except subprocess.CalledProcessError as exc:
                raise OMSessionException(f"Error on directory creation for {self.as_posix()}!") from exc

        def cwd(self) -> OMPathABC:  # pylint: disable=W0221 # is @classmethod in the original; see pathlib.PathBase
            """
            Returns the current working directory as an OMPathABC object.
            """
            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', 'pwd']

            result = subprocess.run(cmdl, capture_output=True, text=True, check=True)
            if result.returncode == 0:
                return type(self)(result.stdout.strip(), session=self._session)
            raise OSError("Can not get current work directory ...")

        def unlink(self, missing_ok: bool = False) -> None:
            """
            Unlink (delete) the file or directory represented by this path.
            """

            if not self.is_file():
                raise OSError(f"Can not unlink a directory: {self.as_posix()}!")

            if not self.is_file():
                return

            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'rm "{self.as_posix()}"']

            try:
                subprocess.run(cmdl, check=True)
            except subprocess.CalledProcessError as exc:
                raise OSError(f"Cannot unlink file {self.as_posix()}: {exc}") from exc

        def resolve(self, strict: bool = False) -> OMPathABC:
            """
            Resolve the path to an absolute path. This is done based on available OMC functions.
            """
            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'readlink -f "{self.as_posix()}"']

            result = subprocess.run(cmdl, capture_output=True, text=True, check=True)
            if result.returncode == 0:
                return type(self)(result.stdout.strip(), session=self._session)
            raise FileNotFoundError(f"Cannot resolve path: {self.as_posix()}")

        def size(self) -> int:
            """
            Get the size of the file in bytes - implementation based on pathlib.Path.
            """
            if not self.is_file():
                raise OMSessionException(f"Path {self.as_posix()} is not a file!")

            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'stat -c %s "{self.as_posix()}"']

            result = subprocess.run(cmdl, capture_output=True, text=True, check=True)
            stdout = result.stdout.strip()
            if result.returncode == 0:
                try:
                    return int(stdout)
                except ValueError as exc:
                    raise OSError(f"Invalid return value for file size ({self.as_posix()}): {stdout}") from exc
            else:
                raise OSError(f"Cannot get size for file {self.as_posix()}")

    OMPathRunnerLocal = _OMPathRunnerLocal
    OMPathRunnerBash = _OMPathRunnerBash


class OMSessionRunnerABC(OMSessionABC, metaclass=abc.ABCMeta):
    """
    Implementation based on OMSessionABC without any use of an OMC server.
    """

    def __init__(
            self,
            ompath_runner: Type[OMPathRunnerABC],
            timeout: float = 10.0,
            version: str = "1.27.0",
            cmd_prefix: Optional[list[str]] = None,
            model_execution_local: bool = True,
    ) -> None:
        super().__init__(timeout=timeout)
        self._version = version

        if not issubclass(ompath_runner, OMPathRunnerABC):
            raise OMSessionException(f"Invalid OMPathRunner class: {type(ompath_runner)}!")
        self._ompath_runner = ompath_runner

        self.model_execution_local = model_execution_local
        if cmd_prefix is not None:
            self._cmd_prefix = cmd_prefix


class OMSessionRunner(OMSessionRunnerABC):
    """
    Implementation based on OMSessionABC without any use of an OMC server.
    """

    def __init__(
            self,
            ompath_runner: Type[OMPathRunnerABC] = OMPathRunnerLocal,
            timeout: float = 10.0,
            version: str = "1.27.0",
            cmd_prefix: Optional[list[str]] = None,
            model_execution_local: bool = True,
    ) -> None:
        super().__init__(
            ompath_runner=ompath_runner,
            timeout=timeout,
            version=version,
            cmd_prefix=cmd_prefix,
            model_execution_local=model_execution_local,
        )

    def __post_init__(self) -> None:
        """
        No connection to an OMC server is created by this class!
        """

    def model_execution_prefix(self, cwd: Optional[OMPathABC] = None) -> list[str]:
        """
        Helper function which returns a command prefix.
        """
        return self.get_cmd_prefix()

    def get_version(self) -> str:
        """
        We can not provide an OM version as we are not link to an OMC server. Thus, the provided version string is used
        directly.
        """
        return self._version

    def set_workdir(self, workdir: OMPathABC) -> None:
        """
        Set the workdir for this session. For OMSessionRunner this is a nop. The workdir must be defined within the
        definition of cmd_prefix.
        """

    def omcpath(self, *path) -> OMPathABC:
        """
        Create an OMCPath object based on the given path segments and the current OMCSession* class.
        """
        return self._ompath_runner(*path, session=self)

    def omcpath_tempdir(self, tempdir_base: Optional[OMPathABC] = None) -> OMPathABC:
        """
        Get a temporary directory without using OMC.
        """
        if tempdir_base is None:
            tempdir_str = tempfile.gettempdir()
            tempdir_base = self.omcpath(tempdir_str)

        return self._tempdir(tempdir_base=tempdir_base)

    def sendExpression(self, expr: str, parsed: bool = True) -> Any:
        raise OMSessionException(f"{self.__class__.__name__} does not uses an OMC server!")
