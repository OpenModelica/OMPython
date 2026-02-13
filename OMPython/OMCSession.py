# -*- coding: utf-8 -*-
"""
Definition of an OMC session.
"""

from __future__ import annotations

import abc
import io
import json
import logging
import os
import pathlib
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any, Optional, Tuple, Type
import uuid
import warnings

import psutil
import pyparsing
import zmq

# TODO: replace this with the new parser
from OMPython.OMTypedParser import om_parser_typed
from OMPython.OMParser import om_parser_basic

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class DockerPopen:
    """
    Dummy implementation of Popen for a (running) docker process. The process is identified by its process ID (pid).
    """

    def __init__(self, pid):
        self.pid = pid
        self.process = psutil.Process(pid)
        self.returncode = 0

    def poll(self):
        return None if self.process.is_running() else True

    def kill(self):
        return os.kill(pid=self.pid, signal=signal.SIGKILL)

    def wait(self, timeout):
        try:
            self.process.wait(timeout=timeout)
        except psutil.TimeoutExpired:
            pass


class OMSessionException(Exception):
    """
    Exception which is raised by any OMC* class.
    """


class OMCSessionException(OMSessionException):
    """
    Just a compatibility layer ...
    """


class OMCSessionCmd:
    """
    Implementation of Open Modelica Compiler API functions. Depreciated!
    """

    def __init__(self, session: OMSessionABC, readonly: bool = False):
        warnings.warn(
            message="The class OMCSessionCMD is depreciated and will be removed in future versions; "
                    "please use OMCSession*.sendExpression(...) instead!",
            category=DeprecationWarning,
            stacklevel=2,
        )

        if not isinstance(session, OMSessionABC):
            raise OMSessionException("Invalid OMC process definition!")
        self._session = session
        self._readonly = readonly
        self._omc_cache: dict[tuple[str, bool], Any] = {}

    def _ask(self, question: str, opt: Optional[list[str]] = None, parsed: bool = True):

        if opt is None:
            expression = question
        elif isinstance(opt, list):
            expression = f"{question}({','.join([str(x) for x in opt])})"
        else:
            raise OMSessionException(f"Invalid definition of options for {repr(question)}: {repr(opt)}")

        p = (expression, parsed)

        if self._readonly and question != 'getErrorString':
            # can use cache if readonly
            if p in self._omc_cache:
                return self._omc_cache[p]

        try:
            res = self._session.sendExpression(expression, parsed=parsed)
        except OMSessionException as ex:
            raise OMSessionException(f"OMC _ask() failed: {expression} (parsed={parsed})") from ex

        # save response
        self._omc_cache[p] = res

        return res

    # TODO: Open Modelica Compiler API functions. Would be nice to generate these.
    def loadFile(self, filename):
        return self._ask(question='loadFile', opt=[f'"{filename}"'])

    def loadModel(self, className):
        return self._ask(question='loadModel', opt=[className])

    def isModel(self, className):
        return self._ask(question='isModel', opt=[className])

    def isPackage(self, className):
        return self._ask(question='isPackage', opt=[className])

    def isPrimitive(self, className):
        return self._ask(question='isPrimitive', opt=[className])

    def isConnector(self, className):
        return self._ask(question='isConnector', opt=[className])

    def isRecord(self, className):
        return self._ask(question='isRecord', opt=[className])

    def isBlock(self, className):
        return self._ask(question='isBlock', opt=[className])

    def isType(self, className):
        return self._ask(question='isType', opt=[className])

    def isFunction(self, className):
        return self._ask(question='isFunction', opt=[className])

    def isClass(self, className):
        return self._ask(question='isClass', opt=[className])

    def isParameter(self, className):
        return self._ask(question='isParameter', opt=[className])

    def isConstant(self, className):
        return self._ask(question='isConstant', opt=[className])

    def isProtected(self, className):
        return self._ask(question='isProtected', opt=[className])

    def getPackages(self, className="AllLoadedClasses"):
        return self._ask(question='getPackages', opt=[className])

    def getClassRestriction(self, className):
        return self._ask(question='getClassRestriction', opt=[className])

    def getDerivedClassModifierNames(self, className):
        return self._ask(question='getDerivedClassModifierNames', opt=[className])

    def getDerivedClassModifierValue(self, className, modifierName):
        return self._ask(question='getDerivedClassModifierValue', opt=[className, modifierName])

    def typeNameStrings(self, className):
        return self._ask(question='typeNameStrings', opt=[className])

    def getComponents(self, className):
        return self._ask(question='getComponents', opt=[className])

    def getClassComment(self, className):
        try:
            return self._ask(question='getClassComment', opt=[className])
        except pyparsing.ParseException as ex:
            logger.warning("Method 'getClassComment(%s)' failed; OMTypedParser error: %s",
                           className, ex.msg)
            return 'No description available'

    def getNthComponent(self, className, comp_id):
        """ returns with (type, name, description) """
        return self._ask(question='getNthComponent', opt=[className, comp_id])

    def getNthComponentAnnotation(self, className, comp_id):
        return self._ask(question='getNthComponentAnnotation', opt=[className, comp_id])

    def getImportCount(self, className):
        return self._ask(question='getImportCount', opt=[className])

    def getNthImport(self, className, importNumber):
        # [Path, id, kind]
        return self._ask(question='getNthImport', opt=[className, importNumber])

    def getInheritanceCount(self, className):
        return self._ask(question='getInheritanceCount', opt=[className])

    def getNthInheritedClass(self, className, inheritanceDepth):
        return self._ask(question='getNthInheritedClass', opt=[className, inheritanceDepth])

    def getParameterNames(self, className):
        try:
            return self._ask(question='getParameterNames', opt=[className])
        except KeyError as ex:
            logger.warning('OMPython error: %s', ex)
            # FIXME: OMC returns with a different structure for empty parameter set
            return []

    def getParameterValue(self, className, parameterName):
        try:
            return self._ask(question='getParameterValue', opt=[className, parameterName])
        except pyparsing.ParseException as ex:
            logger.warning("Method 'getParameterValue(%s, %s)' failed; OMTypedParser error: %s",
                           className, parameterName, ex.msg)
            return ""

    def getComponentModifierNames(self, className, componentName):
        return self._ask(question='getComponentModifierNames', opt=[className, componentName])

    def getComponentModifierValue(self, className, componentName):
        return self._ask(question='getComponentModifierValue', opt=[className, componentName])

    def getExtendsModifierNames(self, className, componentName):
        return self._ask(question='getExtendsModifierNames', opt=[className, componentName])

    def getExtendsModifierValue(self, className, extendsName, modifierName):
        return self._ask(question='getExtendsModifierValue', opt=[className, extendsName, modifierName])

    def getNthComponentModification(self, className, comp_id):
        # FIXME: OMPython exception Results KeyError exception

        # get {$Code(....)} field
        # \{\$Code\((\S*\s*)*\)\}
        value = self._ask(question='getNthComponentModification', opt=[className, comp_id], parsed=False)
        value = value.replace("{$Code(", "")
        return value[:-3]
        # return self.re_Code.findall(value)

    # function getClassNames
    #   input TypeName class_ = $Code(AllLoadedClasses);
    #   input Boolean recursive = false;
    #   input Boolean qualified = false;
    #   input Boolean sort = false;
    #   input Boolean builtin = false "List also builtin classes if true";
    #   input Boolean showProtected = false "List also protected classes if true";
    #   output TypeName classNames[:];
    # end getClassNames;
    def getClassNames(self, className=None, recursive=False, qualified=False, sort=False, builtin=False,
                      showProtected=False):
        opt = [className] if className else [] + [f'recursive={str(recursive).lower()}',
                                                  f'qualified={str(qualified).lower()}',
                                                  f'sort={str(sort).lower()}',
                                                  f'builtin={str(builtin).lower()}',
                                                  f'showProtected={str(showProtected).lower()}']
        return self._ask(question='getClassNames', opt=opt)


# due to the compatibility layer to Python < 3.12, the OM(C)Path classes must be hidden behind the following if
# conditions. This is also the reason for OMPathABC, a simple base class to be used in ModelicaSystem* classes.
# Reason: before Python 3.12, pathlib.PurePosixPath can not be derived from; therefore, OMPathABC is not possible
if sys.version_info < (3, 12):
    class OMPathCompatibility(pathlib.Path):
        """
        Compatibility class for OMPathABC in Python < 3.12. This allows to run all code which uses OMPathABC (mainly
        ModelicaSystem) on these Python versions. There are remaining limitation as only local execution is possible.
        """

        # modified copy of pathlib.Path.__new__() definition
        def __new__(cls, *args, **kwargs):
            logger.warning("Python < 3.12 - using a version of class OMCPath "
                           "based on pathlib.Path for local usage only.")

            if cls is OMPathCompatibility:
                cls = OMPathCompatibilityWindows if os.name == 'nt' else OMPathCompatibilityPosix
            self = cls._from_parts(args)
            if not self._flavour.is_supported:
                raise NotImplementedError(f"cannot instantiate {cls.__name__} on your system")
            return self

        def size(self) -> int:
            """
            Needed compatibility function to have the same interface as OMCPathReal
            """
            return self.stat().st_size

    class OMPathCompatibilityPosix(pathlib.PosixPath, OMPathCompatibility):
        """
        Compatibility class for OMCPath on Posix systems (Python < 3.12)
        """

    class OMPathCompatibilityWindows(pathlib.WindowsPath, OMPathCompatibility):
        """
        Compatibility class for OMCPath on Windows systems (Python < 3.12)
        """

    OMPathABC = OMPathCompatibility
    OMCPath = OMPathCompatibility
    OMPathRunnerABC = OMPathCompatibility
    OMPathRunnerLocal = OMPathCompatibility
    OMPathRunnerBash = OMPathCompatibility

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
        def is_file(self) -> bool:
            """
            Check if the path is a regular file.
            """

        @abc.abstractmethod
        def is_dir(self) -> bool:
            """
            Check if the path is a directory.
            """

        @abc.abstractmethod
        def is_absolute(self) -> bool:
            """
            Check if the path is an absolute path.
            """

        @abc.abstractmethod
        def read_text(self) -> str:
            """
            Read the content of the file represented by this path as text.
            """

        @abc.abstractmethod
        def write_text(self, data: str) -> int:
            """
            Write text data to the file represented by this path.
            """

        @abc.abstractmethod
        def mkdir(self, parents: bool = True, exist_ok: bool = False) -> None:
            """
            Create a directory at the path represented by this class.

            The argument parents with default value True exists to ensure compatibility with the fallback solution for
            Python < 3.12. In this case, pathlib.Path is used directly and this option ensures, that missing parent
            directories are also created.
            """

        @abc.abstractmethod
        def cwd(self) -> OMPathABC:
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

    class _OMCPath(OMPathABC):
        """
        Implementation of a OMPathABC using OMC as backend. The connection to OMC is provided via an instances of an
        OMCSession* classes.
        """

        def is_file(self) -> bool:
            """
            Check if the path is a regular file.
            """
            retval = self.get_session().sendExpression(expr=f'regularFileExists("{self.as_posix()}")')
            if not isinstance(retval, bool):
                raise OMSessionException(f"Invalid return value for is_file(): {retval} - expect bool")
            return retval

        def is_dir(self) -> bool:
            """
            Check if the path is a directory.
            """
            retval = self.get_session().sendExpression(expr=f'directoryExists("{self.as_posix()}")')
            if not isinstance(retval, bool):
                raise OMSessionException(f"Invalid return value for is_dir(): {retval} - expect bool")
            return retval

        def is_absolute(self) -> bool:
            """
            Check if the path is an absolute path. Special handling to differentiate Windows and Posix definitions.
            """
            if self._session.model_execution_windows and self._session.model_execution_local:
                return pathlib.PureWindowsPath(self.as_posix()).is_absolute()
            return pathlib.PurePosixPath(self.as_posix()).is_absolute()

        def read_text(self) -> str:
            """
            Read the content of the file represented by this path as text.
            """
            retval = self.get_session().sendExpression(expr=f'readFile("{self.as_posix()}")')
            if not isinstance(retval, str):
                raise OMSessionException(f"Invalid return value for read_text(): {retval} - expect str")
            return retval

        def write_text(self, data: str) -> int:
            """
            Write text data to the file represented by this path.
            """
            if not isinstance(data, str):
                raise TypeError(f"data must be str, not {data.__class__.__name__}")

            data_omc = self._session.escape_str(data)
            self._session.sendExpression(expr=f'writeFile("{self.as_posix()}", "{data_omc}", false);')

            return len(data)

        def mkdir(self, parents: bool = True, exist_ok: bool = False) -> None:
            """
            Create a directory at the path represented by this class.

            The argument parents with default value True exists to ensure compatibility with the fallback solution for
            Python < 3.12. In this case, pathlib.Path is used directly and this option ensures, that missing parent
            directories are also created.
            """
            if self.is_dir() and not exist_ok:
                raise FileExistsError(f"Directory {self.as_posix()} already exists!")

            if not self._session.sendExpression(expr=f'mkdir("{self.as_posix()}")'):
                raise OMSessionException(f"Error on directory creation for {self.as_posix()}!")

        def cwd(self) -> OMPathABC:
            """
            Returns the current working directory as an OMPathABC object.
            """
            cwd_str = self._session.sendExpression(expr='cd()')
            return type(self)(cwd_str, session=self._session)

        def unlink(self, missing_ok: bool = False) -> None:
            """
            Unlink (delete) the file or directory represented by this path.
            """
            res = self._session.sendExpression(expr=f'deleteFile("{self.as_posix()}")')
            if not res and not missing_ok:
                raise FileNotFoundError(f"Cannot delete file {self.as_posix()} - it does not exists!")

        def resolve(self, strict: bool = False) -> OMPathABC:
            """
            Resolve the path to an absolute path. This is done based on available OMC functions.
            """
            if strict and not (self.is_file() or self.is_dir()):
                raise OMSessionException(f"Path {self.as_posix()} does not exist!")

            if self.is_file():
                pathstr_resolved = self._omc_resolve(self.parent.as_posix())
                omcpath_resolved = self._session.omcpath(pathstr_resolved) / self.name
            elif self.is_dir():
                pathstr_resolved = self._omc_resolve(self.as_posix())
                omcpath_resolved = self._session.omcpath(pathstr_resolved)
            else:
                raise OMSessionException(f"Path {self.as_posix()} is neither a file nor a directory!")

            if not omcpath_resolved.is_file() and not omcpath_resolved.is_dir():
                raise OMSessionException(f"OMCPath resolve failed for {self.as_posix()} - path does not exist!")

            return omcpath_resolved

        def _omc_resolve(self, pathstr: str) -> str:
            """
            Internal function to resolve the path of the OMCPath object using OMC functions *WITHOUT* changing the cwd
            within OMC.
            """
            expr = ('omcpath_cwd := cd(); '
                    f'omcpath_check := cd("{pathstr}"); '  # check requested pathstring
                    'cd(omcpath_cwd)')

            try:
                retval = self.get_session().sendExpression(expr=expr, parsed=False)
                if not isinstance(retval, str):
                    raise OMSessionException(f"Invalid return value for _omc_resolve(): {retval} - expect str")
                result_parts = retval.split('\n')
                pathstr_resolved = result_parts[1]
                pathstr_resolved = pathstr_resolved[1:-1]  # remove quotes
            except OMSessionException as ex:
                raise OMSessionException(f"OMCPath resolve failed for {pathstr}!") from ex

            return pathstr_resolved

        def size(self) -> int:
            """
            Get the size of the file in bytes - this is an extra function and the best we can do using OMC.
            """
            if not self.is_file():
                raise OMSessionException(f"Path {self.as_posix()} is not a file!")

            res = self._session.sendExpression(expr=f'stat("{self.as_posix()}")')
            if res[0]:
                return int(res[1])

            raise OMSessionException(f"Error reading file size for path {self.as_posix()}!")

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

        def is_file(self) -> bool:
            """
            Check if the path is a regular file.
            """
            return self._path().is_file()

        def is_dir(self) -> bool:
            """
            Check if the path is a directory.
            """
            return self._path().is_dir()

        def is_absolute(self) -> bool:
            """
            Check if the path is an absolute path.
            """
            return self._path().is_absolute()

        def read_text(self) -> str:
            """
            Read the content of the file represented by this path as text.
            """
            return self._path().read_text(encoding='utf-8')

        def write_text(self, data: str):
            """
            Write text data to the file represented by this path.
            """
            if not isinstance(data, str):
                raise TypeError(f"data must be str, not {data.__class__.__name__}")

            return self._path().write_text(data=data, encoding='utf-8')

        def mkdir(self, parents: bool = True, exist_ok: bool = False) -> None:
            """
            Create a directory at the path represented by this class.

            The argument parents with default value True exists to ensure compatibility with the fallback solution for
            Python < 3.12. In this case, pathlib.Path is used directly and this option ensures, that missing parent
            directories are also created.
            """
            self._path().mkdir(parents=parents, exist_ok=exist_ok)

        def cwd(self) -> OMPathABC:
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

        def is_file(self) -> bool:
            """
            Check if the path is a regular file.
            """
            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'test -f "{self.as_posix()}"']

            try:
                subprocess.run(cmdl, check=True)
                return True
            except subprocess.CalledProcessError:
                return False

        def is_dir(self) -> bool:
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

        def read_text(self) -> str:
            """
            Read the content of the file represented by this path as text.
            """
            cmdl = self.get_session().get_cmd_prefix()
            cmdl += ['bash', '-c', f'cat "{self.as_posix()}"']

            result = subprocess.run(cmdl, capture_output=True, check=True)
            if result.returncode == 0:
                return result.stdout.decode('utf-8')
            raise FileNotFoundError(f"Cannot read file: {self.as_posix()}")

        def write_text(self, data: str) -> int:
            """
            Write text data to the file represented by this path.
            """
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

        def mkdir(self, parents: bool = True, exist_ok: bool = False) -> None:
            """
            Create a directory at the path represented by this class.

            The argument parents with default value True exists to ensure compatibility with the fallback solution for
            Python < 3.12. In this case, pathlib.Path is used directly and this option ensures, that missing parent
            directories are also created.
            """

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

        def cwd(self) -> OMPathABC:
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

    OMCPath = _OMCPath
    OMPathRunnerLocal = _OMPathRunnerLocal
    OMPathRunnerBash = _OMPathRunnerBash


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


class OMCSessionABC(OMSessionABC, metaclass=abc.ABCMeta):
    """
    Base class for an OMC session started via ZMQ. This class contains common functionality for all variants of an
    OMC session definition.

    The main method is sendExpression() which is used to send commands to the OMC process.

    The following variants are defined:

    * OMCSessionLocal

    * OMCSessionPort

    * OMCSessionDocker

    * OMCSessionDockerContainer

    * OMCSessionWSL
    """

    def __init__(
            self,
            timeout: float = 10.00,
            **kwargs,
    ) -> None:
        """
        Initialisation for OMCSession
        """
        super().__init__(timeout=timeout)

        # some helper data
        self.model_execution_windows = platform.system() == "Windows"
        self.model_execution_local = False

        # generate a random string for this instance of OMC
        self._random_string = uuid.uuid4().hex
        # get a temporary directory
        self._temp_dir = pathlib.Path(tempfile.gettempdir())

        # omc process
        self._omc_process: Optional[subprocess.Popen] = None
        # omc ZMQ port to use
        self._omc_port: Optional[str] = None
        # omc port and log file
        self._omc_filebase = f"openmodelica.{self._random_string}"
        # ZMQ socket to communicate with OMC
        self._omc_zmq: Optional[zmq.Socket[bytes]] = None

        # setup log file - this file must be closed in the destructor
        self._omc_logfile = self._temp_dir / (self._omc_filebase + ".log")
        self._omc_loghandle: Optional[io.TextIOWrapper] = None
        try:
            self._omc_loghandle = open(file=self._omc_logfile, mode="w+", encoding="utf-8")
        except OSError as ex:
            raise OMSessionException(f"Cannot open log file {self._omc_logfile}.") from ex

        # variables to store compiled re expressions use in self.sendExpression()
        self._re_log_entries: Optional[re.Pattern[str]] = None
        self._re_log_raw: Optional[re.Pattern[str]] = None

        self._re_portfile_path = re.compile(pattern=r'\nDumped server port in file: (.*?)($|\n)',
                                            flags=re.MULTILINE | re.DOTALL)

    def __post_init__(self) -> None:
        """
        Create the connection to the OMC server using ZeroMQ.
        """
        # set_timeout() is used to define the value of _timeout as it includes additional checks
        self.set_timeout(timeout=self._timeout)

        port = self.get_port()
        if not isinstance(port, str):
            raise OMSessionException(f"Invalid content for port: {port}")

        # Create the ZeroMQ socket and connect to OMC server
        context = zmq.Context.instance()
        omc = context.socket(zmq.REQ)
        omc.setsockopt(zmq.LINGER, 0)  # Dismisses pending messages if closed
        omc.setsockopt(zmq.IMMEDIATE, True)  # Queue messages only to completed connections
        omc.connect(port)

        self._omc_zmq = omc

    def __del__(self):
        if isinstance(self._omc_zmq, zmq.Socket):
            try:
                self.sendExpression(expr="quit()")
            except OMSessionException as exc:
                logger.warning(f"Exception on sending 'quit()' to OMC: {exc}! Continue nevertheless ...")
            finally:
                self._omc_zmq = None

        if self._omc_loghandle is not None:
            try:
                self._omc_loghandle.close()
            except (OSError, IOError):
                pass
            finally:
                self._omc_loghandle = None

        if isinstance(self._omc_process, subprocess.Popen):
            try:
                self._omc_process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                if self._omc_process:
                    logger.warning("OMC did not exit after being sent the 'quit()' command; "
                                   "killing the process with pid=%s", self._omc_process.pid)
                    self._omc_process.kill()
                    self._omc_process.wait()
            finally:

                self._omc_process = None

    def _timeout_loop(
            self,
            timeout: Optional[float] = None,
            timestep: float = 0.1,
    ):
        """
        Helper (using yield) for while loops to check OMC startup / response. The loop is executed as long as True is
        returned, i.e. the first False will stop the while loop.
        """

        if timeout is None:
            timeout = self._timeout
        if timeout <= 0:
            raise OMSessionException(f"Invalid timeout: {timeout}")

        timer = 0.0
        yield True
        while True:
            timer += timestep
            if timer > timeout:
                break
            time.sleep(timestep)
            yield True
        yield False

    def set_timeout(self, timeout: Optional[float] = None) -> float:
        """
        Set the timeout to be used for OMC communication (OMCSession).

        The defined value is set and the current value is returned. If None is provided as argument, nothing is changed.
        """
        retval = self._timeout
        if timeout is not None:
            if timeout <= 0.0:
                raise OMSessionException(f"Invalid timeout value: {timeout}!")
            self._timeout = timeout
        return retval

    @staticmethod
    def escape_str(value: str) -> str:
        """
        Escape a string such that it can be used as string within OMC expressions, i.e. escape all double quotes.
        """
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def get_version(self) -> str:
        """
        Get the OM version.
        """
        return self.sendExpression("getVersion()", parsed=True)

    def set_workdir(self, workdir: OMPathABC) -> None:
        """
        Set the workdir for this session.
        """
        exp = f'cd("{workdir.as_posix()}")'
        self.sendExpression(exp)

    def model_execution_prefix(self, cwd: Optional[OMPathABC] = None) -> list[str]:
        """
        Helper function which returns a command prefix needed for docker and WSL. It defaults to an empty list.
        """

        return []

    def omcpath(self, *path) -> OMPathABC:
        """
        Create an OMCPath object based on the given path segments and the current OMCSession* class.
        """

        # fallback solution for Python < 3.12; a modified pathlib.Path object is used as OMCPath replacement
        if sys.version_info < (3, 12):
            if isinstance(self, OMCSessionLocal):
                # noinspection PyArgumentList
                return OMCPath(*path)
            raise OMSessionException("OMCPath is supported for Python < 3.12 only if OMCSessionLocal is used!")
        return OMCPath(*path, session=self)

    def omcpath_tempdir(self, tempdir_base: Optional[OMPathABC] = None) -> OMPathABC:
        """
        Get a temporary directory using OMC. It is our own implementation as non-local usage relies on OMC to run all
        filesystem related access.
        """

        if tempdir_base is None:
            # fallback solution for Python < 3.12; a modified pathlib.Path object is used as OMCPath replacement
            if sys.version_info < (3, 12):
                tempdir_str = tempfile.gettempdir()
            else:
                tempdir_str = self.sendExpression(expr="getTempDirectoryPath()")
            tempdir_base = self.omcpath(tempdir_str)

        return self._tempdir(tempdir_base=tempdir_base)

    def execute(self, command: str):
        warnings.warn(
            message="This function is depreciated and will be removed in future versions; "
                    "please use sendExpression() instead",
            category=DeprecationWarning,
            stacklevel=2,
        )

        return self.sendExpression(command, parsed=False)

    def sendExpression(self, expr: str, parsed: bool = True) -> Any:
        """
        Send an expression to the OMC server and return the result.

        The complete error handling of the OMC result is done within this method using 'getMessagesStringInternal()'.
        Caller should only check for OMCSessionException.
        """

        if self._omc_zmq is None:
            raise OMSessionException("No OMC running. Please create a new instance of OMCSession!")

        logger.debug("sendExpression(expr='%r', parsed=%r)", str(expr), parsed)

        loop = self._timeout_loop(timestep=0.05)
        while next(loop):
            try:
                self._omc_zmq.send_string(str(expr), flags=zmq.NOBLOCK)
                break
            except zmq.error.Again:
                pass
        else:
            # in the deletion process, the content is cleared. Thus, any access to a class attribute must be checked
            try:
                log_content = self.get_log()
            except OMSessionException:
                log_content = 'log not available'

            logger.error(f"OMC did not start. Log-file says:\n{log_content}")
            raise OMSessionException(f"No connection with OMC (timeout={self._timeout}).")

        if expr == "quit()":
            self._omc_zmq.close()
            self._omc_zmq = None
            return None

        result = self._omc_zmq.recv_string()

        if result.startswith('Error occurred building AST'):
            raise OMSessionException(f"OMC error: {result}")

        if expr == "getErrorString()":
            # no error handling if 'getErrorString()' is called
            if parsed:
                logger.warning("Result of 'getErrorString()' cannot be parsed!")
            return result

        if expr == "getMessagesStringInternal()":
            # no error handling if 'getMessagesStringInternal()' is called
            if parsed:
                logger.warning("Result of 'getMessagesStringInternal()' cannot be parsed!")
            return result

        # always check for error
        self._omc_zmq.send_string('getMessagesStringInternal()', flags=zmq.NOBLOCK)
        error_raw = self._omc_zmq.recv_string()
        # run error handling only if there is something to check
        msg_long_list = []
        has_error = False
        if error_raw != "{}\n":
            if not self._re_log_entries:
                self._re_log_entries = re.compile(pattern=r'record OpenModelica\.Scripting\.ErrorMessage'
                                                          '(.*?)'
                                                          r'end OpenModelica\.Scripting\.ErrorMessage;',
                                                  flags=re.MULTILINE | re.DOTALL)
            if not self._re_log_raw:
                self._re_log_raw = re.compile(
                    pattern=r"\s*info = record OpenModelica\.Scripting\.SourceInfo\n"
                            r"\s*filename = \"(.*?)\",\n"
                            r"\s*readonly = (.*?),\n"
                            r"\s*lineStart = (\d+),\n"
                            r"\s*columnStart = (\d+),\n"
                            r"\s*lineEnd = (\d+),\n"
                            r"\s*columnEnd = (\d+)\n"
                            r"\s*end OpenModelica\.Scripting\.SourceInfo;,\n"
                            r"\s*message = \"(.*?)\",\n"  # message
                            r"\s*kind = \.OpenModelica\.Scripting\.ErrorKind\.(.*?),\n"  # kind
                            r"\s*level = \.OpenModelica\.Scripting\.ErrorLevel\.(.*?),\n"  # level
                            r"\s*id = (\d+)",  # id
                    flags=re.MULTILINE | re.DOTALL)

            # extract all ErrorMessage records
            log_entries = self._re_log_entries.findall(string=error_raw)
            for log_entry in reversed(log_entries):
                log_raw = self._re_log_raw.findall(string=log_entry)
                if len(log_raw) != 1 or len(log_raw[0]) != 10:
                    logger.warning("Invalid ErrorMessage record returned by 'getMessagesStringInternal()':"
                                   f" {repr(log_entry)}!")
                    continue

                log_filename = log_raw[0][0]
                log_readonly = log_raw[0][1]
                log_lstart = log_raw[0][2]
                log_cstart = log_raw[0][3]
                log_lend = log_raw[0][4]
                log_cend = log_raw[0][5]
                log_message = log_raw[0][6].encode().decode('unicode_escape')
                log_kind = log_raw[0][7]
                log_level = log_raw[0][8]
                log_id = log_raw[0][9]

                msg_short = (f"[OMC log for 'sendExpression(expr={expr}, parsed={parsed})']: "
                             f"[{log_kind}:{log_level}:{log_id}] {log_message}")

                # response according to the used log level
                # see: https://build.openmodelica.org/Documentation/OpenModelica.Scripting.ErrorLevel.html
                if log_level == 'error':
                    logger.error(msg_short)
                    has_error = True
                elif log_level == 'warning':
                    logger.warning(msg_short)
                elif log_level == 'notification':
                    logger.info(msg_short)
                else:  # internal
                    logger.debug(msg_short)

                # track all messages such that this list can be reported if an error occurred
                msg_long = (f"[{log_kind}:{log_level}:{log_id}] "
                            f"[{log_filename}:{log_readonly}:{log_lstart}:{log_cstart}:{log_lend}:{log_cend}] "
                            f"{log_message}")
                msg_long_list.append(msg_long)
            if has_error:
                msg_long_str = '\n'.join(f"{idx:02d}: {msg}" for idx, msg in enumerate(msg_long_list))
                raise OMSessionException(f"OMC error occurred for 'sendExpression(expr={expr}, parsed={parsed}):\n"
                                         f"{msg_long_str}")

        if not parsed:
            return result

        try:
            return om_parser_typed(result)
        except pyparsing.ParseException as ex1:
            logger.warning('OMTypedParser error: %s. Returning the basic parser result.', ex1.msg)
            try:
                return om_parser_basic(result)
            except (TypeError, UnboundLocalError) as ex2:
                raise OMSessionException("Cannot parse OMC result") from ex2

    def get_port(self) -> Optional[str]:
        """
        Get the port to connect to the OMC session.
        """
        if not isinstance(self._omc_port, str):
            raise OMSessionException(f"Invalid port to connect to OMC process: {self._omc_port}")
        return self._omc_port

    def get_log(self) -> str:
        """
        Get the log file content of the OMC session.
        """
        if self._omc_loghandle is None:
            raise OMSessionException("Log file not available!")

        self._omc_loghandle.seek(0)
        log = self._omc_loghandle.read()

        return log

    def _get_portfile_path(self) -> Optional[pathlib.Path]:
        omc_log = self.get_log()

        portfile = self._re_portfile_path.findall(string=omc_log)

        portfile_path = None
        if portfile:
            portfile_path = pathlib.Path(portfile[-1][0])

        return portfile_path


class OMCSessionPort(OMCSessionABC):
    """
    OMCSession implementation which uses a port to connect to an already running OMC server.
    """

    def __init__(
            self,
            omc_port: str,
            timeout: float = 10.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self._omc_port = omc_port


class OMCSessionLocal(OMCSessionABC):
    """
    OMCSession implementation which runs the OMC server locally on the machine (Linux / Windows).
    """

    def __init__(
            self,
            timeout: float = 10.00,
            omhome: Optional[str | os.PathLike] = None,
    ) -> None:

        super().__init__(timeout=timeout)

        self.model_execution_local = True

        # where to find OpenModelica
        self._omhome = self._omc_home_get(omhome=omhome)
        # start up omc executable, which is waiting for the ZMQ connection
        self._omc_process = self._omc_process_get()
        # connect to the running omc instance using ZMQ
        self._omc_port = self._omc_port_get()

    @staticmethod
    def _omc_home_get(omhome: Optional[str | os.PathLike] = None) -> pathlib.Path:
        # use the provided path
        if omhome is not None:
            return pathlib.Path(omhome)

        # check the environment variable
        omhome = os.environ.get('OPENMODELICAHOME')
        if omhome is not None:
            return pathlib.Path(omhome)

        # Get the path to the OMC executable, if not installed this will be None
        path_to_omc = shutil.which("omc")
        if path_to_omc is not None:
            return pathlib.Path(path_to_omc).parents[1]

        raise OMSessionException("Cannot find OpenModelica executable, please install from openmodelica.org")

    def _omc_process_get(self) -> subprocess.Popen:
        my_env = os.environ.copy()
        my_env["PATH"] = (self._omhome / "bin").as_posix() + os.pathsep + my_env["PATH"]

        omc_command = [
            (self._omhome / "bin" / "omc").as_posix(),
            "--locale=C",
            "--interactive=zmq",
            f"-z={self._random_string}"]

        omc_process = subprocess.Popen(omc_command,
                                       stdout=self._omc_loghandle,
                                       stderr=self._omc_loghandle,
                                       env=my_env)
        return omc_process

    def _omc_port_get(self) -> str:
        port = None

        # See if the omc server is running
        loop = self._timeout_loop(timestep=0.1)
        while next(loop):
            omc_portfile_path = self._get_portfile_path()
            if omc_portfile_path is not None and omc_portfile_path.is_file():
                # Read the port file
                with open(file=omc_portfile_path, mode='r', encoding="utf-8") as f_p:
                    port = f_p.readline()
                break
            if port is not None:
                break
        else:
            logger.error(f"OMC server did not start. Log-file says:\n{self.get_log()}")
            raise OMSessionException(f"OMC Server did not start (timeout={self._timeout}, "
                                     f"logfile={repr(self._omc_logfile)}).")

        logger.info(f"Local OMC Server is up and running at ZMQ port {port} "
                    f"pid={self._omc_process.pid if isinstance(self._omc_process, subprocess.Popen) else '?'}")

        return port


class OMCSessionZMQ(OMSessionABC):
    """
    This class is a compatibility layer for the new schema using OMCSession* classes.
    """

    def __init__(
            self,
            timeout: float = 10.00,
            omhome: Optional[str] = None,
            omc_process: Optional[OMCSessionABC] = None,
    ) -> None:
        """
        Initialisation for OMCSessionZMQ
        """
        warnings.warn(message="The class OMCSessionZMQ is depreciated and will be removed in future versions; "
                              "please use OMCProcess* classes instead!",
                      category=DeprecationWarning,
                      stacklevel=2)

        if omc_process is None:
            omc_process = OMCSessionLocal(omhome=omhome, timeout=timeout)
        elif not isinstance(omc_process, OMCSessionABC):
            raise OMSessionException("Invalid definition of the OMC process!")
        self.omc_process = omc_process

        super().__init__(timeout=timeout)

    def __del__(self):
        if hasattr(self, 'omc_process'):
            del self.omc_process

    @staticmethod
    def escape_str(value: str) -> str:
        """
        Escape a string such that it can be used as string within OMC expressions, i.e. escape all double quotes.
        """
        return OMCSessionABC.escape_str(value=value)

    def omcpath(self, *path) -> OMPathABC:
        """
        Create an OMCPath object based on the given path segments and the current OMC process definition.
        """
        return self.omc_process.omcpath(*path)

    def omcpath_tempdir(self, tempdir_base: Optional[OMPathABC] = None) -> OMPathABC:
        """
        Get a temporary directory using OMC. It is our own implementation as non-local usage relies on OMC to run all
        filesystem related access.
        """
        return self.omc_process.omcpath_tempdir(tempdir_base=tempdir_base)

    def execute(self, command: str):
        return self.omc_process.execute(command=command)

    def sendExpression(self, command: str, parsed: bool = True) -> Any:
        """
        Send an expression to the OMC server and return the result.

        The complete error handling of the OMC result is done within this method using '"getMessagesStringInternal()'.
        Caller should only check for OMCSessionException.
        """
        return self.omc_process.sendExpression(expr=command, parsed=parsed)

    def get_version(self) -> str:
        return self.omc_process.get_version()

    def model_execution_prefix(self, cwd: Optional[OMPathABC] = None) -> list[str]:
        return self.omc_process.model_execution_prefix(cwd=cwd)

    def set_workdir(self, workdir: OMPathABC) -> None:
        return self.omc_process.set_workdir(workdir=workdir)


class OMCSessionDockerABC(OMCSessionABC, metaclass=abc.ABCMeta):
    """
    Base class for OMCSession implementations which run the OMC server in a Docker container.
    """

    def __init__(
            self,
            timeout: float = 10.0,
            docker: Optional[str] = None,
            dockerContainer: Optional[str] = None,
            dockerExtraArgs: Optional[list] = None,
            dockerOpenModelicaPath: str | os.PathLike = "omc",
            dockerNetwork: Optional[str] = None,
            port: Optional[int] = None,
    ) -> None:
        super().__init__(timeout=timeout)

        if dockerExtraArgs is None:
            dockerExtraArgs = []

        self._docker_extra_args = dockerExtraArgs
        self._docker_open_modelica_path = pathlib.PurePosixPath(dockerOpenModelicaPath)
        self._docker_network = dockerNetwork
        self._docker_container_id: str
        self._docker_process: Optional[DockerPopen]

        # start up omc executable in docker container waiting for the ZMQ connection
        self._omc_process, self._docker_process, self._docker_container_id = self._docker_omc_start(
            docker_image=docker,
            docker_cid=dockerContainer,
            omc_port=port,
        )
        # connect to the running omc instance using ZMQ
        self._omc_port = self._omc_port_get(docker_cid=self._docker_container_id)
        if port is not None and not self._omc_port.endswith(f":{port}"):
            raise OMSessionException(f"Port mismatch: {self._omc_port} is not using the defined port {port}!")

        self._cmd_prefix = self.model_execution_prefix()

    def _docker_process_get(self, docker_cid: str) -> Optional[DockerPopen]:
        if sys.platform == 'win32':
            raise NotImplementedError("Docker not supported on win32!")

        loop = self._timeout_loop(timestep=0.2)
        while next(loop):
            docker_top = subprocess.check_output(["docker", "top", docker_cid]).decode().strip()
            docker_process = None
            for line in docker_top.split("\n"):
                columns = line.split()
                if self._random_string in line:
                    try:
                        docker_process = DockerPopen(int(columns[1]))
                    except psutil.NoSuchProcess as ex:
                        raise OMSessionException(f"Could not find PID {docker_top} - "
                                                 "is this a docker instance spawned without --pid=host?") from ex
            if docker_process is not None:
                break
        else:
            logger.error(f"Docker did not start. Log-file says:\n{self.get_log()}")
            raise OMSessionException(f"Docker based OMC Server did not start (timeout={self._timeout}).")

        return docker_process

    @abc.abstractmethod
    def _docker_omc_start(
            self,
            docker_image: Optional[str] = None,
            docker_cid: Optional[str] = None,
            omc_port: Optional[int] = None,
    ) -> Tuple[subprocess.Popen, DockerPopen, str]:
        pass

    @staticmethod
    def _getuid() -> int:
        """
        The uid to give to docker.
        On Windows, volumes are mapped with all files are chmod ugo+rwx,
        so uid does not matter as long as it is not the root user.
        """
        # mypy complained about os.getuid() not being available on
        # Windows, hence the type: ignore comment.
        return 1000 if sys.platform == 'win32' else os.getuid()  # type: ignore

    def _omc_port_get(
            self,
            docker_cid: str,
    ) -> str:
        port = None

        if not isinstance(docker_cid, str):
            raise OMSessionException(f"Invalid docker container ID: {docker_cid}")

        # See if the omc server is running
        loop = self._timeout_loop(timestep=0.1)
        while next(loop):
            omc_portfile_path = self._get_portfile_path()
            if omc_portfile_path is not None:
                try:
                    output = subprocess.check_output(args=["docker",
                                                           "exec", docker_cid,
                                                           "cat", omc_portfile_path.as_posix()],
                                                     stderr=subprocess.DEVNULL)
                    port = output.decode().strip()
                except subprocess.CalledProcessError:
                    pass
            if port is not None:
                break
        else:
            logger.error(f"Docker did not start. Log-file says:\n{self.get_log()}")
            raise OMSessionException(f"Docker based OMC Server did not start (timeout={self._timeout}, "
                                     f"logfile={repr(self._omc_logfile)}).")

        logger.info(f"Docker based OMC Server is up and running at port {port}")

        return port

    def get_server_address(self) -> Optional[str]:
        """
        Get the server address of the OMC server running in a Docker container.
        """
        if self._docker_network == "separate" and isinstance(self._docker_container_id, str):
            output = subprocess.check_output(["docker", "inspect", self._docker_container_id]).decode().strip()
            address = json.loads(output)[0]["NetworkSettings"]["IPAddress"]
            if not isinstance(address, str):
                raise OMSessionException(f"Invalid docker server address: {address}!")
            return address

        return None

    def get_docker_container_id(self) -> str:
        """
        Get the Docker container ID of the Docker container with the OMC server.
        """
        if not isinstance(self._docker_container_id, str):
            raise OMSessionException(f"Invalid docker container ID: {self._docker_container_id}!")

        return self._docker_container_id

    def model_execution_prefix(self, cwd: Optional[OMPathABC] = None) -> list[str]:
        """
        Helper function which returns a command prefix needed for docker and WSL. It defaults to an empty list.
        """
        docker_cmd = [
            "docker", "exec",
            "--user", str(self._getuid()),
        ]
        if isinstance(cwd, OMPathABC):
            docker_cmd += ["--workdir", cwd.as_posix()]
        docker_cmd += self._docker_extra_args
        if isinstance(self._docker_container_id, str):
            docker_cmd += [self._docker_container_id]

        return docker_cmd


class OMCSessionDocker(OMCSessionDockerABC):
    """
    OMC process running in a Docker container.
    """

    def __init__(
            self,
            timeout: float = 10.00,
            docker: Optional[str] = None,
            dockerExtraArgs: Optional[list] = None,
            dockerOpenModelicaPath: str | os.PathLike = "omc",
            dockerNetwork: Optional[str] = None,
            port: Optional[int] = None,
    ) -> None:

        super().__init__(
            timeout=timeout,
            docker=docker,
            dockerExtraArgs=dockerExtraArgs,
            dockerOpenModelicaPath=dockerOpenModelicaPath,
            dockerNetwork=dockerNetwork,
            port=port,
        )

    def __del__(self) -> None:

        if hasattr(self, '_docker_process') and isinstance(self._docker_process, DockerPopen):
            try:
                self._docker_process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                if self._docker_process:
                    logger.warning("OMC did not exit after being sent the quit() command; "
                                   "killing the process with pid=%s", self._docker_process.pid)
                    self._docker_process.kill()
                    self._docker_process.wait(timeout=2.0)
            finally:
                self._docker_process = None

        super().__del__()

    def _docker_omc_cmd(
            self,
            docker_image: str,
            docker_cid_file: pathlib.Path,
            omc_path_and_args_list: list[str],
            omc_port: Optional[int | str] = None,
    ) -> list:
        """
        Define the command that will be called by the subprocess module.
        """

        extra_flags = []

        if sys.platform == "win32":
            extra_flags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            if not self._omc_port:
                raise OMSessionException("Docker on Windows requires knowing which port to connect to - "
                                         "please set the interactivePort argument")

        port: Optional[int] = None
        if isinstance(omc_port, str):
            port = int(omc_port)
        elif isinstance(omc_port, int):
            port = omc_port

        if sys.platform == "win32":
            if not isinstance(port, int):
                raise OMSessionException("OMC on Windows needs the interactive port - "
                                         f"missing or invalid value: {repr(omc_port)}!")
            docker_network_str = ["-p", f"127.0.0.1:{port}:{port}"]
        elif self._docker_network == "host" or self._docker_network is None:
            docker_network_str = ["--network=host"]
        elif self._docker_network == "separate":
            docker_network_str = []
            extra_flags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
        else:
            raise OMSessionException(f'dockerNetwork was set to {self._docker_network}, '
                                     'but only \"host\" or \"separate\" is allowed')

        if isinstance(port, int):
            extra_flags = extra_flags + [f"--interactivePort={port}"]

        omc_command = ([
                           "docker", "run",
                           "--cidfile", docker_cid_file.as_posix(),
                           "--rm",
                           "--user", str(self._getuid()),
                       ]
                       + self._docker_extra_args
                       + docker_network_str
                       + [docker_image, self._docker_open_modelica_path.as_posix()]
                       + omc_path_and_args_list
                       + extra_flags)

        return omc_command

    def _docker_omc_start(
            self,
            docker_image: Optional[str] = None,
            docker_cid: Optional[str] = None,
            omc_port: Optional[int] = None,
    ) -> Tuple[subprocess.Popen, DockerPopen, str]:

        if not isinstance(docker_image, str):
            raise OMSessionException("A docker image name must be provided!")

        my_env = os.environ.copy()

        docker_cid_file = self._temp_dir / (self._omc_filebase + ".docker.cid")

        omc_command = self._docker_omc_cmd(
            docker_image=docker_image,
            docker_cid_file=docker_cid_file,
            omc_path_and_args_list=["--locale=C",
                                    "--interactive=zmq",
                                    f"-z={self._random_string}"],
            omc_port=omc_port,
        )

        omc_process = subprocess.Popen(omc_command,
                                       stdout=self._omc_loghandle,
                                       stderr=self._omc_loghandle,
                                       env=my_env)

        if not isinstance(docker_cid_file, pathlib.Path):
            raise OMSessionException(f"Invalid content for docker container ID file path: {docker_cid_file}")

        # the provided value for docker_cid is not used
        docker_cid = None
        loop = self._timeout_loop(timestep=0.1)
        while next(loop):
            try:
                with open(file=docker_cid_file, mode="r", encoding="utf-8") as fh:
                    docker_cid = fh.read().strip()
            except IOError:
                pass
            if docker_cid is not None:
                break
            time.sleep(self._timeout / 40.0)

        if docker_cid is None:
            raise OMSessionException(f"Docker did not start (timeout={self._timeout} might be too short "
                                     "especially if you did not docker pull the image before this command). "
                                     f"Log-file says:\n{self.get_log()}")

        docker_process = self._docker_process_get(docker_cid=docker_cid)
        if docker_process is None:
            logger.error(f"Docker did not start. Log-file says:\n{self.get_log()}")
            raise OMSessionException(f"Docker top did not contain omc process {self._random_string}.")

        return omc_process, docker_process, docker_cid


class OMCSessionDockerContainer(OMCSessionDockerABC):
    """
    OMC process running in a Docker container (by container ID).
    """

    def __init__(
            self,
            timeout: float = 10.00,
            dockerContainer: Optional[str] = None,
            dockerExtraArgs: Optional[list] = None,
            dockerOpenModelicaPath: str | os.PathLike = "omc",
            dockerNetwork: Optional[str] = None,
            port: Optional[int] = None,
    ) -> None:

        super().__init__(
            timeout=timeout,
            dockerContainer=dockerContainer,
            dockerExtraArgs=dockerExtraArgs,
            dockerOpenModelicaPath=dockerOpenModelicaPath,
            dockerNetwork=dockerNetwork,
            port=port,
        )

    def __del__(self) -> None:

        super().__del__()

        # docker container ID was provided - do NOT kill the docker process!
        self._docker_process = None

    def _docker_omc_cmd(
            self,
            docker_cid: str,
            omc_path_and_args_list: list[str],
            omc_port: Optional[int] = None,
    ) -> list:
        """
        Define the command that will be called by the subprocess module.
        """
        extra_flags: list[str] = []

        if sys.platform == "win32":
            extra_flags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            if not isinstance(omc_port, int):
                raise OMSessionException("Docker on Windows requires knowing which port to connect to - "
                                         "Please set the interactivePort argument. Furthermore, the container needs "
                                         "to have already manually exposed this port when it was started "
                                         "(-p 127.0.0.1:n:n) or you get an error later.")

        if isinstance(omc_port, int):
            extra_flags = extra_flags + [f"--interactivePort={omc_port}"]

        omc_command = ([
                           "docker", "exec",
                           "--user", str(self._getuid()),
                       ]
                       + self._docker_extra_args
                       + [docker_cid, self._docker_open_modelica_path.as_posix()]
                       + omc_path_and_args_list
                       + extra_flags)

        return omc_command

    def _docker_omc_start(
            self,
            docker_image: Optional[str] = None,
            docker_cid: Optional[str] = None,
            omc_port: Optional[int] = None,
    ) -> Tuple[subprocess.Popen, DockerPopen, str]:

        if not isinstance(docker_cid, str):
            raise OMSessionException("A docker container ID must be provided!")

        my_env = os.environ.copy()

        omc_command = self._docker_omc_cmd(
            docker_cid=docker_cid,
            omc_path_and_args_list=["--locale=C",
                                    "--interactive=zmq",
                                    f"-z={self._random_string}"],
            omc_port=omc_port,
        )

        omc_process = subprocess.Popen(omc_command,
                                       stdout=self._omc_loghandle,
                                       stderr=self._omc_loghandle,
                                       env=my_env)

        docker_process = None
        if isinstance(docker_cid, str):
            docker_process = self._docker_process_get(docker_cid=docker_cid)

        if docker_process is None:
            raise OMSessionException(f"Docker top did not contain omc process {self._random_string} "
                                     f"/ {docker_cid}. Log-file says:\n{self.get_log()}")

        return omc_process, docker_process, docker_cid


class OMCSessionWSL(OMCSessionABC):
    """
    OMC process running in Windows Subsystem for Linux (WSL).
    """

    def __init__(
            self,
            timeout: float = 10.00,
            wsl_omc: str = 'omc',
            wsl_distribution: Optional[str] = None,
            wsl_user: Optional[str] = None,
    ) -> None:

        super().__init__(timeout=timeout)

        # where to find OpenModelica
        self._wsl_omc = wsl_omc
        # store WSL distribution and user
        self._wsl_distribution = wsl_distribution
        self._wsl_user = wsl_user
        # start up omc executable, which is waiting for the ZMQ connection
        self._omc_process = self._omc_process_get()
        # connect to the running omc instance using ZMQ
        self._omc_port = self._omc_port_get()

        self._cmd_prefix = self.model_execution_prefix()

    def model_execution_prefix(self, cwd: Optional[OMPathABC] = None) -> list[str]:
        """
        Helper function which returns a command prefix needed for docker and WSL. It defaults to an empty list.
        """
        # get wsl base command
        wsl_cmd = ['wsl']
        if isinstance(self._wsl_distribution, str):
            wsl_cmd += ['--distribution', self._wsl_distribution]
        if isinstance(self._wsl_user, str):
            wsl_cmd += ['--user', self._wsl_user]
        if isinstance(cwd, OMPathABC):
            wsl_cmd += ['--cd', cwd.as_posix()]
        wsl_cmd += ['--']

        return wsl_cmd

    def _omc_process_get(self) -> subprocess.Popen:
        my_env = os.environ.copy()

        omc_command = self.model_execution_prefix() + [
            self._wsl_omc,
            "--locale=C",
            "--interactive=zmq",
            f"-z={self._random_string}",
        ]

        omc_process = subprocess.Popen(omc_command,
                                       stdout=self._omc_loghandle,
                                       stderr=self._omc_loghandle,
                                       env=my_env)
        return omc_process

    def _omc_port_get(self) -> str:
        port = None

        # See if the omc server is running
        loop = self._timeout_loop(timestep=0.1)
        while next(loop):
            try:
                omc_portfile_path = self._get_portfile_path()
                if omc_portfile_path is not None:
                    output = subprocess.check_output(
                        args=self.model_execution_prefix() + ["cat", omc_portfile_path.as_posix()],
                        stderr=subprocess.DEVNULL,
                    )
                    port = output.decode().strip()
            except subprocess.CalledProcessError:
                pass
            if port is not None:
                break
        else:
            logger.error(f"WSL based OMC server did not start. Log-file says:\n{self.get_log()}")
            raise OMSessionException(f"WSL based OMC Server did not start (timeout={self._timeout}, "
                                     f"logfile={repr(self._omc_logfile)}).")

        logger.info(f"WSL based OMC Server is up and running at ZMQ port {port} "
                    f"pid={self._omc_process.pid if isinstance(self._omc_process, subprocess.Popen) else '?'}")

        return port


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


DummyPopen = DockerPopen
OMCProcessLocal = OMCSessionLocal
OMCProcessPort = OMCSessionPort
OMCProcessDocker = OMCSessionDocker
OMCProcessDockerContainer = OMCSessionDockerContainer
OMCProcessWSL = OMCSessionWSL
