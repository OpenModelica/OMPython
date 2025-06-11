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
                 docker: Optional[str] = None,
                 dockerContainer: Optional[int] = None,
                 dockerExtraArgs: Optional[list] = None,
                 dockerOpenModelicaPath: str = "omc",
                 dockerNetwork: Optional[str] = None,
                 port: Optional[int] = None,
                 omhome: Optional[str] = None):
        if dockerExtraArgs is None:
            dockerExtraArgs = []

        self._omhome = self._get_omhome(omhome=omhome)

        self._omc_process = None
        self._omc_command = None
        self._omc: Optional[Any] = None
        self._dockerCid: Optional[int] = None
        self._serverIPAddress = "127.0.0.1"
        self._temp_dir = pathlib.Path(tempfile.gettempdir())
        # generate a random string for this session
        self._random_string = uuid.uuid4().hex
        try:
            self._currentUser = getpass.getuser()
            if not self._currentUser:
                self._currentUser = "nobody"
        except KeyError:
            # We are running as a uid not existing in the password database... Pretend we are nobody
            self._currentUser = "nobody"

        self._docker = docker
        self._dockerContainer = dockerContainer
        self._dockerExtraArgs = dockerExtraArgs
        self._dockerOpenModelicaPath = dockerOpenModelicaPath
        self._dockerNetwork = dockerNetwork
        self._omc_log_file = self._create_omc_log_file("port")
        self._timeout = timeout
        # Locating and using the IOR
        if sys.platform != 'win32' or docker or dockerContainer:
            port_file = "openmodelica." + self._currentUser + ".port." + self._random_string
        else:
            port_file = "openmodelica.port." + self._random_string
        self._port_file = ((pathlib.Path("/tmp") if docker else self._temp_dir) / port_file).as_posix()
        self._interactivePort = port
        # set omc executable path and args
        self._omc_command = self._set_omc_command(omc_path_and_args_list=["--interactive=zmq",
                                                                          "--locale=C",
                                                                          f"-z={self._random_string}"])
        # start up omc executable, which is waiting for the ZMQ connection
        self._omc_process = self._start_omc_process(timeout)
        # connect to the running omc instance using ZMQ
        self._omc_port = self._connect_to_omc(timeout)

        self._re_log_entries = None
        self._re_log_raw = None

    def __del__(self):
        try:
            self.sendExpression("quit()")
        except OMCSessionException:
            pass
        self._omc_log_file.close()
        try:
            self._omc_process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            if self._omc_process:
                logger.warning("OMC did not exit after being sent the quit() command; "
                               "killing the process with pid=%s", self._omc_process.pid)
                self._omc_process.kill()
                self._omc_process.wait()

    def _create_omc_log_file(self, suffix):  # output?
        if sys.platform == 'win32':
            log_filename = f"openmodelica.{suffix}.{self._random_string}.log"
        else:
            log_filename = f"openmodelica.{self._currentUser}.{suffix}.{self._random_string}.log"
        # this file must be closed in the destructor
        omc_log_file = open(self._temp_dir / log_filename, "w+")

        return omc_log_file

    def _start_omc_process(self, timeout):  # output?
        if sys.platform == 'win32':
            omhome_bin = (self._omhome / "bin").as_posix()
            my_env = os.environ.copy()
            my_env["PATH"] = omhome_bin + os.pathsep + my_env["PATH"]
            omc_process = subprocess.Popen(self._omc_command, stdout=self._omc_log_file,
                                           stderr=self._omc_log_file, env=my_env)
        else:
            # set the user environment variable so omc running from wsgi has the same user as OMPython
            my_env = os.environ.copy()
            my_env["USER"] = self._currentUser
            omc_process = subprocess.Popen(self._omc_command, stdout=self._omc_log_file,
                                           stderr=self._omc_log_file, env=my_env)
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
                logger.error("Docker did not start. Log-file says:\n%s" % (open(self._omc_log_file.name).read()))
                raise OMCSessionException("Docker did not start (timeout=%f might be too short especially if you did "
                                          "not docker pull the image before this command)." % timeout)

        dockerTop = None
        if self._docker or self._dockerContainer:
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
                                f"without --pid=host?\nLog-file says:\n{open(self._omc_log_file.name).read()}")
                        break
                if omc_process is not None:
                    break
                time.sleep(timeout / 40.0)
            if omc_process is None:
                raise OMCSessionException("Docker top did not contain omc process %s:\n%s\nLog-file says:\n%s"
                                          % (self._random_string, dockerTop, open(self._omc_log_file.name).read()))
        return omc_process

    def _getuid(self):
        """
        The uid to give to docker.
        On Windows, volumes are mapped with all files are chmod ugo+rwx,
        so uid does not matter as long as it is not the root user.
        """
        return 1000 if sys.platform == 'win32' else os.getuid()

    def _set_omc_command(self, omc_path_and_args_list) -> list:
        """Define the command that will be called by the subprocess module.

        On Windows, use the list input style of the subprocess module to
        avoid problems resulting from spaces in the path string.
        Linux, however, only works with the string version.
        """
        if (self._docker or self._dockerContainer) and sys.platform == "win32":
            extraFlags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            if not self._interactivePort:
                raise OMCSessionException("docker on Windows requires knowing which port to connect to. For "
                                          "dockerContainer=..., the container needs to have already manually exposed "
                                          "this port when it was started (-p 127.0.0.1:n:n) or you get an error later.")
        else:
            extraFlags = []
        if self._docker:
            if sys.platform == "win32":
                assert self._interactivePort is not None  # mypy complained
                p = int(self._interactivePort)
                dockerNetworkStr = ["-p", "127.0.0.1:%d:%d" % (p, p)]
            elif self._dockerNetwork == "host" or self._dockerNetwork is None:
                dockerNetworkStr = ["--network=host"]
            elif self._dockerNetwork == "separate":
                dockerNetworkStr = []
                extraFlags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            else:
                raise OMCSessionException('dockerNetwork was set to %s, but only \"host\" or \"separate\" is allowed')
            self._dockerCidFile = self._omc_log_file.name + ".docker.cid"
            omcCommand = (["docker", "run",
                           "--cidfile", self._dockerCidFile,
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
            omcCommand = [str(self._get_omc_path())]
        if self._interactivePort:
            extraFlags = extraFlags + ["--interactivePort=%d" % int(self._interactivePort)]

        omc_command = omcCommand + omc_path_and_args_list + extraFlags

        return omc_command

    def _get_omhome(self, omhome: Optional[str] = None):
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

    def _get_omc_path(self) -> pathlib.Path:
        return self._omhome / "bin" / "omc"

    def _connect_to_omc(self, timeout) -> str:
        omc_zeromq_uri = "file:///" + self._port_file
        # See if the omc server is running
        attempts = 0
        port = None
        while True:
            if self._dockerCid:
                try:
                    port = subprocess.check_output(args=["docker",
                                                         "exec", str(self._dockerCid),
                                                         "cat", str(self._port_file)],
                                                   stderr=subprocess.DEVNULL).decode().strip()
                    break
                except subprocess.CalledProcessError:
                    pass
            else:
                if os.path.isfile(self._port_file):
                    # Read the port file
                    with open(self._port_file, 'r') as f_p:
                        port = f_p.readline()
                    os.remove(self._port_file)
                    break

            attempts += 1
            if attempts == 80.0:
                name = self._omc_log_file.name
                self._omc_log_file.close()
                logger.error("OMC Server did not start. Please start it! Log-file says:\n%s" % open(name).read())
                raise OMCSessionException(f"OMC Server did not start (timeout={timeout}). "
                                          f"Could not open file {self._port_file}")
            time.sleep(timeout / 80.0)

        port = port.replace("0.0.0.0", self._serverIPAddress)
        logger.info(f"OMC Server is up and running at {omc_zeromq_uri} "
                    f"pid={self._omc_process.pid if self._omc_process else '?'} cid={self._dockerCid}")

        # Create the ZeroMQ socket and connect to OMC server
        context = zmq.Context.instance()
        self._omc = context.socket(zmq.REQ)
        self._omc.setsockopt(zmq.LINGER, 0)  # Dismisses pending messages if closed
        self._omc.setsockopt(zmq.IMMEDIATE, True)  # Queue messages only to completed connections
        self._omc.connect(port)

        return port

    def execute(self, command):
        warnings.warn("This function is depreciated and will be removed in future versions; "
                      "please use sendExpression() instead", DeprecationWarning, stacklevel=1)

        return self.sendExpression(command, parsed=False)

    def sendExpression(self, command, parsed=True):
        p = self._omc_process.poll()  # check if process is running
        if p is not None:
            raise OMCSessionException("Process Exited, No connection with OMC. Create a new instance of OMCSessionZMQ!")

        if self._omc is None:
            raise OMCSessionException("No OMC running. Create a new instance of OMCSessionZMQ!")

        logger.debug("sendExpression(%r, parsed=%r)", command, parsed)

        attempts = 0
        while True:
            try:
                self._omc.send_string(str(command), flags=zmq.NOBLOCK)
                break
            except zmq.error.Again:
                pass
            attempts += 1
            if attempts >= 50:
                self._omc_log_file.seek(0)
                log = self._omc_log_file.read()
                self._omc_log_file.close()
                raise OMCSessionException(f"No connection with OMC (timeout={self._timeout}). Log-file says: \n{log}")
            time.sleep(self._timeout / 50.0)
        if command == "quit()":
            self._omc.close()
            self._omc = None
            return None
        else:
            result = self._omc.recv_string()

            if command == "getErrorString()":
                # no error handling if 'getErrorString()' is called
                pass
            elif command == "getMessagesStringInternal()":
                # no error handling if 'getMessagesStringInternal()' is called; parsing NOT possible!
                if parsed:
                    logger.warning("Result of 'getMessagesStringInternal()' cannot be parsed - set parsed to False!")
                    parsed = False
            else:
                # always check for error
                self._omc.send_string('getMessagesStringInternal()', flags=zmq.NOBLOCK)
                error_raw = self._omc.recv_string()
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
