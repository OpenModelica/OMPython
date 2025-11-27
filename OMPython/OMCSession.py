# -*- coding: utf-8 -*-
"""
Definition of an OMC session.
"""

from __future__ import annotations

import abc
import dataclasses
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
from typing import Any, Optional, Tuple
import uuid
import warnings
import zmq

import psutil
import pyparsing

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
        return os.kill(self.pid, signal.SIGKILL)

    def wait(self, timeout):
        try:
            self.process.wait(timeout=timeout)
        except psutil.TimeoutExpired:
            pass


class OMCSessionException(Exception):
    """
    Exception which is raised by any OMC* class.
    """


class OMCSessionCmd:
    """
    Implementation of Open Modelica Compiler API functions. Depreciated!
    """

    def __init__(self, session: OMCSession, readonly: bool = False):
        if not isinstance(session, OMCSession):
            raise OMCSessionException("Invalid OMC process definition!")
        self._session = session
        self._readonly = readonly
        self._omc_cache: dict[tuple[str, bool], Any] = {}

    def _ask(self, question: str, opt: Optional[list[str]] = None, parsed: bool = True):

        if opt is None:
            expression = question
        elif isinstance(opt, list):
            expression = f"{question}({','.join([str(x) for x in opt])})"
        else:
            raise OMCSessionException(f"Invalid definition of options for {repr(question)}: {repr(opt)}")

        p = (expression, parsed)

        if self._readonly and question != 'getErrorString':
            # can use cache if readonly
            if p in self._omc_cache:
                return self._omc_cache[p]

        try:
            res = self._session.sendExpression(expression, parsed=parsed)
        except OMCSessionException as ex:
            raise OMCSessionException(f"OMC _ask() failed: {expression} (parsed={parsed})") from ex

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
        except OMCSessionException:
            raise

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
        except OMCSessionException:
            raise

    def getParameterValue(self, className, parameterName):
        try:
            return self._ask(question='getParameterValue', opt=[className, parameterName])
        except pyparsing.ParseException as ex:
            logger.warning("Method 'getParameterValue(%s, %s)' failed; OMTypedParser error: %s",
                           className, parameterName, ex.msg)
            return ""
        except OMCSessionException:
            raise

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


class OMCPathReal(pathlib.PurePosixPath):
    """
    Implementation of a basic (PurePosix)Path object which uses OMC as backend. The connection to OMC is provided via an
    instances of OMCSession* classes.

    PurePosixPath is selected to cover usage of OMC in docker or via WSL. Usage of specialised function could result in
    errors as well as usage on a Windows system due to slightly different definitions (PureWindowsPath).
    """

    def __init__(self, *path, session: OMCSession) -> None:
        super().__init__(*path)
        self._session = session

    def with_segments(self, *pathsegments):
        """
        Create a new OMCPath object with the given path segments.

        The original definition of Path is overridden to ensure the OMC session is set.
        """
        return type(self)(*pathsegments, session=self._session)

    def is_file(self, *, follow_symlinks=True) -> bool:
        """
        Check if the path is a regular file.
        """
        return self._session.sendExpression(f'regularFileExists("{self.as_posix()}")')

    def is_dir(self, *, follow_symlinks=True) -> bool:
        """
        Check if the path is a directory.
        """
        return self._session.sendExpression(f'directoryExists("{self.as_posix()}")')

    def is_absolute(self):
        """
        Check if the path is an absolute path considering the possibility that we are running locally on Windows. This
        case needs special handling as the definition of is_absolute() differs.
        """
        if isinstance(self._session, OMCSessionLocal) and platform.system() == 'Windows':
            return pathlib.PureWindowsPath(self.as_posix()).is_absolute()
        return super().is_absolute()

    def read_text(self, encoding=None, errors=None, newline=None) -> str:
        """
        Read the content of the file represented by this path as text.

        The additional arguments `encoding`, `errors` and `newline` are only defined for compatibility with Path()
        definition.
        """
        return self._session.sendExpression(f'readFile("{self.as_posix()}")')

    def write_text(self, data: str, encoding=None, errors=None, newline=None):
        """
        Write text data to the file represented by this path.

        The additional arguments `encoding`, `errors`, and `newline` are only defined for compatibility with Path()
        definitions.
        """
        if not isinstance(data, str):
            raise TypeError(f"data must be str, not {data.__class__.__name__}")

        data_omc = self._session.escape_str(data)
        self._session.sendExpression(f'writeFile("{self.as_posix()}", "{data_omc}", false);')

        return len(data)

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """
        Create a directory at the path represented by this OMCPath object.

        The additional arguments `mode`, and `parents` are only defined for compatibility with Path() definitions.
        """
        if self.is_dir() and not exist_ok:
            raise FileExistsError(f"Directory {self.as_posix()} already exists!")

        return self._session.sendExpression(f'mkdir("{self.as_posix()}")')

    def cwd(self):
        """
        Returns the current working directory as an OMCPath object.
        """
        cwd_str = self._session.sendExpression('cd()')
        return OMCPath(cwd_str, session=self._session)

    def unlink(self, missing_ok: bool = False) -> None:
        """
        Unlink (delete) the file or directory represented by this path.
        """
        res = self._session.sendExpression(f'deleteFile("{self.as_posix()}")')
        if not res and not missing_ok:
            raise FileNotFoundError(f"Cannot delete file {self.as_posix()} - it does not exists!")

    def resolve(self, strict: bool = False):
        """
        Resolve the path to an absolute path. This is done based on available OMC functions.
        """
        if strict and not (self.is_file() or self.is_dir()):
            raise OMCSessionException(f"Path {self.as_posix()} does not exist!")

        if self.is_file():
            pathstr_resolved = self._omc_resolve(self.parent.as_posix())
            omcpath_resolved = self._session.omcpath(pathstr_resolved) / self.name
        elif self.is_dir():
            pathstr_resolved = self._omc_resolve(self.as_posix())
            omcpath_resolved = self._session.omcpath(pathstr_resolved)
        else:
            raise OMCSessionException(f"Path {self.as_posix()} is neither a file nor a directory!")

        if not omcpath_resolved.is_file() and not omcpath_resolved.is_dir():
            raise OMCSessionException(f"OMCPath resolve failed for {self.as_posix()} - path does not exist!")

        return omcpath_resolved

    def _omc_resolve(self, pathstr: str) -> str:
        """
        Internal function to resolve the path of the OMCPath object using OMC functions *WITHOUT* changing the cwd
        within OMC.
        """
        expression = ('omcpath_cwd := cd(); '
                      f'omcpath_check := cd("{pathstr}"); '  # check requested pathstring
                      'cd(omcpath_cwd)')

        try:
            result = self._session.sendExpression(command=expression, parsed=False)
            result_parts = result.split('\n')
            pathstr_resolved = result_parts[1]
            pathstr_resolved = pathstr_resolved[1:-1]  # remove quotes
        except OMCSessionException as ex:
            raise OMCSessionException(f"OMCPath resolve failed for {pathstr}!") from ex

        return pathstr_resolved

    def absolute(self):
        """
        Resolve the path to an absolute path. This is done by calling resolve() as it is the best we can do
        using OMC functions.
        """
        return self.resolve(strict=True)

    def exists(self, follow_symlinks=True) -> bool:
        """
        Semi replacement for pathlib.Path.exists().
        """
        return self.is_file() or self.is_dir()

    def size(self) -> int:
        """
        Get the size of the file in bytes - this is an extra function and the best we can do using OMC.
        """
        if not self.is_file():
            raise OMCSessionException(f"Path {self.as_posix()} is not a file!")

        res = self._session.sendExpression(f'stat("{self.as_posix()}")')
        if res[0]:
            return int(res[1])

        raise OMCSessionException(f"Error reading file size for path {self.as_posix()}!")

    def stat(self):
        """
        The function stat() cannot be implemented using OMC.
        """
        raise NotImplementedError("The function stat() cannot be implemented using OMC; "
                                  "use size() to get the file size.")


if sys.version_info < (3, 12):

    class OMCPathCompatibility(pathlib.Path):
        """
        Compatibility class for OMCPath in Python < 3.12. This allows to run all code which uses OMCPath (mainly
        ModelicaSystem) on these Python versions. There is one remaining limitation: only OMCProcessLocal will work as
        OMCPathCompatibility is based on the standard pathlib.Path implementation.
        """

        # modified copy of pathlib.Path.__new__() definition
        def __new__(cls, *args, **kwargs):
            logger.warning("Python < 3.12 - using a version of class OMCPath "
                           "based on pathlib.Path for local usage only.")

            if cls is OMCPathCompatibility:
                cls = OMCPathCompatibilityWindows if os.name == 'nt' else OMCPathCompatibilityPosix
            self = cls._from_parts(args)
            if not self._flavour.is_supported:
                raise NotImplementedError(f"cannot instantiate {cls.__name__} on your system")
            return self

        def size(self) -> int:
            """
            Needed compatibility function to have the same interface as OMCPathReal
            """
            return self.stat().st_size

    class OMCPathCompatibilityPosix(pathlib.PosixPath, OMCPathCompatibility):
        """
        Compatibility class for OMCPath on Posix systems (Python < 3.12)
        """

    class OMCPathCompatibilityWindows(pathlib.WindowsPath, OMCPathCompatibility):
        """
        Compatibility class for OMCPath on Windows systems (Python < 3.12)
        """

    OMCPath = OMCPathCompatibility

else:
    OMCPath = OMCPathReal


@dataclasses.dataclass
class OMCSessionRunData:
    """
    Data class to store the command line data for running a model executable in the OMC environment.

    All data should be defined for the environment, where OMC is running (local, docker or WSL)

    To use this as a definition of an OMC simulation run, it has to be processed within
    OMCProcess*.omc_run_data_update(). This defines the attribute cmd_model_executable.
    """
    # cmd_path is the expected working directory
    cmd_path: str
    cmd_model_name: str
    # command line arguments for the model executable
    cmd_args: list[str]
    # result file with the simulation output
    cmd_result_path: str

    # command prefix data (as list of strings); needed for docker or WSL
    cmd_prefix: Optional[list[str]] = None
    # cmd_model_executable is build out of cmd_path and cmd_model_name; this is mainly needed on Windows (add *.exe)
    cmd_model_executable: Optional[str] = None
    # additional library search path; this is mainly needed if OMCProcessLocal is run on Windows
    cmd_library_path: Optional[str] = None

    # working directory to be used on the *local* system
    cmd_cwd_local: Optional[str] = None

    def get_cmd(self) -> list[str]:
        """
        Get the command line to run the model executable in the environment defined by the OMCProcess definition.
        """

        if self.cmd_model_executable is None:
            raise OMCSessionException("No model file defined for the model executable!")

        cmdl = [] if self.cmd_prefix is None else self.cmd_prefix
        cmdl += [self.cmd_model_executable] + self.cmd_args

        return cmdl


class OMCSessionZMQ:
    """
    This class is a compatibility layer for the new schema using OMCSession* classes.
    """

    def __init__(
            self,
            timeout: float = 10.00,
            omhome: Optional[str] = None,
            omc_process: Optional[OMCSession] = None,
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
        elif not isinstance(omc_process, OMCSession):
            raise OMCSessionException("Invalid definition of the OMC process!")
        self.omc_process = omc_process

    def __del__(self):
        del self.omc_process

    @staticmethod
    def escape_str(value: str) -> str:
        """
        Escape a string such that it can be used as string within OMC expressions, i.e. escape all double quotes.
        """
        return OMCSession.escape_str(value=value)

    def omcpath(self, *path) -> OMCPath:
        """
        Create an OMCPath object based on the given path segments and the current OMC process definition.
        """
        return self.omc_process.omcpath(*path)

    def omcpath_tempdir(self, tempdir_base: Optional[OMCPath] = None) -> OMCPath:
        """
        Get a temporary directory using OMC. It is our own implementation as non-local usage relies on OMC to run all
        filesystem related access.
        """
        return self.omc_process.omcpath_tempdir(tempdir_base=tempdir_base)

    def omc_run_data_update(self, omc_run_data: OMCSessionRunData) -> OMCSessionRunData:
        """
        Modify data based on the selected OMCProcess implementation.

        Needs to be implemented in the subclasses.
        """
        return self.omc_process.omc_run_data_update(omc_run_data=omc_run_data)

    def run_model_executable(self, cmd_run_data: OMCSessionRunData) -> int:
        """
        Run the command defined in cmd_run_data. This class is defined as static method such that there is no need to
        keep instances of over classes around.
        """
        return self.omc_process.run_model_executable(cmd_run_data=cmd_run_data)

    def execute(self, command: str):
        return self.omc_process.execute(command=command)

    def sendExpression(self, command: str, parsed: bool = True) -> Any:
        """
        Send an expression to the OMC server and return the result.

        The complete error handling of the OMC result is done within this method using '"getMessagesStringInternal()'.
        Caller should only check for OMCSessionException.
        """
        return self.omc_process.sendExpression(command=command, parsed=parsed)


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


class OMCSessionMeta(abc.ABCMeta, PostInitCaller):
    """
    Helper class to get a combined metaclass of ABCMeta and PostInitCaller.

    References:
    * https://stackoverflow.com/questions/11276037/resolving-metaclass-conflicts
    """


class OMCSession(metaclass=OMCSessionMeta):
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

        # store variables
        self._timeout = timeout
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
        logfile = self._temp_dir / (self._omc_filebase + ".log")
        self._omc_loghandle: Optional[io.TextIOWrapper] = None
        try:
            self._omc_loghandle = open(file=logfile, mode="w+", encoding="utf-8")
        except OSError as ex:
            raise OMCSessionException(f"Cannot open log file {logfile}.") from ex

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
            raise OMCSessionException(f"Invalid content for port: {port}")

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
                self.sendExpression("quit()")
            except OMCSessionException as exc:
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
            raise OMCSessionException(f"Invalid timeout: {timeout}")

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
                raise OMCSessionException(f"Invalid timeout value: {timeout}!")
            self._timeout = timeout
        return retval

    @staticmethod
    def escape_str(value: str) -> str:
        """
        Escape a string such that it can be used as string within OMC expressions, i.e. escape all double quotes.
        """
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def omcpath(self, *path) -> OMCPath:
        """
        Create an OMCPath object based on the given path segments and the current OMCSession* class.
        """

        # fallback solution for Python < 3.12; a modified pathlib.Path object is used as OMCPath replacement
        if sys.version_info < (3, 12):
            if isinstance(self, OMCSessionLocal):
                # noinspection PyArgumentList
                return OMCPath(*path)
            raise OMCSessionException("OMCPath is supported for Python < 3.12 only if OMCSessionLocal is used!")
        return OMCPath(*path, session=self)

    def omcpath_tempdir(self, tempdir_base: Optional[OMCPath] = None) -> OMCPath:
        """
        Get a temporary directory using OMC. It is our own implementation as non-local usage relies on OMC to run all
        filesystem related access.
        """
        names = [str(uuid.uuid4()) for _ in range(100)]

        if tempdir_base is None:
            # fallback solution for Python < 3.12; a modified pathlib.Path object is used as OMCPath replacement
            if sys.version_info < (3, 12):
                tempdir_str = tempfile.gettempdir()
            else:
                tempdir_str = self.sendExpression("getTempDirectoryPath()")
            tempdir_base = self.omcpath(tempdir_str)

        tempdir: Optional[OMCPath] = None
        for name in names:
            # create a unique temporary directory name
            tempdir = tempdir_base / name

            if tempdir.exists():
                continue

            tempdir.mkdir(parents=True, exist_ok=False)
            break

        if tempdir is None or not tempdir.is_dir():
            raise OMCSessionException("Cannot create a temporary directory!")

        return tempdir

    def run_model_executable(self, cmd_run_data: OMCSessionRunData) -> int:
        """
        Run the command defined in cmd_run_data.
        """

        my_env = os.environ.copy()
        if isinstance(cmd_run_data.cmd_library_path, str):
            my_env["PATH"] = cmd_run_data.cmd_library_path + os.pathsep + my_env["PATH"]

        cmdl = cmd_run_data.get_cmd()

        logger.debug("Run OM command %s in %s", repr(cmdl), cmd_run_data.cmd_path)
        try:
            cmdres = subprocess.run(
                cmdl,
                capture_output=True,
                text=True,
                env=my_env,
                cwd=cmd_run_data.cmd_cwd_local,
                timeout=self._timeout,
                check=True,
            )
            stdout = cmdres.stdout.strip()
            stderr = cmdres.stderr.strip()
            returncode = cmdres.returncode

            logger.debug("OM output for command %s:\n%s", repr(cmdl), stdout)

            if stderr:
                raise OMCSessionException(f"Error running model executable {repr(cmdl)}: {stderr}")
        except subprocess.TimeoutExpired as ex:
            raise OMCSessionException(f"Timeout running model executable {repr(cmdl)}") from ex
        except subprocess.CalledProcessError as ex:
            raise OMCSessionException(f"Error running model executable {repr(cmdl)}") from ex

        return returncode

    def execute(self, command: str):
        warnings.warn(message="This function is depreciated and will be removed in future versions; "
                              "please use sendExpression() instead",
                      category=DeprecationWarning,
                      stacklevel=2)

        return self.sendExpression(command, parsed=False)

    def sendExpression(self, command: str, parsed: bool = True) -> Any:
        """
        Send an expression to the OMC server and return the result.

        The complete error handling of the OMC result is done within this method using '"getMessagesStringInternal()'.
        Caller should only check for OMCSessionException.
        """

        if self._omc_zmq is None:
            raise OMCSessionException("No OMC running. Please create a new instance of OMCSession!")

        logger.debug("sendExpression(%r, parsed=%r)", command, parsed)

        loop = self._timeout_loop(timestep=0.05)
        while next(loop):
            try:
                self._omc_zmq.send_string(str(command), flags=zmq.NOBLOCK)
                break
            except zmq.error.Again:
                pass
        else:
            # in the deletion process, the content is cleared. Thus, any access to a class attribute must be checked
            try:
                log_content = self.get_log()
            except OMCSessionException:
                log_content = 'log not available'

            logger.error(f"Docker did not start. Log-file says:\n{log_content}")
            raise OMCSessionException(f"No connection with OMC (timeout={self._timeout}).")

        if command == "quit()":
            self._omc_zmq.close()
            self._omc_zmq = None
            return None

        result = self._omc_zmq.recv_string()

        if result.startswith('Error occurred building AST'):
            raise OMCSessionException(f"OMC error: {result}")

        if command == "getErrorString()":
            # no error handling if 'getErrorString()' is called
            if parsed:
                logger.warning("Result of 'getErrorString()' cannot be parsed!")
            return result

        if command == "getMessagesStringInternal()":
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

                msg_short = (f"[OMC log for 'sendExpression({command}, {parsed})']: "
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
                raise OMCSessionException(f"OMC error occurred for 'sendExpression({command}, {parsed}):\n"
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
                raise OMCSessionException("Cannot parse OMC result") from ex2

    def get_port(self) -> Optional[str]:
        """
        Get the port to connect to the OMC session.
        """
        if not isinstance(self._omc_port, str):
            raise OMCSessionException(f"Invalid port to connect to OMC process: {self._omc_port}")
        return self._omc_port

    def get_log(self) -> str:
        """
        Get the log file content of the OMC session.
        """
        if self._omc_loghandle is None:
            raise OMCSessionException("Log file not available!")

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

    @abc.abstractmethod
    def omc_run_data_update(self, omc_run_data: OMCSessionRunData) -> OMCSessionRunData:
        """
        Update the OMCSessionRunData object based on the selected OMCSession implementation.

        The main point is the definition of OMCSessionRunData.cmd_model_executable which contains the specific command
        to run depending on the selected system.

        Needs to be implemented in the subclasses.
        """
        raise NotImplementedError("This method must be implemented in subclasses!")


class OMCSessionPort(OMCSession):
    """
    OMCSession implementation which uses a port to connect to an already running OMC server.
    """

    def __init__(
            self,
            omc_port: str,
    ) -> None:
        super().__init__()
        self._omc_port = omc_port

    @staticmethod
    def run_model_executable(cmd_run_data: OMCSessionRunData) -> int:
        """
        Run the command defined in cmd_run_data. This class is defined as static method such that there is no need to
        keep instances of over classes around.
        """
        raise OMCSessionException("OMCSessionPort does not support run_model_executable()!")

    def get_log(self) -> str:
        """
        Get the log file content of the OMC session.
        """
        log = f"No log available if OMC session is defined by port ({self.__class__.__name__})"

        return log

    def omc_run_data_update(self, omc_run_data: OMCSessionRunData) -> OMCSessionRunData:
        """
        Update the OMCSessionRunData object based on the selected OMCSession implementation.
        """
        raise OMCSessionException(f"({self.__class__.__name__}) does not support omc_run_data_update()!")


class OMCSessionLocal(OMCSession):
    """
    OMCSession implementation which runs the OMC server locally on the machine (Linux / Windows).
    """

    def __init__(
            self,
            timeout: float = 10.00,
            omhome: Optional[str | os.PathLike] = None,
    ) -> None:

        super().__init__(timeout=timeout)

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

        raise OMCSessionException("Cannot find OpenModelica executable, please install from openmodelica.org")

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
            logger.error(f"Docker did not start. Log-file says:\n{self.get_log()}")
            raise OMCSessionException(f"OMC Server did not start (timeout={self._timeout}).")

        logger.info(f"Local OMC Server is up and running at ZMQ port {port} "
                    f"pid={self._omc_process.pid if isinstance(self._omc_process, subprocess.Popen) else '?'}")

        return port

    def omc_run_data_update(self, omc_run_data: OMCSessionRunData) -> OMCSessionRunData:
        """
        Update the OMCSessionRunData object based on the selected OMCSession implementation.
        """
        # create a copy of the data
        omc_run_data_copy = dataclasses.replace(omc_run_data)

        # as this is the local implementation, pathlib.Path can be used
        cmd_path = pathlib.Path(omc_run_data_copy.cmd_path)

        if platform.system() == "Windows":
            path_dll = ""

            # set the process environment from the generated .bat file in windows which should have all the dependencies
            path_bat = cmd_path / f"{omc_run_data.cmd_model_name}.bat"
            if not path_bat.is_file():
                raise OMCSessionException("Batch file (*.bat) does not exist " + str(path_bat))

            content = path_bat.read_text(encoding='utf-8')
            for line in content.splitlines():
                match = re.match(r"^SET PATH=([^%]*)", line, re.IGNORECASE)
                if match:
                    path_dll = match.group(1).strip(';')  # Remove any trailing semicolons
            my_env = os.environ.copy()
            my_env["PATH"] = path_dll + os.pathsep + my_env["PATH"]

            omc_run_data_copy.cmd_library_path = path_dll

            cmd_model_executable = cmd_path / f"{omc_run_data_copy.cmd_model_name}.exe"
        else:
            # for Linux the paths to the needed libraries should be included in the executable (using rpath)
            cmd_model_executable = cmd_path / omc_run_data_copy.cmd_model_name

        if not cmd_model_executable.is_file():
            raise OMCSessionException(f"Application file path not found: {cmd_model_executable}")
        omc_run_data_copy.cmd_model_executable = cmd_model_executable.as_posix()

        # define local(!) working directory
        omc_run_data_copy.cmd_cwd_local = omc_run_data.cmd_path

        return omc_run_data_copy


class OMCSessionDockerHelper(OMCSession):
    """
    Base class for OMCSession implementations which run the OMC server in a Docker container.
    """

    def __init__(
            self,
            timeout: float = 10.00,
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

        self._interactive_port = port

        self._docker_container_id: Optional[str] = None
        self._docker_process: Optional[DockerPopen] = None

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
                        raise OMCSessionException(f"Could not find PID {docker_top} - "
                                                  "is this a docker instance spawned without --pid=host?") from ex
            if docker_process is not None:
                break
        else:
            logger.error(f"Docker did not start. Log-file says:\n{self.get_log()}")
            raise OMCSessionException(f"Docker based OMC Server did not start (timeout={self._timeout}).")

        return docker_process

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

    def _omc_port_get(self) -> str:
        port = None

        if not isinstance(self._docker_container_id, str):
            raise OMCSessionException(f"Invalid docker container ID: {self._docker_container_id}")

        # See if the omc server is running
        loop = self._timeout_loop(timestep=0.1)
        while next(loop):
            omc_portfile_path = self._get_portfile_path()
            if omc_portfile_path is not None:
                try:
                    output = subprocess.check_output(args=["docker",
                                                           "exec", self._docker_container_id,
                                                           "cat", omc_portfile_path.as_posix()],
                                                     stderr=subprocess.DEVNULL)
                    port = output.decode().strip()
                except subprocess.CalledProcessError:
                    pass
            if port is not None:
                break
        else:
            logger.error(f"Docker did not start. Log-file says:\n{self.get_log()}")
            raise OMCSessionException(f"Docker based OMC Server did not start (timeout={self._timeout}).")

        logger.info(f"Docker based OMC Server is up and running at port {port}")

        return port

    def get_server_address(self) -> Optional[str]:
        """
        Get the server address of the OMC server running in a Docker container.
        """
        if self._docker_network == "separate" and isinstance(self._docker_container_id, str):
            output = subprocess.check_output(["docker", "inspect", self._docker_container_id]).decode().strip()
            return json.loads(output)[0]["NetworkSettings"]["IPAddress"]

        return None

    def get_docker_container_id(self) -> str:
        """
        Get the Docker container ID of the Docker container with the OMC server.
        """
        if not isinstance(self._docker_container_id, str):
            raise OMCSessionException(f"Invalid docker container ID: {self._docker_container_id}!")

        return self._docker_container_id

    def omc_run_data_update(self, omc_run_data: OMCSessionRunData) -> OMCSessionRunData:
        """
        Update the OMCSessionRunData object based on the selected OMCSession implementation.
        """
        omc_run_data_copy = dataclasses.replace(omc_run_data)

        omc_run_data_copy.cmd_prefix = (
                [
                    "docker", "exec",
                    "--user", str(self._getuid()),
                    "--workdir", omc_run_data_copy.cmd_path,
                ]
                + self._docker_extra_args
                + [self._docker_container_id]
        )

        cmd_path = pathlib.PurePosixPath(omc_run_data_copy.cmd_path)
        cmd_model_executable = cmd_path / omc_run_data_copy.cmd_model_name
        omc_run_data_copy.cmd_model_executable = cmd_model_executable.as_posix()

        return omc_run_data_copy


class OMCSessionDocker(OMCSessionDockerHelper):
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
            dockerExtraArgs=dockerExtraArgs,
            dockerOpenModelicaPath=dockerOpenModelicaPath,
            dockerNetwork=dockerNetwork,
            port=port,
        )

        if docker is None:
            raise OMCSessionException("Argument docker must be set!")

        self._docker = docker

        # start up omc executable in docker container waiting for the ZMQ connection
        self._omc_process, self._docker_process, self._docker_container_id = self._docker_omc_start()
        # connect to the running omc instance using ZMQ
        self._omc_port = self._omc_port_get()

    def __del__(self) -> None:

        super().__del__()

        if isinstance(self._docker_process, DockerPopen):
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

    def _docker_omc_cmd(
            self,
            omc_path_and_args_list: list[str],
            docker_cid_file: pathlib.Path,
    ) -> list:
        """
        Define the command that will be called by the subprocess module.
        """
        extra_flags = []

        if sys.platform == "win32":
            extra_flags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            if not self._interactive_port:
                raise OMCSessionException("docker on Windows requires knowing which port to connect to - "
                                          "please set the interactivePort argument")

        if sys.platform == "win32":
            if isinstance(self._interactive_port, str):
                port = int(self._interactive_port)
            elif isinstance(self._interactive_port, int):
                port = self._interactive_port
            else:
                raise OMCSessionException("Missing or invalid interactive port!")
            docker_network_str = ["-p", f"127.0.0.1:{port}:{port}"]
        elif self._docker_network == "host" or self._docker_network is None:
            docker_network_str = ["--network=host"]
        elif self._docker_network == "separate":
            docker_network_str = []
            extra_flags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
        else:
            raise OMCSessionException(f'dockerNetwork was set to {self._docker_network}, '
                                      'but only \"host\" or \"separate\" is allowed')

        if isinstance(self._interactive_port, int):
            extra_flags = extra_flags + [f"--interactivePort={int(self._interactive_port)}"]

        omc_command = ([
                           "docker", "run",
                           "--cidfile", docker_cid_file.as_posix(),
                           "--rm",
                           "--user", str(self._getuid()),
                       ]
                       + self._docker_extra_args
                       + docker_network_str
                       + [self._docker, self._docker_open_modelica_path.as_posix()]
                       + omc_path_and_args_list
                       + extra_flags)

        return omc_command

    def _docker_omc_start(self) -> Tuple[subprocess.Popen, DockerPopen, str]:
        my_env = os.environ.copy()

        docker_cid_file = self._temp_dir / (self._omc_filebase + ".docker.cid")

        omc_command = self._docker_omc_cmd(
            omc_path_and_args_list=["--locale=C",
                                    "--interactive=zmq",
                                    f"-z={self._random_string}"],
            docker_cid_file=docker_cid_file,
        )

        omc_process = subprocess.Popen(omc_command,
                                       stdout=self._omc_loghandle,
                                       stderr=self._omc_loghandle,
                                       env=my_env)

        if not isinstance(docker_cid_file, pathlib.Path):
            raise OMCSessionException(f"Invalid content for docker container ID file path: {docker_cid_file}")

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
        else:
            logger.error(f"Docker did not start. Log-file says:\n{self.get_log()}")
            raise OMCSessionException(f"Docker did not start (timeout={self._timeout} might be too short "
                                      "especially if you did not docker pull the image before this command).")

        docker_process = self._docker_process_get(docker_cid=docker_cid)
        if docker_process is None:
            logger.error(f"Docker did not start. Log-file says:\n{self.get_log()}")
            raise OMCSessionException(f"Docker top did not contain omc process {self._random_string}.")

        return omc_process, docker_process, docker_cid


class OMCSessionDockerContainer(OMCSessionDockerHelper):
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
            dockerExtraArgs=dockerExtraArgs,
            dockerOpenModelicaPath=dockerOpenModelicaPath,
            dockerNetwork=dockerNetwork,
            port=port,
        )

        if not isinstance(dockerContainer, str):
            raise OMCSessionException("Argument dockerContainer must be set!")

        self._docker_container_id = dockerContainer

        # start up omc executable in docker container waiting for the ZMQ connection
        self._omc_process, self._docker_process = self._docker_omc_start()
        # connect to the running omc instance using ZMQ
        self._omc_port = self._omc_port_get()

    def __del__(self) -> None:

        super().__del__()

        # docker container ID was provided - do NOT kill the docker process!
        self._docker_process = None

    def _docker_omc_cmd(self, omc_path_and_args_list) -> list:
        """
        Define the command that will be called by the subprocess module.
        """
        extra_flags: list[str] = []

        if sys.platform == "win32":
            extra_flags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            if not self._interactive_port:
                raise OMCSessionException("Docker on Windows requires knowing which port to connect to - "
                                          "Please set the interactivePort argument. Furthermore, the container needs "
                                          "to have already manually exposed this port when it was started "
                                          "(-p 127.0.0.1:n:n) or you get an error later.")

        if isinstance(self._interactive_port, int):
            extra_flags = extra_flags + [f"--interactivePort={int(self._interactive_port)}"]

        omc_command = ([
                           "docker", "exec",
                           "--user", str(self._getuid()),
                       ]
                       + self._docker_extra_args
                       + [self._docker_container_id, self._docker_open_modelica_path.as_posix()]
                       + omc_path_and_args_list
                       + extra_flags)

        return omc_command

    def _docker_omc_start(self) -> Tuple[subprocess.Popen, DockerPopen]:
        my_env = os.environ.copy()

        omc_command = self._docker_omc_cmd(
            omc_path_and_args_list=["--locale=C",
                                    "--interactive=zmq",
                                    f"-z={self._random_string}"],
        )

        omc_process = subprocess.Popen(omc_command,
                                       stdout=self._omc_loghandle,
                                       stderr=self._omc_loghandle,
                                       env=my_env)

        docker_process = None
        if isinstance(self._docker_container_id, str):
            docker_process = self._docker_process_get(docker_cid=self._docker_container_id)

        if docker_process is None:
            raise OMCSessionException(f"Docker top did not contain omc process {self._random_string} "
                                      f"/ {self._docker_container_id}. Log-file says:\n{self.get_log()}")

        return omc_process, docker_process


class OMCSessionWSL(OMCSession):
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

    def _wsl_cmd(self, wsl_cwd: Optional[str] = None) -> list[str]:
        # get wsl base command
        wsl_cmd = ['wsl']
        if isinstance(self._wsl_distribution, str):
            wsl_cmd += ['--distribution', self._wsl_distribution]
        if isinstance(self._wsl_user, str):
            wsl_cmd += ['--user', self._wsl_user]
        if isinstance(wsl_cwd, str):
            wsl_cmd += ['--cd', wsl_cwd]
        wsl_cmd += ['--']

        return wsl_cmd

    def _omc_process_get(self) -> subprocess.Popen:
        my_env = os.environ.copy()

        omc_command = self._wsl_cmd() + [
            self._wsl_omc,
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
            try:
                omc_portfile_path = self._get_portfile_path()
                if omc_portfile_path is not None:
                    output = subprocess.check_output(
                        args=self._wsl_cmd() + ["cat", omc_portfile_path.as_posix()],
                        stderr=subprocess.DEVNULL,
                    )
                    port = output.decode().strip()
            except subprocess.CalledProcessError:
                pass
            if port is not None:
                break
        else:
            logger.error(f"Docker did not start. Log-file says:\n{self.get_log()}")
            raise OMCSessionException(f"WSL based OMC Server did not start (timeout={self._timeout}).")

        logger.info(f"WSL based OMC Server is up and running at ZMQ port {port} "
                    f"pid={self._omc_process.pid if isinstance(self._omc_process, subprocess.Popen) else '?'}")

        return port

    def omc_run_data_update(self, omc_run_data: OMCSessionRunData) -> OMCSessionRunData:
        """
        Update the OMCSessionRunData object based on the selected OMCSession implementation.
        """
        omc_run_data_copy = dataclasses.replace(omc_run_data)

        omc_run_data_copy.cmd_prefix = self._wsl_cmd(wsl_cwd=omc_run_data.cmd_path)

        cmd_path = pathlib.PurePosixPath(omc_run_data_copy.cmd_path)
        cmd_model_executable = cmd_path / omc_run_data_copy.cmd_model_name
        omc_run_data_copy.cmd_model_executable = cmd_model_executable.as_posix()

        return omc_run_data_copy
