# -*- coding: utf-8 -*-
"""
Definition of a generic OM session.
"""

from __future__ import annotations

import abc
import logging
import os
import pathlib
import platform
import sys
from typing import Any, Optional
import uuid

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class OMSessionException(Exception):
    """
    Exception which is raised by any OMC* class.
    """


# due to the compatibility layer to Python < 3.12, the OM(C)Path classes must be hidden behind the following if
# conditions. This is also the reason for OMPathABC, a simple base class to be used in ModelicaSystem* classes.
# Reason: before Python 3.12, pathlib.PurePosixPath can not be derived from; therefore, OMPathABC is not possible
if sys.version_info < (3, 12):
    class _OMPathCompatibility(pathlib.Path):
        """
        Compatibility class for OMPathABC in Python < 3.12. This allows to run all code which uses OMPathABC (mainly
        ModelicaSystem) on these Python versions. There are remaining limitation as only local execution is possible.
        """

        # modified copy of pathlib.Path.__new__() definition
        def __new__(cls, *args, **kwargs):
            logger.warning("Python < 3.12 - using a version of class OMCPath "
                           "based on pathlib.Path for local usage only.")

            if cls is _OMPathCompatibility:
                cls = _OMPathCompatibilityWindows if os.name == 'nt' else _OMPathCompatibilityPosix
            self = cls._from_parts(args)
            if not self._flavour.is_supported:
                raise NotImplementedError(f"cannot instantiate {cls.__name__} on your system")
            return self

        def size(self) -> int:
            """
            Needed compatibility function to have the same interface as OMCPathReal
            """
            return self.stat().st_size

    class _OMPathCompatibilityPosix(pathlib.PosixPath, _OMPathCompatibility):
        """
        Compatibility class for OMCPath on Posix systems (Python < 3.12)
        """

    class _OMPathCompatibilityWindows(pathlib.WindowsPath, _OMPathCompatibility):
        """
        Compatibility class for OMCPath on Windows systems (Python < 3.12)
        """

    OMPathABC = _OMPathCompatibility

else:
    class OMPathABC(pathlib.PurePosixPath, metaclass=abc.ABCMeta):
        """
        Implementation of a basic (PurePosix)Path object to be used within OMPython. The derived classes can use OMC as
        backend and - thus - work on different configurations like docker or WSL. The connection to OMC is provided via
        an instances of classes derived from BaseSession.

        PurePosixPath is selected as it covers all but Windows systems (Linux, docker, WSL). However, the code is
        written such that possible Windows system are taken into account. Nevertheless, the overall functionality is
        limited compared to standard pathlib.Path objects.
        """

        def __init__(self, *path, session: OMSessionABC) -> None:
            super().__init__(*path)
            self._session = session

        def get_session(self) -> OMSessionABC:
            """
            Get session definition used for this instance of OMPath.
            """
            return self._session

        def with_segments(self, *pathsegments) -> OMPathABC:
            """
            Create a new OMCPath object with the given path segments.

            The original definition of Path is overridden to ensure the session data is set.
            """
            return type(self)(*pathsegments, session=self._session)

        @abc.abstractmethod
        def is_file(self, *, follow_symlinks=True) -> bool:
            """
            Check if the path is a regular file.
            """

        @abc.abstractmethod
        def is_dir(self, *, follow_symlinks: bool = True) -> bool:
            """
            Check if the path is a directory.
            """

        @abc.abstractmethod
        def is_absolute(self) -> bool:
            """
            Check if the path is an absolute path.
            """

        @abc.abstractmethod
        def read_text(self, encoding=None, errors=None, newline=None) -> str:
            """
            Read the content of the file represented by this path as text.
            """

        @abc.abstractmethod
        def write_text(self, data: str, encoding=None, errors=None, newline=None) -> int:
            """
            Write text data to the file represented by this path.
            """

        @abc.abstractmethod
        def mkdir(self, mode=0o777, parents: bool = False, exist_ok: bool = False) -> None:
            """
            Create a directory at the path represented by this class.

            The argument parents with default value True exists to ensure compatibility with the fallback solution for
            Python < 3.12. In this case, pathlib.Path is used directly and this option ensures, that missing parent
            directories are also created.
            """

        @abc.abstractmethod
        def cwd(self) -> OMPathABC:  # pylint: disable=W0221 # is @classmethod in the original; see pathlib.PathBase
            """
            Returns the current working directory as an OMPathABC object.
            """

        @abc.abstractmethod
        def unlink(self, missing_ok: bool = False) -> None:
            """
            Unlink (delete) the file or directory represented by this path.
            """

        @abc.abstractmethod
        def resolve(self, strict: bool = False) -> OMPathABC:
            """
            Resolve the path to an absolute path.
            """

        def absolute(self) -> OMPathABC:
            """
            Resolve the path to an absolute path. Just a wrapper for resolve().
            """
            return self.resolve()

        def exists(self) -> bool:
            """
            Semi replacement for pathlib.Path.exists().
            """
            return self.is_file() or self.is_dir()

        @abc.abstractmethod
        def size(self) -> int:
            """
            Get the size of the file in bytes - this is an extra function and the best we can do using OMC.
            """


class PostInitCaller(type):
    """
    Metaclass definition to define a new function __post_init__() which is called after all __init__() functions where
    executed. The workflow would read as follows:

    On creating a class with the following inheritance Class2 => Class1 => Class0, where each class calls the __init__()
    functions of its parent, i.e. super().__init__(), as well as __post_init__() the call schema would be:

    myclass = Class2()
        Class2.__init__()
        Class1.__init__()
        Class0.__init__()
        Class2.__post_init__() <= this is done due to the metaclass
        Class1.__post_init__()
        Class0.__post_init__()

    References:
    * https://stackoverflow.com/questions/100003/what-are-metaclasses-in-python
    * https://stackoverflow.com/questions/795190/how-to-perform-common-post-initialization-tasks-in-inherited-classes
    """

    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post_init__()
        return obj


class OMSessionMeta(abc.ABCMeta, PostInitCaller):
    """
    Helper class to get a combined metaclass of ABCMeta and PostInitCaller.

    References:
    * https://stackoverflow.com/questions/11276037/resolving-metaclass-conflicts
    """


class OMSessionABC(metaclass=OMSessionMeta):
    """
    This class implements the basic structure a OMPython session definition needs. It provides the structure for an
    implementation using OMC as backend (via ZMQ) or a dummy implementation which just runs a model executable.
    """

    def __init__(
            self,
            timeout: float = 10.00,
            **kwargs,
    ) -> None:
        """
        Initialisation for OMSessionBase
        """

        # some helper data
        self.model_execution_windows = platform.system() == "Windows"
        self.model_execution_local = False

        # store variables
        self._timeout = timeout
        # command prefix (to be used for docker or WSL)
        self._cmd_prefix: list[str] = []

    def __post_init__(self) -> None:
        """
        Post initialisation method.
        """

    def get_cmd_prefix(self) -> list[str]:
        """
        Get session definition used for this instance of OMPath.
        """
        return self._cmd_prefix.copy()

    @staticmethod
    def escape_str(value: str) -> str:
        """
        Escape a string such that it can be used as string within OMC expressions, i.e. escape all double quotes.
        """
        return value.replace("\\", "\\\\").replace('"', '\\"')

    @abc.abstractmethod
    def model_execution_prefix(self, cwd: Optional[OMPathABC] = None) -> list[str]:
        """
        Helper function which returns a command prefix.
        """

    @abc.abstractmethod
    def get_version(self) -> str:
        """
        Get the OM version.
        """

    @abc.abstractmethod
    def set_workdir(self, workdir: OMPathABC) -> None:
        """
        Set the workdir for this session.
        """

    @abc.abstractmethod
    def omcpath(self, *path) -> OMPathABC:
        """
        Create an OMPathABC object based on the given path segments and the current class.
        """

    @abc.abstractmethod
    def omcpath_tempdir(self, tempdir_base: Optional[OMPathABC] = None) -> OMPathABC:
        """
        Get a temporary directory based on the specific definition for this session.
        """

    @staticmethod
    def _tempdir(tempdir_base: OMPathABC) -> OMPathABC:
        names = [str(uuid.uuid4()) for _ in range(100)]

        tempdir: Optional[OMPathABC] = None
        for name in names:
            # create a unique temporary directory name
            tempdir = tempdir_base / name

            if tempdir.exists():
                continue

            tempdir.mkdir(parents=True, exist_ok=False)
            break

        if tempdir is None or not tempdir.is_dir():
            raise FileNotFoundError(f"Cannot create a temporary directory in {tempdir_base}!")

        return tempdir

    @abc.abstractmethod
    def sendExpression(self, expr: str, parsed: bool = True) -> Any:
        """
        Function needed to send expressions to the OMC server via ZMQ.
        """
