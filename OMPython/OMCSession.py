# -*- coding: utf-8 -*-
"""
Definition of an OMC session.
"""

from __future__ import annotations

__license__ = """
 This file is part of OpenModelica.

 Copyright (c) 1998-CurrentYear, Open Source Modelica Consortium (OSMC),
 c/o Linköpings universitet, Department of Computer and Information Science,
 SE-58183 Linköping, Sweden.

 All rights reserved.

 THIS PROGRAM IS PROVIDED UNDER THE TERMS OF THE BSD NEW LICENSE OR THE
 GPL VERSION 3 LICENSE OR THE OSMC PUBLIC LICENSE (OSMC-PL) VERSION 1.2.
 ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS PROGRAM CONSTITUTES
 RECIPIENT'S ACCEPTANCE OF THE OSMC PUBLIC LICENSE OR THE GPL VERSION 3,
 ACCORDING TO RECIPIENTS CHOICE.

 The OpenModelica software and the OSMC (Open Source Modelica Consortium)
 Public License (OSMC-PL) are obtained from OSMC, either from the above
 address, from the URLs: http://www.openmodelica.org or
 http://www.ida.liu.se/projects/OpenModelica, and in the OpenModelica
 distribution. GNU version 3 is obtained from:
 http://www.gnu.org/copyleft/gpl.html. The New BSD License is obtained from:
 http://www.opensource.org/licenses/BSD-3-Clause.

 This program is distributed WITHOUT ANY WARRANTY; without even the implied
 warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE, EXCEPT AS
 EXPRESSLY SET FORTH IN THE BY RECIPIENT SELECTED SUBSIDIARY LICENSE
 CONDITIONS OF OSMC-PL.
"""

import getpass
import io
import json
import logging
import os
import pathlib
import psutil
import pyparsing
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any, Optional
import uuid
import warnings
import zmq

# TODO: replace this with the new parser
from OMPython.OMTypedParser import parseString as om_parser_typed
from OMPython.OMParser import om_parser_basic

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class DummyPopen:
    def __init__(self, pid):
        self.pid = pid
        self.process = psutil.Process(pid)
        self.returncode = 0

    def poll(self):
        return None if self.process.is_running() else True

    def kill(self):
        return os.kill(self.pid, signal.SIGKILL)

    def wait(self, timeout):
        return self.process.wait(timeout=timeout)


class OMCSessionException(Exception):
    pass


class OMCSessionCmd:

    def __init__(self, session: OMCSessionZMQ, readonly: bool = False):
        if not isinstance(session, OMCSessionZMQ):
            raise OMCSessionException("Invalid session definition!")
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
            raise OMCSessionException("OMC _ask() failed: %s (parsed=%s)", expression, parsed) from ex

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


class OMCSessionZMQ:

    def __init__(self,
                 timeout: float = 10.00,
                 omhome: Optional[str] = None,
                 omc_process: Optional[OMCProcess] = None):

        if omc_process is None:
            omc_process = OMCProcessLocal(omhome=omhome, timeout=timeout)
        elif not isinstance(omc_process, OMCProcess):
            raise OMCSessionException("Invalid definition of the OMC process!")
        self.omc_process = omc_process

        # Create the ZeroMQ socket and connect to OMC server
        context = zmq.Context.instance()
        omc = context.socket(zmq.REQ)
        omc.setsockopt(zmq.LINGER, 0)  # Dismisses pending messages if closed
        omc.setsockopt(zmq.IMMEDIATE, True)  # Queue messages only to completed connections
        omc.connect(self.omc_process.get_port())

        self.omc_zmq = omc

        # variables to store compiled re expressions use in self.sendExpression()
        self._re_log_entries = None
        self._re_log_raw = None

    def __del__(self):
        if self.omc_zmq:
            try:
                self.sendExpression("quit()")
            except OMCSessionException:
                pass

            del self.omc_zmq

        self.omc_zmq = None

    def execute(self, command: str):
        warnings.warn("This function is depreciated and will be removed in future versions; "
                      "please use sendExpression() instead", DeprecationWarning, stacklevel=1)

        return self.sendExpression(command, parsed=False)

    def sendExpression(self, command: str, parsed: bool = True):
        p = self.omc_process.poll()  # check if process is running
        if p is not None:
            raise OMCSessionException("Process Exited, No connection with OMC. Create a new instance of OMCSessionZMQ!")

        if self.omc_zmq is None:
            raise OMCSessionException("No OMC running. Create a new instance of OMCSessionZMQ!")

        logger.debug("sendExpression(%r, parsed=%r)", command, parsed)

        attempts = 0
        while True:
            try:
                self.omc_zmq.send_string(str(command), flags=zmq.NOBLOCK)
                break
            except zmq.error.Again:
                pass
            attempts += 1
            if attempts >= 50:
                self._omc_filehandle_log.seek(0)
                log = self._omc_filehandle_log.read()
                self._omc_filehandle_log.close()
                raise OMCSessionException(f"No connection with OMC (timeout={self._timeout}). Log-file says: \n{log}")
            time.sleep(self._timeout / 50.0)
        if command == "quit()":
            self.omc_zmq.close()
            self.omc_zmq = None
            return None
        else:
            result = self.omc_zmq.recv_string()

            if command == "getErrorString()":
                # no error handling if 'getErrorString()' is called
                pass
            elif command == "getMessagesStringInternal()":
                # no error handling if 'getMessagesStringInternal()' is called; parsing NOT possible!
                if parsed:
                    logger.warning("Result of 'getMessagesStringInternal()' cannot be parsed - set parsed to False!")
                    parsed = False
            else:
                # allways check for error
                self.omc_zmq.send_string('getMessagesStringInternal()', flags=zmq.NOBLOCK)
                error_raw = self.omc_zmq.recv_string()
                # run error handling only if there is something to check
                if error_raw != "{}\n":
                    if not self._re_log_entries:
                        self._re_log_entries = re.compile(pattern=r'record OpenModelica\.Scripting\.ErrorMessage'
                                                                  '(.*?)'
                                                                  r'end OpenModelica\.Scripting\.ErrorMessage;',
                                                          flags=re.MULTILINE | re.DOTALL)
                    if not self._re_log_raw:
                        self._re_log_raw = re.compile(
                            pattern=r"\s+message = \"(.*?)\",\n"  # message
                                    r"\s+kind = .OpenModelica.Scripting.ErrorKind.(.*?),\n"  # kind
                                    r"\s+level = .OpenModelica.Scripting.ErrorLevel.(.*?),\n"  # level
                                    r"\s+id = (.*?)"  # id
                                    "(,\n|\n)",  # end marker
                            flags=re.MULTILINE | re.DOTALL)

                    # extract all ErrorMessage records
                    log_entries = self._re_log_entries.findall(string=error_raw)
                    for log_entry in reversed(log_entries):
                        log_raw = self._re_log_raw.findall(string=log_entry)
                        if len(log_raw) != 1 or len(log_raw[0]) != 5:
                            logger.warning("Invalid ErrorMessage record returned by 'getMessagesStringInternal()':"
                                           f" {repr(log_entry)}!")

                        log_message = log_raw[0][0].encode().decode('unicode_escape')
                        log_kind = log_raw[0][1]
                        log_level = log_raw[0][2]
                        log_id = log_raw[0][3]

                        msg = (f"[OMC log for 'sendExpression({command}, {parsed})']: "
                               f"[{log_kind}:{log_level}:{log_id}] {log_message}")

                        # response according to the used log level
                        # see: https://build.openmodelica.org/Documentation/OpenModelica.Scripting.ErrorLevel.html
                        if log_level == 'error':
                            raise OMCSessionException(msg)
                        elif log_level == 'warning':
                            logger.warning(msg)
                        elif log_level == 'notification':
                            logger.info(msg)
                        else:  # internal
                            logger.debug(msg)

            if parsed is True:
                try:
                    return om_parser_typed(result)
                except pyparsing.ParseException as ex:
                    logger.warning('OMTypedParser error: %s. Returning the basic parser result.', ex.msg)
                    try:
                        return om_parser_basic(result)
                    except (TypeError, UnboundLocalError) as ex:
                        raise OMCSessionException("Cannot parse OMC result") from ex
            else:
                return result


class OMCProcess:

    def __init__(self,
                 timeout: float = 10.00,
                 omhome: Optional[str] = None):

        # store variables
        self._omhome = self._omc_home_get(omhome=omhome)
        self._timeout = timeout

        self._omc_port: Optional[str] = None

    @staticmethod
    def _omc_home_get(omhome: Optional[str] = None):
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

    def get_port(self) -> str:
        if not isinstance(self._omc_port, str):
            raise OMCSessionException(f"Invalid port to connect to OMC process: {self._omc_port}")
        return self._omc_port


class OMCProcessDummy(OMCProcess):

    def __init__(self,
                 omc_port: str):
        super().__init__()
        self._omc_port = omc_port


class OMCProcessLocal(OMCProcess):

    def __init__(self,
                 timeout: float = 10.00,
                 omhome: Optional[str] = None):

        super().__init__(timeout=timeout, omhome=omhome)

        # generate a random string for this session
        self._random_string = uuid.uuid4().hex
        try:
            self._currentUser = getpass.getuser()
            if not self._currentUser:
                self._currentUser = "nobody"
        except KeyError:
            # We are running as a uid not existing in the password database... Pretend we are nobody
            self._currentUser = "nobody"

        # Locating and using the IOR
        self._temp_dir = pathlib.Path(tempfile.gettempdir())
        self._omc_file_port = self._temp_dir / self._filename_port(current_user=self._currentUser,
                                                                   random_str=self._random_string)

        if sys.platform == 'win32':
            filename_log = f"openmodelica.port.{self._random_string}.log"
        else:
            filename_log = f"openmodelica.{self._currentUser}.port.{self._random_string}.log"
        self._omc_file_log = self._temp_dir / filename_log
        # this file must be closed in the destructor
        self._omc_filehandle_log: Optional[io.TextIOWrapper] = None
        try:
            self._omc_filehandle_log = open(self._temp_dir / filename_log, "w+")
        except OSError as ex:
            raise OMCSessionException(f"Cannot open log file {self._omc_file_log}.") from ex

        # set omc executable path and args
        self._omc_command = self._omc_command_get(omc_path_and_args_list=["--locale=C",
                                                                          "--interactive=zmq",
                                                                          f"-z={self._random_string}"])
        # start up omc executable, which is waiting for the ZMQ connection
        self._omc_process = self._omc_process_get(timeout)
        # connect to the running omc instance using ZMQ
        self._omc_port = self._omc_port_get(timeout)

    def __del__(self):
        if self._omc_filehandle_log is not None:
            self._omc_filehandle_log.close()

        try:
            self._omc_process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            if self._omc_process:
                logger.warning("OMC did not exit after being sent the quit() command; "
                               "killing the process with pid=%s", self._omc_process.pid)
                self._omc_process.kill()
                self._omc_process.wait()

    @staticmethod
    def _filename_port(current_user: str, random_str: str) -> str:
        if sys.platform != 'win32':
            filename = f"openmodelica.{current_user}.port.{random_str}"
        else:
            filename = f"openmodelica.port.{random_str}"

        return filename

    def _omc_process_get(self, timeout):  # output?
        my_env = os.environ.copy()

        if sys.platform == 'win32':
            omhome_bin = (self._omhome / "bin").as_posix()
            my_env["PATH"] = omhome_bin + os.pathsep + my_env["PATH"]
        else:
            # set the user environment variable so omc running from wsgi has the same user as OMPython
            my_env["USER"] = self._currentUser

        omc_process = subprocess.Popen(self._omc_command, stdout=self._omc_filehandle_log,
                                       stderr=self._omc_filehandle_log, env=my_env)
        return omc_process

    def _omc_command_get(self, omc_path_and_args_list) -> list:
        """
        Define the command that will be called by the subprocess module.
        """
        omc_command_base = [str(self._omc_path_get())]

        omc_command = omc_command_base + omc_path_and_args_list

        return omc_command

    def _omc_path_get(self) -> pathlib.Path:
        return self._omhome / "bin" / "omc"

    def _omc_port_get(self, timeout) -> str:
        omc_zeromq_uri = "file:///" + self._omc_file_port.as_posix()
        # See if the omc server is running
        attempts = 0
        while True:
            port = self._omc_port_get_main()
            if port is not None:
                break

            attempts += 1
            if attempts == 80.0:
                if self._omc_filehandle_log is not None:
                    name = self._omc_filehandle_log.name
                    self._omc_filehandle_log.close()
                    self._omc_filehandle_log = None
                    log_content = open(name).read()
                else:
                    log_content = '(missing log file)'
                raise OMCSessionException(f"OMC Server did not start (timeout={timeout}). "
                                          f"Could not open file {self._omc_file_port.as_posix()}. "
                                          f"Log-file says:\n{log_content}")
            time.sleep(timeout / 80.0)

        logger.info(f"OMC Server is up and running at {omc_zeromq_uri} "
                    f"pid={self._omc_process.pid if self._omc_process else '?'}")

        return port

    def _omc_port_get_main(self) -> Optional[str]:
        port = None
        if self._omc_file_port.is_file():
            # Read the port file
            with open(self._omc_file_port, 'r') as f_p:
                port = f_p.readline()
            self._omc_file_port.unlink()

        return port


# noinspection PyPep8Naming
class OMCSessionZMQDocker(OMCSessionZMQ):

    def __init__(self,
                 timeout: float = 10.00,
                 docker: Optional[str] = None,
                 dockerContainer: Optional[int] = None,
                 dockerExtraArgs: Optional[list] = None,
                 dockerOpenModelicaPath: str = "omc",
                 dockerNetwork: Optional[str] = None,
                 port: Optional[int] = None,
                 omhome: Optional[str] = None):
        super().__init__(timeout=timeout, omhome=omhome)

        if dockerExtraArgs is None:
            dockerExtraArgs = []

        if docker is None and dockerContainer is None:
            raise OMCSessionException("One of docker or dockerContainer must be set!")

        self._docker = docker
        self._dockerContainer = dockerContainer
        self._dockerExtraArgs = dockerExtraArgs
        self._dockerOpenModelicaPath = dockerOpenModelicaPath
        self._dockerNetwork = dockerNetwork

        self._interactivePort = port

        self._dockerCid: Optional[int] = None
        self._dockerCidFile: Optional[pathlib.Path] = None

    @staticmethod
    def _filename_port(current_user: str, random_str: str) -> str:
        filename = f"openmodelica.{current_user}.port.{random_str}"

        return filename

    @staticmethod
    def _getuid():
        """
        The uid to give to docker.
        On Windows, volumes are mapped with all files are chmod ugo+rwx,
        so uid does not matter as long as it is not the root user.
        """
        return 1000 if sys.platform == 'win32' else os.getuid()

    def _omc_command_get(self, omc_path_and_args_list) -> list:
        """
        Define the command that will be called by the subprocess module.
        """
        extraFlags = []

        if (self._docker or self._dockerContainer) and sys.platform == "win32":
            extraFlags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            if not self._interactivePort:
                raise OMCSessionException("docker on Windows requires knowing which port to connect to. For "
                                          "dockerContainer=..., the container needs to have already manually exposed "
                                          "this port when it was started (-p 127.0.0.1:n:n) or you get an error later.")

        if self._docker:
            if sys.platform == "win32":
                if self._interactivePort is not None and isinstance(self._interactivePort, int):
                    p = int(self._interactivePort)
                    dockerNetworkStr = ["-p", "127.0.0.1:%d:%d" % (p, p)]
                else:
                    raise OMCSessionException("Missing or invalid interactive port!")
            elif self._dockerNetwork == "host" or self._dockerNetwork is None:
                dockerNetworkStr = ["--network=host"]
            elif self._dockerNetwork == "separate":
                dockerNetworkStr = []
                extraFlags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            else:
                raise OMCSessionException(f'dockerNetwork was set to {self._dockerNetwork}, '
                                          'but only \"host\" or \"separate\" is allowed')
            self._dockerCidFile = self._omc_file_log.parent / (self._omc_file_log.stem + ".docker.cid")

            omcCommand = (["docker", "run",
                           "--cidfile", self._dockerCidFile.as_posix(),
                           "--rm",
                           "--env", "USER=%s" % self._currentUser,
                           "--user", str(self._getuid())]
                          + self._dockerExtraArgs
                          + dockerNetworkStr
                          + [self._docker, self._dockerOpenModelicaPath])
        elif self._dockerContainer:
            omcCommand = (["docker", "exec",
                           "--env", "USER=%s" % self._currentUser,
                           "--user", str(self._getuid())]
                          + self._dockerExtraArgs
                          + [self._dockerContainer, self._dockerOpenModelicaPath])
            self._dockerCid = self._dockerContainer
        else:
            raise OMCSessionException("Only for docker!")

        if self._interactivePort:
            extraFlags = extraFlags + ["--interactivePort=%d" % int(self._interactivePort)]

        omc_command = omcCommand + omc_path_and_args_list + extraFlags

        return omc_command

    def _omc_process_get(self, timeout):  # output?
        omc_process = super()._omc_process_get(timeout=timeout)

        if self._docker:
            for i in range(0, 40):
                try:
                    with open(self._dockerCidFile, "r") as fin:
                        self._dockerCid = fin.read().strip()
                except IOError:
                    pass
                if self._dockerCid:
                    break
                time.sleep(timeout / 40.0)
            try:
                os.remove(self._dockerCidFile)
            except FileNotFoundError:
                pass
            if self._dockerCid is None:
                logger.error("Docker did not start. Log-file says:\n%s" % (open(self._omc_filehandle_log.name).read()))
                raise OMCSessionException("Docker did not start (timeout=%f might be too short especially if you did "
                                          "not docker pull the image before this command)." % timeout)

        if self._docker or self._dockerContainer:
            dockerTop = None
            if self._dockerNetwork == "separate":
                output = subprocess.check_output(["docker", "inspect", self._dockerCid]).decode().strip()
                self._serverIPAddress = json.loads(output)[0]["NetworkSettings"]["IPAddress"]
            for i in range(0, 40):
                if sys.platform == 'win32':
                    break
                dockerTop = subprocess.check_output(["docker", "top", self._dockerCid]).decode().strip()
                omc_process = None
                for line in dockerTop.split("\n"):
                    columns = line.split()
                    if self._random_string in line:
                        try:
                            omc_process = DummyPopen(int(columns[1]))
                        except psutil.NoSuchProcess:
                            raise OMCSessionException(
                                f"Could not find PID {dockerTop} - is this a docker instance spawned "
                                f"without --pid=host?\nLog-file says:\n{open(self._omc_filehandle_log.name).read()}")
                        break
                if omc_process is not None:
                    break
                time.sleep(timeout / 40.0)
            if omc_process is None:
                raise OMCSessionException("Docker top did not contain omc process %s:\n%s\nLog-file says:\n%s"
                                          % (self._random_string, dockerTop,
                                             open(self._omc_filehandle_log.name).read()))

        return omc_process

    def _omc_port_get_main(self) -> Optional[str]:
        port = None

        try:
            port = subprocess.check_output(args=["docker",
                                                 "exec", str(self._dockerCid),
                                                 "cat", self._omc_file_port.as_posix()],
                                           stderr=subprocess.DEVNULL).decode().strip()
        except subprocess.CalledProcessError:
            pass

        return port
