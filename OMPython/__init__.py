# -*- coding: utf-8 -*-
"""
OMPython is a Python interface to OpenModelica.
To get started, create an OMCSession/OMCSessionZMQ object:
from OMPython import OMCSession/OMCSessionZMQ
omc = OMCSession()/OMCSessionZMQ()
omc.sendExpression(command)

Note: Conversion from OMPython 1.0 to OMPython 2.0 is very simple
1.0:
import OMPython
OMPython.execute(command)
2.0:
from OMPython import OMCSession
OMPython = OMCSession()
OMPython.execute(command)

OMPython 3.0 includes a new class OMCSessionZMQ uses PyZMQ to communicate
with OpenModelica. A new argument `useCorba=False` is added to ModelicaSystem
class which means it will use OMCSessionZMQ by default. If you want to use
OMCSession then create ModelicaSystem object like this,
obj = ModelicaSystem(useCorba=True)

The difference between execute and sendExpression is the type of the
returned expression. sendExpression maps Modelica types to Python types,
while execute tries to map also output that is not valid Modelica.
That format is harder to use.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from future.utils import with_metaclass
from builtins import int, range
from copy import deepcopy
import shutil

import abc
import csv
import getpass
import logging
import json
import os
import platform
import psutil
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from collections import OrderedDict
import numpy as np
import pyparsing
import importlib


if sys.platform == 'darwin':
    # On Mac let's assume omc is installed here and there might be a broken omniORB installed in a bad place
    sys.path.append('/opt/local/lib/python2.7/site-packages/')
    sys.path.append('/opt/openmodelica/lib/python2.7/site-packages/')

# TODO: replace this with the new parser
from OMPython import OMTypedParser, OMParser

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

# Logger Defined
logger = logging.getLogger('OMPython')
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
logger_console_handler = logging.StreamHandler()
logger_console_handler.setLevel(logging.INFO)

# create formatter and add it to the handlers
logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger_console_handler.setFormatter(logger_formatter)

# add the handlers to the logger
logger.addHandler(logger_console_handler)
logger.setLevel(logging.WARNING)

class DummyPopen():
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

class OMCSessionHelper():
  def __init__(self):
    # Get the path to the OMC executable, if not installed this will be None
    omc_env_home = os.environ.get('OPENMODELICAHOME')
    if omc_env_home:
      self.omhome = omc_env_home
    else:
      path_to_omc = shutil.which("omc")
      if path_to_omc is None:
        raise ValueError("Cannot find OpenModelica executable, please install from openmodelica.org")
      self.omhome = os.path.dirname(os.path.dirname(path_to_omc))
  def _get_omc_path(self):
    try:
      return os.path.join(self.omhome, 'bin', 'omc')
    except BaseException:
      logger.error("The OpenModelica compiler is missing in the System path (%s), please install it" % os.path.join(self.omhome, 'bin', 'omc'))
      raise

class OMCSessionBase(with_metaclass(abc.ABCMeta, object)):

    def __init__(self, readonly=False):
        self.readonly = readonly
        self.omc_cache = {}
        self._omc_process = None
        self._omc_command = None
        self._omc = None
        self._dockerCid = None
        self._serverIPAddress = "127.0.0.1"
        self._interactivePort = None
        # FIXME: this code is not well written... need to be refactored
        self._temp_dir = tempfile.gettempdir()
        # generate a random string for this session
        self._random_string = uuid.uuid4().hex
        # omc log file
        self._omc_log_file = None
        try:
            self._currentUser = getpass.getuser()
            if not self._currentUser:
                self._currentUser = "nobody"
        except KeyError:
            # We are running as a uid not existing in the password database... Pretend we are nobody
            self._currentUser = "nobody"

    def __del__(self):
        try:
          self.sendExpression("quit()")
        except:
          pass
        self._omc_log_file.close()
        if sys.version_info.major >= 3:
          try:
            self._omc_process.wait(timeout=2.0)
          except:
            if self._omc_process:
              self._omc_process.kill()
        else:
          for i in range(0,100):
            time.sleep(0.02)
            if self._omc_process and (self._omc_process.poll() is not None):
              break
        # kill self._omc_process process if it is still running/exists
        if self._omc_process is not None and self._omc_process.returncode is None:
            print("OMC did not exit after being sent the quit() command; killing the process with pid=%s" % str(self._omc_process.pid))
            if sys.platform=="win32":
                self._omc_process.kill()
                self._omc_process.wait()
            else:
                os.killpg(os.getpgid(self._omc_process.pid), signal.SIGTERM)
                self._omc_process.kill()
                self._omc_process.wait()

    def _create_omc_log_file(self, suffix):
        if sys.platform == 'win32':
            self._omc_log_file = open(os.path.join(self._temp_dir, "openmodelica.{0}.{1}.log".format(suffix, self._random_string)), 'w')
        else:
            # this file must be closed in the destructor
            self._omc_log_file = open(os.path.join(self._temp_dir, "openmodelica.{0}.{1}.{2}.log".format(self._currentUser, suffix, self._random_string)), 'w')

    def _start_omc_process(self, timeout):
        if sys.platform == 'win32':
            omhome_bin = os.path.join(self.omhome, 'bin').replace("\\", "/")
            my_env = os.environ.copy()
            my_env["PATH"] = omhome_bin + os.pathsep + my_env["PATH"]
            self._omc_process = subprocess.Popen(self._omc_command, stdout=self._omc_log_file, stderr=self._omc_log_file, env=my_env)
        else:
            # set the user environment variable so omc running from wsgi has the same user as OMPython
            my_env = os.environ.copy()
            my_env["USER"] = self._currentUser
            # Because we spawned a shell, and we need to be able to kill OMC, create a new process group for this
            self._omc_process = subprocess.Popen(self._omc_command, shell=True, stdout=self._omc_log_file, stderr=self._omc_log_file, env=my_env, preexec_fn=os.setsid)
        if self._docker:
          for i in range(0,40):
            try:
              with open(self._dockerCidFile, "r") as fin:
                self._dockerCid = fin.read().strip()
            except:
              pass
            if self._dockerCid:
              break
            time.sleep(timeout / 40.0)
          try:
            os.remove(self._dockerCidFile)
          except:
            pass
          if self._dockerCid is None:
            logger.error("Docker did not start. Log-file says:\n%s" % (open(self._omc_log_file.name).read()))
            raise Exception("Docker did not start (timeout=%f might be too short especially if you did not docker pull the image before this command)." % timeout)
        if self._docker or self._dockerContainer:
          if self._dockerNetwork == "separate":
            self._serverIPAddress = json.loads(subprocess.check_output(["docker", "inspect", self._dockerCid]).decode().strip())[0]["NetworkSettings"]["IPAddress"]
          for i in range(0,40):
            if sys.platform == 'win32':
              break
            dockerTop = subprocess.check_output(["docker", "top", self._dockerCid]).decode().strip()
            self._omc_process = None
            for line in dockerTop.split("\n"):
              columns = line.split()
              if self._random_string in line:
                try:
                  self._omc_process = DummyPopen(int(columns[1]))
                except psutil.NoSuchProcess:
                  raise Exception("Could not find PID %d - is this a docker instance spawned without --pid=host?\nLog-file says:\n%s" % (self._random_string, dockerTop, open(self._omc_log_file.name).read()))
                break
            if self._omc_process is not None:
              break
            time.sleep(timeout / 40.0)
          if self._omc_process is None:
            raise Exception("Docker top did not contain omc process %s:\n%s\nLog-file says:\n%s" % (self._random_string, dockerTop, open(self._omc_log_file.name).read()))
        return self._omc_process

    def _getuid(self):
      """
      The uid to give to docker.
      On Windows, volumes are mapped with all files are chmod ugo+rwx,
      so uid does not matter as long as it is not the root user.
      """
      return 1000 if sys.platform == 'win32' else os.getuid()

    def _set_omc_command(self, omc_path_and_args_list):
        """Define the command that will be called by the subprocess module.

        On Windows, use the list input style of the subprocess module to
        avoid problems resulting from spaces in the path string.
        Linux, however, only works with the string version.
        """
        if (self._docker or self._dockerContainer) and sys.platform == "win32":
            extraFlags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            if not self._interactivePort:
                raise Exception("docker on Windows requires knowing which port to connect to. For dockerContainer=..., the container needs to have already manually exposed this port when it was started (-p 127.0.0.1:n:n) or you get an error later.")
        else:
            extraFlags = []
        if self._docker:
            if sys.platform == "win32":
                p = int(self._interactivePort)
                dockerNetworkStr = ["-p", "127.0.0.1:%d:%d" % (p,p)]
            elif self._dockerNetwork == "host" or self._dockerNetwork is None:
                dockerNetworkStr = ["--network=host"]
            elif self._dockerNetwork == "separate":
                dockerNetworkStr = []
                extraFlags = ["-d=zmqDangerousAcceptConnectionsFromAnywhere"]
            else:
                raise Exception('dockerNetwork was set to %s, but only \"host\" or \"separate\" is allowed')
            self._dockerCidFile = self._omc_log_file.name + ".docker.cid"
            omcCommand = ["docker", "run", "--cidfile", self._dockerCidFile, "--rm", "--env", "USER=%s" % self._currentUser, "--user", str(self._getuid())] + self._dockerExtraArgs + dockerNetworkStr + [self._docker, self._dockerOpenModelicaPath]
        elif self._dockerContainer:
            omcCommand = ["docker", "exec", "--env", "USER=%s" % self._currentUser, "--user", str(self._getuid())] + self._dockerExtraArgs + [self._dockerContainer, self._dockerOpenModelicaPath]
            self._dockerCid = self._dockerContainer
        else:
            omcCommand = [self._get_omc_path()]
        if self._interactivePort:
            extraFlags = extraFlags + ["--interactivePort=%d" % int(self._interactivePort)]

        omc_path_and_args_list = omcCommand + omc_path_and_args_list + extraFlags

        if sys.platform == 'win32':
            self._omc_command = omc_path_and_args_list
        else:
            self._omc_command = ' '.join([shlex.quote(a) if (sys.version_info > (3, 0)) else a for a in omc_path_and_args_list])

        return self._omc_command

    @abc.abstractmethod
    def _connect_to_omc(self, timeout):
        pass

    # FIXME: we should have one function which interacts with OMC. Either execute OR sendExpression.
    # Execute uses OMParser.check_for_values and sendExpression uses OMTypedParser.parseString.
    # We should have one parser. Then we can get rid of one of these functions.
    @abc.abstractmethod
    def execute(self, command):
        pass

    def clearOMParserResult(self):
        OMParser.result = {}

    # FIXME: we should have one function which interacts with OMC. Either execute OR sendExpression.
    # Execute uses OMParser.check_for_values and sendExpression uses OMTypedParser.parseString.
    # We should have one parser. Then we can get rid of one of these functions.
    @abc.abstractmethod
    def sendExpression(self, command, parsed=True):
        """
        Sends an expression to the OpenModelica. The return type is parsed as if the
        expression was part of the typed OpenModelica API (see ModelicaBuiltin.mo).
        * Integer and Real are returned as Python numbers
        * Strings, enumerations, and typenames are returned as Python strings
        * Arrays, tuples, and MetaModelica lists are returned as tuples
        * Records are returned as dicts (the name of the record is lost)
        * Booleans are returned as True or False
        * NONE() is returned as None
        * SOME(value) is returned as value
        """
        pass

    def ask(self, question, opt=None, parsed=True):
        p = (question, opt, parsed)

        if self.readonly and question != 'getErrorString':
            # can use cache if readonly
            if p in self.omc_cache:
                return self.omc_cache[p]

        if opt:
            expression = '{0}({1})'.format(question, opt)
        else:
            expression = question

        logger.debug('OMC ask: {0}  - parsed: {1}'.format(expression, parsed))

        try:
            if parsed:
                res = self.execute(expression)
            else:
                res = self.sendExpression(expression, parsed=False)
        except Exception as e:
            logger.error("OMC failed: {0}, {1}, parsed={2}".format(question, opt, parsed))
            raise e

        # save response
        self.omc_cache[p] = res

        return res

    # TODO: Open Modelica Compiler API functions. Would be nice to generate these.
    def loadFile(self, filename):
        return self.ask('loadFile', '"{0}"'.format(filename))

    def loadModel(self, className):
        return self.ask('loadModel', className)

    def isModel(self, className):
        return self.ask('isModel', className)

    def isPackage(self, className):
        return self.ask('isPackage', className)

    def isPrimitive(self, className):
        return self.ask('isPrimitive', className)

    def isConnector(self, className):
        return self.ask('isConnector', className)

    def isRecord(self, className):
        return self.ask('isRecord', className)

    def isBlock(self, className):
        return self.ask('isBlock', className)

    def isType(self, className):
        return self.ask('isType', className)

    def isFunction(self, className):
        return self.ask('isFunction', className)

    def isClass(self, className):
        return self.ask('isClass', className)

    def isParameter(self, className):
        return self.ask('isParameter', className)

    def isConstant(self, className):
        return self.ask('isConstant', className)

    def isProtected(self, className):
        return self.ask('isProtected', className)

    def getPackages(self, className="AllLoadedClasses"):
        return self.ask('getPackages', className)

    def getClassRestriction(self, className):
        return self.ask('getClassRestriction', className)

    def getDerivedClassModifierNames(self, className):
        return self.ask('getDerivedClassModifierNames', className)

    def getDerivedClassModifierValue(self, className, modifierName):
        return self.ask('getDerivedClassModifierValue', '{0}, {1}'.format(className, modifierName))

    def typeNameStrings(self, className):
        return self.ask('typeNameStrings', className)

    def getComponents(self, className):
        return self.ask('getComponents', className)

    def getClassComment(self, className):
        try:
            return self.ask('getClassComment', className)
        except pyparsing.ParseException as ex:
            logger.warning("Method 'getClassComment' failed for {0}".format(className))
            logger.warning('OMTypedParser error: {0}'.format(ex.message))
            return 'No description available'

    def getNthComponent(self, className, comp_id):
        """ returns with (type, name, description) """
        return self.ask('getNthComponent', '{0}, {1}'.format(className, comp_id))

    def getNthComponentAnnotation(self, className, comp_id):
        return self.ask('getNthComponentAnnotation', '{0}, {1}'.format(className, comp_id))

    def getImportCount(self, className):
        return self.ask('getImportCount', className)

    def getNthImport(self, className, importNumber):
        # [Path, id, kind]
        return self.ask('getNthImport', '{0}, {1}'.format(className, importNumber))

    def getInheritanceCount(self, className):
        return self.ask('getInheritanceCount', className)

    def getNthInheritedClass(self, className, inheritanceDepth):
        return self.ask('getNthInheritedClass', '{0}, {1}'.format(className, inheritanceDepth))

    def getParameterNames(self, className):
        try:
            return self.ask('getParameterNames', className)
        except KeyError as ex:
            logger.warning('OMPython error: {0}'.format(ex))
            # FIXME: OMC returns with a different structure for empty parameter set
            return []

    def getParameterValue(self, className, parameterName):
        try:
            return self.ask('getParameterValue', '{0}, {1}'.format(className, parameterName))
        except pyparsing.ParseException as ex:
            logger.warning('OMTypedParser error: {0}'.format(ex.message))
            return ""

    def getComponentModifierNames(self, className, componentName):
        return self.ask('getComponentModifierNames', '{0}, {1}'.format(className, componentName))

    def getComponentModifierValue(self, className, componentName):
        try:
            # FIXME: OMPython exception UnboundLocalError exception for 'Modelica.Fluid.Machines.ControlledPump'
            return self.ask('getComponentModifierValue', '{0}, {1}'.format(className, componentName))
        except pyparsing.ParseException as ex:
            logger.warning('OMTypedParser error: {0}'.format(ex.message))
            result = self.ask('getComponentModifierValue', '{0}, {1}'.format(className, componentName), parsed=False)
            try:
                answer = OMParser.check_for_values(result)
                OMParser.result = {}
                return answer[2:]
            except (TypeError, UnboundLocalError) as ex:
                logger.warning('OMParser error: {0}'.format(ex))
                return result

    def getExtendsModifierNames(self, className, componentName):
        return self.ask('getExtendsModifierNames', '{0}, {1}'.format(className, componentName))

    def getExtendsModifierValue(self, className, extendsName, modifierName):
        try:
            # FIXME: OMPython exception UnboundLocalError exception for 'Modelica.Fluid.Machines.ControlledPump'
            return self.ask('getExtendsModifierValue', '{0}, {1}, {2}'.format(className, extendsName, modifierName))
        except pyparsing.ParseException as ex:
            logger.warning('OMTypedParser error: {0}'.format(ex.message))
            result = self.ask('getExtendsModifierValue', '{0}, {1}, {2}'.format(className, extendsName, modifierName), parsed=False)
            try:
                answer = OMParser.check_for_values(result)
                OMParser.result = {}
                return answer[2:]
            except (TypeError, UnboundLocalError) as ex:
                logger.warning('OMParser error: {0}'.format(ex))
                return result

    def getNthComponentModification(self, className, comp_id):
        # FIXME: OMPython exception Results KeyError exception

        # get {$Code(....)} field
        # \{\$Code\((\S*\s*)*\)\}
        value = self.ask('getNthComponentModification', '{0}, {1}'.format(className, comp_id), parsed=False)
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
        if className:
            value = self.ask('getClassNames',
                             '{0}, recursive={1}, qualified={2}, sort={3}, builtin={4}, showProtected={5}'.format(
                                 className, str(recursive).lower(), str(qualified).lower(), str(sort).lower(),
                                 str(builtin).lower(), str(showProtected).lower()))
        else:
            value = self.ask('getClassNames',
                             'recursive={0}, qualified={1}, sort={2}, builtin={3}, showProtected={4}'.format(
                                 str(recursive).lower(), str(qualified).lower(), str(sort).lower(),
                                 str(builtin).lower(), str(showProtected).lower()))
        return value


class OMCSession(OMCSessionHelper, OMCSessionBase):

    def __init__(self, readonly=False, serverFlag='--interactive=corba', timeout = 10.0, docker = None, dockerContainer = None, dockerExtraArgs = [], dockerOpenModelicaPath = "omc", dockerNetwork = None):
        OMCSessionHelper.__init__(self)
        OMCSessionBase.__init__(self, readonly)
        self._create_omc_log_file("objid")
        # Locating and using the IOR
        if sys.platform != 'win32' or docker or dockerContainer:
            self._port_file = "openmodelica." + self._currentUser + ".objid." + self._random_string
        else:
            self._port_file = "openmodelica.objid." + self._random_string
        self._port_file = os.path.join("/tmp" if (docker or dockerContainer) else self._temp_dir, self._port_file).replace("\\", "/")
        # set omc executable path and args
        self._docker = docker
        self._dockerContainer = dockerContainer
        self._dockerExtraArgs = dockerExtraArgs
        self._dockerOpenModelicaPath = dockerOpenModelicaPath
        self._dockerNetwork = dockerNetwork
        self._timeout = timeout
        self._create_omc_log_file("port")

        self._set_omc_command([serverFlag, "+c={0}".format(self._random_string)])

        # start up omc executable, which is waiting for the CORBA connection
        self._start_omc_process(timeout)
        # connect to the running omc instance using CORBA
        self._connect_to_omc(timeout)

    def __del__(self):
        OMCSessionBase.__del__(self)

    def _connect_to_omc(self, timeout):
        # add OPENMODELICAHOME\lib\python to PYTHONPATH so python can load omniORB imports
        sys.path.append(os.path.join(self.omhome, 'lib', 'python'))
        # import the skeletons for the global module
        try:
          from omniORB import CORBA
          from OMPythonIDL import _OMCIDL
        except ImportError:
          self._omc_process.kill()
          raise
        self._omc_corba_uri = "file:///" + self._port_file
        # See if the omc server is running
        attempts = 0
        while True:
            if self._dockerCid:
                try:
                    self._ior = subprocess.check_output(["docker", "exec", self._dockerCid, "cat", self._port_file], stderr=subprocess.DEVNULL if (sys.version_info > (3, 0)) else subprocess.STDOUT).decode().strip()
                    break
                except subprocess.CalledProcessError:
                    pass
            if os.path.isfile(self._port_file):
                # Read the IOR file
                with open(self._port_file, 'r') as f_p:
                    self._ior = f_p.readline()
                break
            attempts += 1
            if attempts == 80:
                name = self._omc_log_file.name
                self._omc_log_file.close()
                with open(name) as fin:
                  contents = fin.read()
                self._omc_process.kill()
                raise Exception("OMC Server is down (timeout=%f). Please start it! If the OMC version is old, try OMCSession(..., serverFlag='-d=interactiveCorba') or +d=interactiveCorba. Log-file says:\n%s" % (timeout, contents))
            time.sleep(timeout / 80.0)

        while True:
            if self._dockerCid:
                try:
                    self._port = subprocess.check_output(["docker", "exec", self._dockerCid, "cat", self._port_file]).decode().strip()
                    break
                except:
                    pass
            else:
                if os.path.isfile(self._port_file):
                    # Read the port file
                    with open(self._port_file, 'r') as f_p:
                        self._port = f_p.readline()
                    os.remove(self._port_file)
                    break

            attempts += 1
            if attempts == 80.0:
                name = self._omc_log_file.name
                self._omc_log_file.close()
                logger.error("OMC Server is down (timeout=%f). Please start it! Log-file says:\n%s" % open(name).read())
                raise Exception("OMC Server is down. Could not open file %s" % (timeout,self._port_file))
            time.sleep(timeout / 80.0)

        logger.info("OMC Server is up and running at {0}".format(self._omc_corba_uri))
        # initialize the ORB with maximum size for the ORB set
        sys.argv.append("-ORBgiopMaxMsgSize")
        sys.argv.append("2147483647")
        self._orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)

        # Find the root POA
        self._poa = self._orb.resolve_initial_references("RootPOA")
        # Convert the IOR into an object reference
        self._obj_reference = self._orb.string_to_object(self._ior)
        # Narrow the reference to the OmcCommunication object
        self._omc = self._obj_reference._narrow(_OMCIDL.OmcCommunication)
        # Check if we are using the right object
        if self._omc is None:
            logger.error("Object reference is not valid")
            raise Exception

    def execute(self, command):
        ## check for process is running
        p=self._omc_process.poll()
        if (p == None):
            result = self._omc.sendExpression(command)
            if command == "quit()":
                self._omc = None
                return result
            else:
                answer = OMParser.check_for_values(result)
                return answer
        else:
            raise Exception("Process Exited, No connection with OMC. Create a new instance of OMCSession")

    def sendExpression(self, command, parsed=True):
        ## check for process is running
        p=self._omc_process.poll()
        if (p== None):
            result = self._omc.sendExpression(str(command))
            if command == "quit()":
                self._omc = None
                return result
            else:
                if parsed is True:
                    answer = OMTypedParser.parseString(result)
                    return answer
                else:
                    return result
        else:
            raise Exception("Process Exited, No connection with OMC. Create a new instance of OMCSession")

try:
  import zmq
except ImportError:
  pass

class OMCSessionZMQ(OMCSessionHelper, OMCSessionBase):

    def __init__(self, readonly=False, timeout = 10.00, docker = None, dockerContainer = None, dockerExtraArgs = [], dockerOpenModelicaPath = "omc", dockerNetwork = None, port = None):
        OMCSessionHelper.__init__(self)
        OMCSessionBase.__init__(self, readonly)
        # Locating and using the IOR
        if sys.platform != 'win32' or docker or dockerContainer:
            self._port_file = "openmodelica." + self._currentUser + ".port." + self._random_string
        else:
            self._port_file = "openmodelica.port." + self._random_string
        self._docker = docker
        self._dockerContainer = dockerContainer
        self._dockerExtraArgs = dockerExtraArgs
        self._dockerOpenModelicaPath = dockerOpenModelicaPath
        self._dockerNetwork = dockerNetwork
        self._create_omc_log_file("port")
        self._timeout = timeout
        self._port_file = os.path.join("/tmp" if docker else self._temp_dir, self._port_file).replace("\\", "/")
        self._interactivePort = port
        # set omc executable path and args
        self._set_omc_command([
                               "--interactive=zmq",
                               "--locale=C",
                               "-z={0}".format(self._random_string)
                               ])
        # start up omc executable, which is waiting for the ZMQ connection
        self._start_omc_process(timeout)
        # connect to the running omc instance using ZMQ
        self._connect_to_omc(timeout)

    def __del__(self):
        OMCSessionBase.__del__(self)

    def _connect_to_omc(self, timeout):
        self._omc_zeromq_uri = "file:///" + self._port_file
        # See if the omc server is running
        attempts = 0
        self._port = None
        while True:
            if self._dockerCid:
                try:
                    self._port = subprocess.check_output(["docker", "exec", self._dockerCid, "cat", self._port_file], stderr=subprocess.DEVNULL if (sys.version_info > (3, 0)) else subprocess.STDOUT).decode().strip()
                    break
                except:
                    pass
            else:
                if os.path.isfile(self._port_file):
                    # Read the port file
                    with open(self._port_file, 'r') as f_p:
                        self._port = f_p.readline()
                    os.remove(self._port_file)
                    break

            attempts += 1
            if attempts == 80.0:
                name = self._omc_log_file.name
                self._omc_log_file.close()
                logger.error("OMC Server did not start. Please start it! Log-file says:\n%s" % open(name).read())
                raise Exception("OMC Server did not start (timeout=%f). Could not open file %s" % (timeout,self._port_file))
            time.sleep(timeout / 80.0)

        self._port = self._port.replace("0.0.0.0", self._serverIPAddress)
        logger.info("OMC Server is up and running at {0} pid={1} cid={2}".format(self._omc_zeromq_uri, self._omc_process.pid, self._dockerCid))

        # Create the ZeroMQ socket and connect to OMC server
        import zmq
        context = zmq.Context.instance()
        self._omc = context.socket(zmq.REQ)
        self._omc.setsockopt(zmq.LINGER, 0) # Dismisses pending messages if closed
        self._omc.setsockopt(zmq.IMMEDIATE, True) # Queue messages only to completed connections
        self._omc.connect(self._port)

    def execute(self, command):
        ## check for process is running
        return self.sendExpression(command, parsed=False)

    def sendExpression(self, command, parsed=True):
        ## check for process is running
        p=self._omc_process.poll()
        if (p == None):
            attempts = 0
            while True:
                try:
                    self._omc.send_string(str(command), flags=zmq.NOBLOCK)
                    break
                except zmq.error.Again:
                    pass
                attempts += 1
                if attempts == 50.0:
                    name = self._omc_log_file.name
                    self._omc_log_file.close()
                    raise Exception("No connection with OMC (timeout=%f). Log-file says: \n%s" % (self._timeout, open(name).read()))
                time.sleep(self._timeout / 50.0)
            if command == "quit()":
                self._omc.close()
                self._omc = None
                return None
            else:
                result = self._omc.recv_string()
                if parsed is True:
                    answer = OMTypedParser.parseString(result)
                    return answer
                else:
                    return result
        else:
            raise Exception("Process Exited, No connection with OMC. Create a new instance of OMCSession")


class ModelicaSystem(object):
    def __init__(self, fileName=None, modelName=None, lmodel=[], useCorba=False, commandLineOptions=None, variableFilter=None, customBuildDirectory=None, verbose=True):  # 1
        """
        "constructor"
        It initializes to load file and build a model, generating object, exe, xml, mat, and json files. etc. It can be called :
            •without any arguments: In this case it neither loads a file nor build a model. This is useful when a FMU needed to convert to Modelica model
            •with two arguments as file name with ".mo" extension and the model name respectively
            •with three arguments, the first and second are file name and model name respectively and the third arguments is Modelica standard library to load a model, which is common in such models where the model is based on the standard library. For example, here is a model named "dcmotor.mo" below table 4-2, which is located in the directory of OpenModelica at "C:\\OpenModelica1.9.4-dev.beta2\\share\\doc\\omc\\testmodels".
        Note: If the model file is not in the current working directory, then the path where file is located must be included together with file name. Besides, if the Modelica model contains several different models within the same package, then in order to build the specific model, in second argument, user must put the package name with dot(.) followed by specific model name.
        ex: myModel = ModelicaSystem("ModelicaModel.mo", "modelName")
        """
        if fileName is None and modelName is None and not lmodel:  # all None
            if useCorba:
                self.getconn = OMCSession()
            else:
                self.getconn = OMCSessionZMQ()
            return

        self.tree = None
        self.quantitiesList=[]
        self.paramlist={}
        self.inputlist={}
        self.outputlist={}
        self.continuouslist={}
        self.simulateOptions={}
        self.overridevariables={}
        self.simoptionsoverride={}
        self.linearOptions={'startTime':0.0, 'stopTime': 1.0, 'stepSize':0.002, 'tolerance':1e-8}
        self.optimizeOptions={'startTime':0.0, 'stopTime': 1.0, 'numberOfIntervals':500, 'stepSize':0.002, 'tolerance':1e-8}
        self.linearinputs = []  # linearization input list
        self.linearoutputs = []  # linearization output list
        self.linearstates = []  # linearization  states list
        self.tempdir = ""

        if useCorba:
            self.getconn = OMCSession()
        else:
            self.getconn = OMCSessionZMQ()

        ## needed for properly deleting the OMCSessionZMQ
        self._omc_log_file = self.getconn._omc_log_file
        self._omc_process = self.getconn._omc_process

        ## set commandLineOptions if provided by users
        if commandLineOptions is not None:
            exp="".join(["setCommandLineOptions(","\"",commandLineOptions,"\"",")"])
            self.getconn.sendExpression(exp)

        self.xmlFile = None
        self.lmodel = lmodel  # may be needed if model is derived from other model
        self.modelName = modelName  # Model class name
        self.fileName = fileName  # Model file/package name
        self.inputFlag = False  # for model with input quantity
        self.simulationFlag = False  # if the model is simulated?
        self.outputFlag = False
        self.csvFile = ''  # for storing inputs condition
        self.resultfile="" # for storing result file
        self.variableFilter = variableFilter

        if fileName is not None and  not os.path.exists(self.fileName):  # if file does not eixt
            print("File Error:" + os.path.abspath(self.fileName) + " does not exist!!!")
            return

        ## set default command Line Options for linearization as
        ## linearize() will use the simulation executable and runtime
        ## flag -l to perform linearization
        self.getconn.sendExpression("setCommandLineOptions(\"--linearizationDumpLanguage=python\")")
        self.getconn.sendExpression("setCommandLineOptions(\"--generateSymbolicLinearization\")")

        self.setTempDirectory(customBuildDirectory)

        if fileName is not None:
            self.loadLibrary(verbose)
            self.loadFile(verbose)

        ## allow directly loading models from MSL without fileName
        if fileName is None and modelName is not None:
            self.loadLibrary(verbose)

        self.buildModel(variableFilter, verbose)

    def __del__(self):
        OMCSessionBase.__del__(self)

    def setCommandLineOptions(self):
        ## set commandLineOptions if provided by users
        if commandLineOptions is not None:
            exp="".join(["setCommandLineOptions(","\"",commandLineOptions,"\"",")"])
            cmdexp = self.getconn.sendExpression(exp)
            if not cmdexp:
                return print(self.getconn.sendExpression("getErrorString()"))

    def loadFile(self, verbose):
        # load file
        loadFileExp="".join(["loadFile(","\"",self.fileName,"\"",")"]).replace("\\","/")
        loadMsg = self.getconn.sendExpression(loadFileExp)
        ## Show notification or warnings to the user when verbose=True OR if some error occurred i.e., not result
        if verbose or not loadMsg:
            return print(self.getconn.sendExpression("getErrorString()"))

    # for loading file/package, loading model and building model
    def loadLibrary(self, verbose):
        # load Modelica standard libraries or Modelica files if needed
        for element in self.lmodel:
            if element is not None:
                if isinstance(element, str):
                    if element.endswith(".mo"):
                        apiCall = "loadFile"
                    else:
                        apiCall = "loadModel"
                    result = self.requestApi(apiCall, element)
                elif isinstance(element, tuple):
                    if not element[1]:
                        libname = "".join(["loadModel(", element[0], ")"])
                    else:
                        libname = "".join(["loadModel(", element[0], ", ", "{", "\"", element[1], "\"", "}", ")"])
                    result = self.sendExpression(libname)
                else:
                    print("| info | loadLibrary() failed, Unknown type detected: ", element , " is of type ",  type(element), ", The following patterns are supported\n1)[\"Modelica\"]\n2)[(\"Modelica\",\"3.2.3\"), \"PowerSystems\"]\n")
                ## Show notification or warnings to the user when verbose=True OR if some error occurred i.e., not result
                if verbose or not result:
                    print(self.requestApi('getErrorString'))

    def setTempDirectory(self, customBuildDirectory):
        # create a unique temp directory for each session and build the model in that directory
        if customBuildDirectory is not None:
            if not os.path.exists(customBuildDirectory):
                print(customBuildDirectory, " does not exist")
            self.tempdir = customBuildDirectory
        else:
            self.tempdir = tempfile.mkdtemp()
            if not os.path.exists(self.tempdir):
                print(self.tempdir, " cannot be created")

        exp="".join(["cd(","\"",self.tempdir,"\"",")"]).replace("\\","/")
        self.getconn.sendExpression(exp)

    def getWorkDirectory(self):
        return self.tempdir

    def buildModel(self, variableFilter=None, verbose=True):
        if variableFilter is not None:
            self.variableFilter = variableFilter

        if self.variableFilter is not None:
            varFilter = "variableFilter=" + "\"" + self.variableFilter + "\""
        else:
            varFilter = "variableFilter=" +  "\".*""\""
        # print(varFilter)
        # buildModelResult=self.getconn.sendExpression("buildModel("+ mName +")")
        buildModelResult = self.requestApi("buildModel", self.modelName, properties=varFilter)
        buildModelError = self.requestApi("getErrorString")

        if ('' in buildModelResult):
            print(buildModelError)

        # Issue #145. Always print the getErrorString since it might contains build warnings.
        if verbose:
            print(buildModelError)

        self.xmlFile=os.path.join(os.path.dirname(buildModelResult[0]),buildModelResult[1]).replace("\\","/")
        self.xmlparse()

    def sendExpression(self,expr,parsed=True):
        return self.getconn.sendExpression(expr,parsed)

    # request to OMC
    def requestApi(self, apiName, entity=None, properties=None):  # 2
        if (entity is not None and properties is not None):
            exp = '{}({}, {})'.format(apiName, entity, properties)
        elif entity is not None and properties is None:
            if (apiName == "loadFile" or apiName == "importFMU"):
                exp = '{}("{}")'.format(apiName, entity)
            else:
                exp = '{}({})'.format(apiName, entity)
        else:
            exp = '{}()'.format(apiName)
        try:
            res = self.getconn.sendExpression(exp)
        except Exception as e:
            print(e)
            res = None
        return res


    def xmlparse(self):
        if(os.path.exists(self.xmlFile)):
            self.tree = ET.parse(self.xmlFile)
            self.root = self.tree.getroot()
            rootCQ = self.root
            for attr in rootCQ.iter('DefaultExperiment'):
                self.simulateOptions["startTime"]= attr.get('startTime')
                self.simulateOptions["stopTime"] = attr.get('stopTime')
                self.simulateOptions["stepSize"] = attr.get('stepSize')
                self.simulateOptions["tolerance"] = attr.get('tolerance')
                self.simulateOptions["solver"] = attr.get('solver')
                self.simulateOptions["outputFormat"] = attr.get('outputFormat')

            for sv in rootCQ.iter('ScalarVariable'):
                scalar={}
                scalar["name"] = sv.get('name')
                scalar["changeable"] = sv.get('isValueChangeable')
                scalar["description"] = sv.get('description')
                scalar["variability"] = sv.get('variability')
                scalar["causality"] = sv.get('causality')
                scalar["alias"] = sv.get('alias')
                scalar["aliasvariable"] = sv.get('aliasVariable')
                ch = list(sv)
                start = None
                min = None
                max = None
                unit = None
                for att in ch:
                    start = att.get('start')
                    min = att.get('min')
                    max = att.get('max')
                    unit = att.get('unit')
                scalar["start"] =start
                scalar["min"] = min
                scalar["max"] = max
                scalar["unit"] = unit

                if(scalar["variability"]=="parameter"):
                    if scalar["name"] in self.overridevariables:
                        self.paramlist[scalar["name"]] = self.overridevariables[scalar["name"]]
                    else:
                        self.paramlist[scalar["name"]] = scalar["start"]
                if(scalar["variability"]=="continuous"):
                    self.continuouslist[scalar["name"]]=scalar["start"]
                if(scalar["causality"]=="input"):
                    self.inputlist[scalar["name"]]=scalar["start"]
                if(scalar["causality"]=="output"):
                    self.outputlist[scalar["name"]]=scalar["start"]

                self.quantitiesList.append(scalar)
        else:
            print("Error: ! XML file not generated: " + self.xmlFile)
            return


    def getQuantities(self, names=None):  # 3
        """
        This method returns list of dictionaries. It displays details of quantities such as name, value, changeable, and description, where changeable means  if value for corresponding quantity name is changeable or not. It can be called :
        usage:
        >>> getQuantities()
        >>> getQuantities("Name1")
        >>> getQuantities(["Name1","Name2"])
        """
        if(names==None):
            return self.quantitiesList
        elif(isinstance(names, str)):
            return [x for x in self.quantitiesList if x["name"] == names]
        elif isinstance(names, list):
            return [x for y in names for x in self.quantitiesList if x["name"]==y]


    def getContinuous(self, names=None):  # 4
        """
        This method returns dict. The key is continuous names and value is corresponding continuous value.
        usage:
        >>> getContinuous()
        >>> getContinuous("Name1")
        >>> getContinuous(["Name1","Name2"])
        """
        if not self.simulationFlag:
            if(names==None):
                return self.continuouslist
            elif(isinstance(names, str)):
                return [self.continuouslist.get(names ,"NotExist")]
            elif(isinstance(names, list)):
                return ([self.continuouslist.get(x ,"NotExist") for x in names])
        else:
            if(names==None):
                for i in self.continuouslist:
                    try:
                        value = self.getSolutions(i)
                        self.continuouslist[i]=value[0][-1]
                    except Exception:
                        print(i,"could not be computed")
                return self.continuouslist

            elif(isinstance(names, str)):
                if names in self.continuouslist:
                    value = self.getSolutions(names)
                    self.continuouslist[names]=value[0][-1]
                    return [self.continuouslist.get(names)]
                else:
                    return (names, "  is not continuous")

            elif(isinstance(names, list)):
                valuelist=[]
                for i in names:
                    if i in self.continuouslist:
                        value=self.getSolutions(i)
                        self.continuouslist[i]=value[0][-1]
                        valuelist.append(value[0][-1])
                    else:
                        return (i,"  is not continuous")
                return valuelist

    def getParameters(self, names=None):  # 5
        """
        This method returns dict. The key is parameter names and value is corresponding parameter value.
        If name is None then the function will return dict which contain all parameter names as key and value as corresponding values.
        usage:
        >>> getParameters()
        >>> getParameters("Name1")
        >>> getParameters(["Name1","Name2"])
        """
        if(names==None):
            return self.paramlist
        elif(isinstance(names, str)):
            return [self.paramlist.get(names,"NotExist")]
        elif(isinstance(names, list)):
            return ([self.paramlist.get(x,"NotExist") for x in names])

    def getlinearParameters(self, names=None):  # 5
        """
        This method returns dict. The key is parameter names and value is corresponding parameter value.
        If *name is None then the function will return dict which contain all parameter names as key and value as corresponding values. eg., getParameters()
        Otherwise variable number of arguments can be passed as parameter name in string format separated by commas. eg., getParameters('paraName1', 'paraName2')
        """
        if(names==0):
            return self.linearparameters
        elif(isinstance(names, str)):
            return [self.linearparameters.get(names,"NotExist")]
        else:
            return ([self.linearparameters.get(x,"NotExist") for x in names])

    def getInputs(self, names=None):  # 6
        """
        This method returns dict. The key is input names and value is corresponding input value.
        If *name is None then the function will return dict which contain all input names as key and value as corresponding values. eg., getInputs()
        Otherwise variable number of arguments can be passed as input name in string format separated by commas. eg., getInputs('iName1', 'iName2')
        """
        if(names==None):
            return self.inputlist
        elif(isinstance(names, str)):
            return [self.inputlist.get(names,"NotExist")]
        elif(isinstance(names, list)):
            return ([self.inputlist.get(x,"NotExist") for x in names])

    def getOutputs(self, names=None):  # 7
        """
        This method returns dict. The key is output names and value is corresponding output value.
        If name is None then the function will return dict which contain all output names as key and value as corresponding values. eg., getOutputs()
        usage:
        >>> getOutputs()
        >>> getOutputs("Name1")
        >>> getOutputs(["Name1","Name2"])
        """
        if not self.simulationFlag:
            if(names==None):
                return self.outputlist
            elif(isinstance(names, str)):
                return [self.outputlist.get(names,"NotExist")]
            else:
                return ([self.outputlist.get(x,"NotExist") for x in names])
        else:
            if (names== None):
                for i in self.outputlist:
                    value = self.getSolutions(i)
                    self.outputlist[i]=value[0][-1]
                return self.outputlist
            elif(isinstance(names, str)):
                 if names in self.outputlist:
                     value = self.getSolutions(names)
                     self.outputlist[names]=value[0][-1]
                     return [self.outputlist.get(names)]
                 else:
                     return (names, " is not Output")
            elif(isinstance(names, list)):
                valuelist=[]
                for i in names:
                    if i in self.outputlist:
                        value=self.getSolutions(i)
                        self.outputlist[i]=value[0][-1]
                        valuelist.append(value[0][-1])
                    else:
                        return (i, "is not Output")
                return valuelist

    def getSimulationOptions(self, names=None):  # 8
        """
        This method returns dict. The key is simulation option names and value is corresponding simulation option value.
        If name is None then the function will return dict which contain all simulation option names as key and value as corresponding values. eg., getSimulationOptions()
        usage:
        >>> getSimulationOptions()
        >>> getSimulationOptions("Name1")
        >>> getSimulationOptions(["Name1","Name2"])
        """
        if(names==None):
            return self.simulateOptions
        elif(isinstance(names, str)):
            return [self.simulateOptions.get(names,"NotExist")]
        elif(isinstance(names, list)):
            return ([self.simulateOptions.get(x,"NotExist") for x in names])

    def getLinearizationOptions(self, names=None):  # 9
        """
        This method returns dict. The key is linearize option names and value is corresponding linearize option value.
        If name is None then the function will return dict which contain all linearize option names as key and value as corresponding values. eg., getLinearizationOptions()
        usage:
        >>> getLinearizationOptions()
        >>> getLinearizationOptions("Name1")
        >>> getLinearizationOptions(["Name1","Name2"])
        """
        if(names==None):
            return self.linearOptions
        elif(isinstance(names, str)):
            return [self.linearOptions.get(names,"NotExist")]
        elif(isinstance(names, list)):
            return ([self.linearOptions.get(x,"NotExist") for x in names])

    def getOptimizationOptions(self, names=None):  # 10
        """
        usage:
        >>> getOptimizationOptions()
        >>> getOptimizationOptions("Name1")
        >>> getOptimizationOptions(["Name1","Name2"])
        """
        if(names==None):
            return self.optimizeOptions
        elif(isinstance(names, str)):
            return [self.optimizeOptions.get(names,"NotExist")]
        elif(isinstance(names, list)):
            return ([self.optimizeOptions.get(x,"NotExist") for x in names])

    # to simulate or re-simulate model
    def simulate(self, resultfile=None, simflags=None, verbose=True):  # 11
        """
        This method simulates model according to the simulation options.
        usage
        >>> simulate()
        >>> simulate(resultfile="a.mat")
        >>> simulate(simflags="-noEventEmit -noRestart -override=e=0.3,g=10) set runtime simulation flags
        """
        if(resultfile is None):
            r=""
            self.resultfile = os.path.join(self.tempdir, self.modelName + "_res.mat").replace("\\", "/")
        else:
            if os.path.exists(resultfile):
                r=" -r=" + resultfile
                self.resultfile = resultfile
            else:
                r=" -r=" + os.path.join(self.tempdir, resultfile).replace("\\", "/")
                self.resultfile = os.path.join(self.tempdir, resultfile).replace("\\", "/")

        # allow runtime simulation flags from user input
        if(simflags is None):
            simflags=""
        else:
            simflags=" " + simflags

        overrideFile = os.path.join(self.tempdir, '{}.{}'.format(self.modelName + "_override", "txt")).replace("\\", "/")
        if (self.overridevariables or self.simoptionsoverride):
            tmpdict=self.overridevariables.copy()
            tmpdict.update(self.simoptionsoverride)
            # write to override file
            file = open(overrideFile, "w")
            for (key, value) in tmpdict.items():
                name = key + "=" + value + "\n"
                file.write(name)
            file.close()
            override =" -overrideFile=" + overrideFile
        else:
            override =""

        if (self.inputFlag):  # if model has input quantities
            for i in self.inputlist:
                val=self.inputlist[i]
                if(val==None):
                    val=[(float(self.simulateOptions["startTime"]), 0.0), (float(self.simulateOptions["stopTime"]), 0.0)]
                    self.inputlist[i]=[(float(self.simulateOptions["startTime"]), 0.0), (float(self.simulateOptions["stopTime"]), 0.0)]
                if float(self.simulateOptions["startTime"]) != val[0][0]:
                    print("!!! startTime not matched for Input ",i)
                    return
                if float(self.simulateOptions["stopTime"]) != val[-1][0]:
                    print("!!! stopTime not matched for Input ",i)
                    return
                if val[0][0] < float(self.simulateOptions["startTime"]):
                    print('Input time value is less than simulation startTime for inputs', i)
                    return
            self.createCSVData()  # create csv file
            csvinput=" -csvInput=" + self.csvFile
        else:
            csvinput=""

        if (platform.system() == "Windows"):
            getExeFile = os.path.join(self.tempdir, '{}.{}'.format(self.modelName, "exe")).replace("\\", "/")
        else:
            getExeFile = os.path.join(self.tempdir, self.modelName).replace("\\", "/")
        currentDir = os.getcwd()
        if (os.path.exists(getExeFile)):
            cmd = getExeFile + override + csvinput + r + simflags
            cmd = cmd.split(" ")
            #print(cmd)
            os.chdir(self.tempdir)
            if (platform.system() == "Windows"):
                omhome = os.path.join(os.environ.get("OPENMODELICAHOME"))
                dllPath = os.path.join(omhome, "bin").replace("\\", "/") + os.pathsep + os.path.join(omhome, "lib/omc").replace("\\", "/") + os.pathsep + os.path.join(omhome, "lib/omc/cpp").replace("\\", "/") +  os.pathsep + os.path.join(omhome, "lib/omc/omsicpp").replace("\\", "/")
                my_env = os.environ.copy()
                my_env["PATH"] = dllPath + os.pathsep + my_env["PATH"]
                if not verbose:
                    p = subprocess.Popen(cmd, env=my_env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                else:
                    p = subprocess.Popen(cmd, env=my_env)
            else:
                if not verbose:
                    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                else:
                    p = subprocess.Popen(cmd)
            p.wait()
            p.terminate()
            os.chdir(currentDir)
            self.simulationFlag = True
        else:
            raise Exception("Error: Application file path not found: " +  getExeFile)

    # to extract simulation results
    def getSolutions(self, varList=None, resultfile=None):  # 12
        """
        This method returns tuple of numpy arrays. It can be called:
            •with a list of quantities name in string format as argument: it returns the simulation results of the corresponding names in the same order. Here it supports Python unpacking depending upon the number of variables assigned.
        usage:
        >>> getSolutions()
        >>> getSolutions("Name1")
        >>> getSolutions(["Name1","Name2"])
        >>> getSolutions(resultfile="c:/a.mat")
        >>> getSolutions("Name1",resultfile=""c:/a.mat"")
        >>> getSolutions(["Name1","Name2"],resultfile=""c:/a.mat"")
        """
        if (resultfile == None):
            resFile = self.resultfile
        else:
            resFile = resultfile

        # check for result file exits
        if (not os.path.exists(resFile)):
            print("Error: Result file does not exist " + resFile)
            return
            #exit()
        else:
            resultVars = self.getconn.sendExpression("readSimulationResultVars(\"" + resFile + "\")")
            self.getconn.sendExpression("closeSimulationResultFile()")
            if (varList == None):
                return resultVars
            elif (isinstance(varList,str)):
                if (varList not in resultVars and varList!="time"):
                    print('!!! ', varList, ' does not exist\n')
                    return
                exp = "readSimulationResult(\"" + resFile + '",{' + varList + "})"
                res = self.getconn.sendExpression(exp)
                npRes = np.array(res)
                exp2 = "closeSimulationResultFile()"
                self.getconn.sendExpression(exp2)
                return npRes
            elif (isinstance(varList, list)):
                #varList, = varList
                for v in varList:
                    if v == "time":
                        continue
                    if v not in resultVars:
                        print('!!! ', v, ' does not exist\n')
                        return
                variables = ",".join(varList)
                exp = "readSimulationResult(\"" + resFile + '",{' + variables + "})"
                res = self.getconn.sendExpression(exp)
                npRes = np.array(res)
                exp2 = "closeSimulationResultFile()"
                self.getconn.sendExpression(exp2)
                return npRes

    def strip_space(self,name):
        if(isinstance(name,str)):
            return name.replace(" ","")
        elif(isinstance(name,list)):
            return [x.replace(" ","") for x in name]

    def setMethodHelper(self,args1,args2,args3,args4=None,verbose=None):
        """
        Helper function for setParameter(),setContinuous(),setSimulationOptions(),setLinearizationOption(),setOptimizationOption()
        args1 - string or list of string given by user
        args2 - dict() containing the values of different variables(eg:, parameter,continuous,simulation parameters)
        args3 - function name (eg; continuous, parameter, simulation, linearization,optimization)
        args4 - dict() which stores the new override variables list,
        """
        if(isinstance(args1,str)):
            args1=self.strip_space(args1)
            value=args1.split("=")
            if value[0] in args2:
                if (args3 == "parameter" and self.isParameterChangeable(value[0], value[1], verbose)):
                    args2[value[0]]=value[1]
                    if(args4!=None):
                        args4[value[0]]=value[1]
                elif (args3 != "parameter"):
                    args2[value[0]]=value[1]
                    if(args4!=None):
                        args4[value[0]]=value[1]
            else:
                print("\"" + value[0] + "\"" + " is not a" +  args3 + " variable")
                return
        elif(isinstance(args1,list)):
            args1=self.strip_space(args1)
            for var in args1:
                value=var.split("=")
                if value[0] in args2:
                    if (args3 == "parameter" and self.isParameterChangeable(value[0], value[1], verbose)):
                        args2[value[0]]=value[1]
                        if(args4!=None):
                            args4[value[0]]=value[1]
                    elif (args3 != "parameter"):
                        args2[value[0]]=value[1]
                        if(args4!=None):
                            args4[value[0]]=value[1]
                else:
                    print("\"" + value[0] + "\"" + " is not a "+ args3 + " variable")

    def setContinuous(self, cvals):  # 13
        """
        This method is used to set continuous values. It can be called:
        with a sequence of continuous name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setContinuous("Name=value")
        >>> setContinuous(["Name1=value1","Name2=value2"])
        """
        return self.setMethodHelper(cvals,self.continuouslist,"continuous",self.overridevariables)

    def setParameters(self, pvals, verbose=True):  # 14
        """
        This method is used to set parameter values. It can be called:
        with a sequence of parameter name and assigning corresponding value as arguments as show in the example below:
        usage
        >>> setParameters("Name=value")
        >>> setParameters(["Name1=value1","Name2=value2"])
        """
        return self.setMethodHelper(pvals,self.paramlist,"parameter",self.overridevariables, verbose)

    def isParameterChangeable(self, name, value, verbose):
        q = self.getQuantities(name)
        if (q[0]["changeable"] == "false"):
            if verbose:
                print("| info |  setParameters() failed : It is not possible to set the following signal " + "\"" + name + "\"" + ", It seems to be structural, final, protected or evaluated or has a non-constant binding, use sendExpression(setParameterValue("+ self.modelName + ", " + name + ", " + value + "), parsed=false)" + " and rebuild the model using buildModel() API")
            return False
        return True

    def setSimulationOptions(self, simOptions):  # 16
        """
        This method is used to set simulation options. It can be called:
        with a sequence of simulation options name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setSimulationOptions("Name=value")
        >>> setSimulationOptions(["Name1=value1","Name2=value2"])
        """
        return self.setMethodHelper(simOptions,self.simulateOptions,"simulation-option",self.simoptionsoverride)

    def setLinearizationOptions(self, linearizationOptions):  # 18
        """
        This method is used to set linearization options. It can be called:
        with a sequence of linearization options name and assigning corresponding value as arguments as show in the example below
        usage
        >>> setLinearizationOptions("Name=value")
        >>> setLinearizationOptions(["Name1=value1","Name2=value2"])
        """
        return self.setMethodHelper(linearizationOptions,self.linearOptions,"Linearization-option",None)

    def setOptimizationOptions(self, optimizationOptions):  # 17
        """
        This method is used to set optimization options. It can be called:
        with a sequence of optimization options name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setOptimizationOptions("Name=value")
        >>> setOptimizationOptions(["Name1=value1","Name2=value2"])
        """
        return self.setMethodHelper(optimizationOptions,self.optimizeOptions,"optimization-option",None)

    def setInputs(self, name):  # 15
        """
        This method is used to set input values. It can be called:
        with a sequence of input name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setInputs("Name=value")
        >>> setInputs(["Name1=value1","Name2=value2"])
        """
        if (isinstance(name,str)):
            name=self.strip_space(name)
            value=name.split("=")
            if value[0] in self.inputlist:
                tmpvalue=eval(value[1])
                if(isinstance(tmpvalue,int) or  isinstance(tmpvalue, float)):
                    self.inputlist[value[0]] = [(float(self.simulateOptions["startTime"]), float(value[1])), (float(self.simulateOptions["stopTime"]), float(value[1]))]
                elif(isinstance(tmpvalue,list)):
                    self.checkValidInputs(tmpvalue)
                    self.inputlist[value[0]] = tmpvalue
                self.inputFlag=True
            else:
                print(value[0], "!is not an input")
        elif (isinstance(name,list)):
            name=self.strip_space(name)
            for var in name:
                value=var.split("=")
                if value[0] in self.inputlist:
                    tmpvalue=eval(value[1])
                    if(isinstance(tmpvalue,int) or  isinstance(tmpvalue, float)):
                        self.inputlist[value[0]] = [(float(self.simulateOptions["startTime"]), float(value[1])), (float(self.simulateOptions["stopTime"]), float(value[1]))]
                    elif(isinstance(tmpvalue,list)):
                        self.checkValidInputs(tmpvalue)
                        self.inputlist[value[0]] = tmpvalue
                    self.inputFlag=True
                else:
                    print(value[0], "!is not an input")

    def checkValidInputs(self,name):
        if name != sorted(name, key=lambda x: x[0]):
            print('Time value should be in increasing order')
            return
        for l in name:
            if isinstance(l, tuple):
                #if l[0] < float(self.simValuesList[0]):
                if l[0] < float(self.simulateOptions["startTime"]):
                    print('Input time value is less than simulation startTime')
                    return
                if len(l) != 2:
                    print('Value for ' + l + ' is in incorrect format!')
                    return
            else:
                print('Error!!! Value must be in tuple format')
                return

    # To create csv file for inputs
    def createCSVData(self):
        sl = list()  # Actual timestamps
        skip = False

        ## check for NONE in input list and replace with proper data (e.g) [(startTime, 0.0), (stopTime, 0.0)]
        tmpinputlist = {}
        for (key, value) in self.inputlist.items():
            if (value is None):
                tmpinputlist[key] = [(float(self.simulateOptions["startTime"]), 0.0),(float(self.simulateOptions["stopTime"]), 0.0)]
            else:
                tmpinputlist[key] = value

        inp = list(tmpinputlist.values())

        for i in inp:
            cl = list()
            el = list()
            for (t, x) in i:
                cl.append(t)
            for i in cl:
                if skip is True:
                    skip = False
                    continue
                if i not in sl:
                    el.append(i)
                else:
                    elem_no = cl.count(i)
                    sl_no = sl.count(i)
                    if elem_no == 2 and sl_no == 1:
                        el.append(i)
                        skip = True
            sl = sl + el

        sl.sort()
        for t in sl:
            for i in inp:
                for ttt in [tt[0] for tt in i]:
                    if t not in [tt[0] for tt in i]:
                        i.append((t, '?'))
        inpSortedList = list()
        sortedList = list()
        for i in inp:
            sortedList = sorted(i, key=lambda x: x[0])
            inpSortedList.append(sortedList)
        for i in inpSortedList:
            ind = 0
            for (t, x) in i:
                if x == '?':
                    t1 = i[ind - 1][0]
                    u1 = i[ind - 1][1]
                    t2 = i[ind + 1][0]
                    u2 = i[ind + 1][1]
                    nex = 2
                    while (u2 == '?'):
                        u2 = i[ind + nex][1]
                        t2 = i[ind + nex][0]
                        nex += 1
                    x = float(u1 + (u2 - u1) * (t - t1) / (t2 - t1))
                    i[ind] = (t, x)
                ind += 1
        slSet = list()
        slSet = set(sl)
        for i in inpSortedList:
            tempTime = list()
            for (t, x) in i:
                tempTime.append(t)
            inSl = None
            inI = None
            for s in slSet:
                inSl = sl.count(s)
                inI = tempTime.count(s)
                if inSl != inI:
                    test = list()
                    test = [(x, y) for x, y in i if x == s]
                    i.append(test[0])
        newInpList = list()
        tempSorting = list()
        for i in inpSortedList:
            # i.sort() => just sorting might not work so need to sort according to 1st element of a tuple
            tempSorting = sorted(i, key=lambda x: x[0])
            newInpList.append(tempSorting)

        interpolated_inputs_all = list()
        for i in newInpList:
            templist = list()
            for (t, x) in i:
                templist.append(x)
            interpolated_inputs_all.append(templist)

        name_ = 'time'
        #name = ','.join(self.__getInputNames())
        name=','.join(list(self.inputlist.keys()))
        name = '{},{},{}'.format(name_, name, 'end')

        a = ''
        l = []
        l.append(name)
        for i in range(0, len(sl)):
            a = ("%s,%s" % (str(float(sl[i])), ",".join(list(str(float(inppp[i])) for inppp in interpolated_inputs_all)))) + ',0'
            l.append(a)

        self.csvFile = os.path.join(self.tempdir, '{}.{}'.format(self.modelName, "csv")).replace("\\", "/")
        with open(self.csvFile, "w") as f:
            writer = csv.writer(f, delimiter='\n')
            writer.writerow(l)
        f.close()

    # to convert Modelica model to FMU
    def convertMo2Fmu(self, version="2.0", fmuType="me_cs", fileNamePrefix="<default>", includeResources=True):  # 19
        """
        This method is used to generate FMU from the given Modelica model. It creates "modelName.fmu" in the current working directory. It can be called:
        with no arguments
        with arguments of https://build.openmodelica.org/Documentation/OpenModelica.Scripting.translateModelFMU.html
        usage
        >>> convertMo2Fmu()
        >>> convertMo2Fmu(version="2.0", fmuType="me|cs|me_cs", fileNamePrefix="<default>", includeResources=true)
        """

        if fileNamePrefix == "<default>":
          fileNamePrefix = self.modelName
        if includeResources:
          includeResourcesStr = "true"
        else:
          includeResourcesStr = "false"
        properties = 'version="{}", fmuType="{}", fileNamePrefix="{}", includeResources={}'.format(version, fmuType, fileNamePrefix,includeResourcesStr)
        fmu = self.requestApi('buildModelFMU', self.modelName, properties)

        ## report proper error message
        if not os.path.exists(fmu):
            return print(self.getconn.sendExpression("getErrorString()"))

        return fmu

    # to convert FMU to Modelica model
    def convertFmu2Mo(self, fmuName):  # 20
        """
        In order to load FMU, at first it needs to be translated into Modelica model. This method is used to generate Modelica model from the given FMU. It generates "fmuName_me_FMU.mo".
        Currently, it only supports Model Exchange conversion.
        usage
        >>> convertFmu2Mo("c:/BouncingBall.Fmu")
        """

        fileName = self.requestApi('importFMU', fmuName)

        ## report proper error message
        if not os.path.exists(fileName):
            return print(self.getconn.sendExpression("getErrorString()"))

        return fileName

    # to optimize model
    def optimize(self):  # 21
        """
        This method optimizes model according to the optimized options. It can be called:
        only without any arguments
        usage
        >>> optimize()
        """
        cName = self.modelName
        properties = ','.join("%s=%s" % (key, val) for (key, val) in list(self.optimizeOptions.items()))
        optimizeError = ''
        self.getconn.sendExpression("setCommandLineOptions(\"-g=Optimica\")")
        optimizeResult = self.requestApi('optimize', cName, properties)
        optimizeError = self.requestApi('getErrorString')
        if optimizeError:
            print(optimizeError)

        return optimizeResult

    # to linearize model
    def linearize(self, lintime = None, simflags= None):  # 22
        """
        This method linearizes model according to the linearized options. This will generate a linear model that consists of matrices A, B, C and D.  It can be called:
        only without any arguments
        usage
        >>> linearize()
        """

        if self.xmlFile is None:
            return print("Linearization cannot be performed as the model is not build, use ModelicaSystem() to build the model first")

        overrideLinearFile = os.path.join(self.tempdir, '{}.{}'.format(self.modelName + "_override_linear", "txt")).replace("\\", "/")

        file = open(overrideLinearFile, "w")
        for (key, value) in self.overridevariables.items():
            name = key + "=" + value + "\n"
            file.write(name)
        for (key, value) in self.linearOptions.items():
            name = key + "=" + str(value) + "\n"
            file.write(name)
        file.close()

        override =" -overrideFile=" + overrideLinearFile
        # print(override)

        if self.inputFlag:
            nameVal = self.getInputs()
            for n in nameVal:
                tupleList = nameVal.get(n)
                if tupleList is not None:
                    for l in tupleList:
                        if l[0] < float(self.simulateOptions["startTime"]):
                            print('Input time value is less than simulation startTime')
                            return
            self.createCSVData()
            csvinput =" -csvInput=" + self.csvFile
        else:
            csvinput=""

        ## prepare the linearization runtime command
        if (platform.system() == "Windows"):
            getExeFile = os.path.join(self.tempdir, '{}.{}'.format(self.modelName, "exe")).replace("\\", "/")
        else:
            getExeFile = os.path.join(self.tempdir, self.modelName).replace("\\", "/")

        if lintime is None:
            linruntime = " -l=" + str(self.linearOptions["stopTime"])
        else:
            linruntime = " -l=" + lintime

        if simflags is None:
            simflags = ""

        currentDir = os.getcwd()
        if (os.path.exists(getExeFile)):
            cmd = getExeFile + linruntime + override + csvinput + simflags
            # print(cmd)
            os.chdir(self.tempdir)
            if (platform.system() == "Windows"):
                omhome = os.path.join(os.environ.get("OPENMODELICAHOME"))
                dllPath = os.path.join(omhome, "bin").replace("\\", "/") + os.pathsep + os.path.join(omhome, "lib/omc").replace("\\", "/") + os.pathsep + os.path.join(omhome, "lib/omc/cpp").replace("\\", "/") +  os.pathsep + os.path.join(omhome, "lib/omc/omsicpp").replace("\\", "/")
                my_env = os.environ.copy()
                my_env["PATH"] = dllPath + os.pathsep + my_env["PATH"]
                p = subprocess.Popen(cmd, env=my_env)
                p.wait()
                p.terminate()
            else:
                os.system(cmd)
        else:
            os.chdir(currentDir)
            raise Exception("Error: Application file path not found: " +  getExeFile)

        # code to get the matrix and linear inputs, outputs and states
        linearFile = os.path.join(self.tempdir, "linearized_model.py").replace("\\","/")

        # support older openmodelica versions before OpenModelica v1.16.2 where linearize() generates "linear_modelname.mo" file
        if not os.path.exists(linearFile):
            linearFile = '{}_{}.{}'.format('linear', self.modelName, 'py')

        if os.path.exists(linearFile):
            # this function is called from the generated python code linearized_model.py at runtime,
            # to improve the performance by directly reading the matrices A, B, C and D from the julia code and avoid building the linearized modelica model
            try:
                ## do not add the linearfile directory to path, as multiple execution of linearization will always use the first added path, instead execute the file
                ## https://github.com/OpenModelica/OMPython/issues/196
                module = importlib.machinery.SourceFileLoader("linearized_model", linearFile).load_module()
                result = module.linearized_model()
                (n, m, p, x0, u0, A, B, C, D, stateVars, inputVars, outputVars) = result
                self.linearinputs = inputVars
                self.linearoutputs = outputVars
                self.linearstates = stateVars
                return [A, B, C, D]
                os.chdir(currentDir)
            except:
                os.chdir(currentDir)
                raise Exception("ModuleNotFoundError: No module named 'linearized_model'")
        else:
            errormsg = self.getconn.sendExpression("getErrorString()")
            os.chdir(currentDir)
            return print("Linearization failed: ", "\"" , linearFile,"\"" ," not found \n", errormsg)


    def getLinearInputs(self):
        """
        function which returns the LinearInputs after Linearization is performed
        usage
        >>> getLinearInputs()
        """
        return self.linearinputs

    def getLinearOutputs(self):
        """
        function which returns the LinearInputs after Linearization is performed
        usage
        >>> getLinearOutputs()
        """
        return self.linearoutputs

    def getLinearStates(self):
        """
        function which returns the LinearInputs after Linearization is performed
        usage
        >>> getLinearStates()
        """
        return self.linearstates

def FindBestOMCSession(*args, **kwargs):
  """
  Analyzes the OMC executable version string to find a suitable selection
  of CORBA or ZMQ, as well as older flags to launch the executable (such
  as +d=interactiveCorba for RML-based OMC).

  This is mainly useful if you are testing old OpenModelica versions using
  the latest OMPython.
  """
  base = OMCSessionHelper()
  omc = base._get_omc_path()
  versionOK = False
  for cmd in ["--version", "+version"]:
    try:
      v = str(subprocess.check_output([omc, cmd], stderr=subprocess.STDOUT))
      versionOK = True
      break
    except subprocess.CalledProcessError:
      pass
  if not versionOK:
    raise Exception("Failed to use omc --version or omc +version. Is omc on the PATH?")
  zmq = False
  v = v.strip().split("-")[0].split("~")[0].strip()
  a = re.search(r"v?([0-9]+)[.]([0-9]+)[.][0-9]+", v)
  try:
    major = int(a.group(1))
    minor = int(a.group(2))
    if major > 1 or (major==1 and minor >= 12):
      zmq = True
  except:
    pass
  if zmq:
    return OMCSessionZMQ(*args, **kwargs)
  if cmd == "+version":
    return OMCSession(*args, serverFlag="+d=interactiveCorba", **kwargs)
  return OMCSession(*args, serverFlag="-d=interactiveCorba", **kwargs)
