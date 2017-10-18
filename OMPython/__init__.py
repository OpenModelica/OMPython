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
from distutils import spawn

import abc
import csv
import getpass
import logging
import os
import platform
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET

import numpy as np
import pyparsing


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


class OMCSessionBase(with_metaclass(abc.ABCMeta, object)):

    def __init__(self, readonly=False):
        self.readonly = readonly
        self.omc_cache = {}
        self._omc_process = None
        self._omc_command = None
        self._omc = None
        # FIXME: this code is not well written... need to be refactored
        self._temp_dir = tempfile.gettempdir()
        # generate a random string for this session
        self._random_string = uuid.uuid4().hex
        # omc log file
        self._omc_log_file = None

    def __del__(self):
        self.sendExpression("quit()")
        self._omc_log_file.close()
        # kill self._omc_process process if it is still running/exists
        if self._omc_process.returncode is None:
            self._omc_process.kill()

    def _create_omc_log_file(self, suffix):
        if sys.platform == 'win32':
            self._omc_log_file = open(os.path.join(self._temp_dir, "openmodelica.{0}.{1}.log".format(suffix, self._random_string)), 'w')
        else:
            self._currentUser = getpass.getuser()
            if not self._currentUser:
                self._currentUser = "nobody"
            # this file must be closed in the destructor
            self._omc_log_file = open(os.path.join(self._temp_dir, "openmodelica.{0}.{1}.{2}.log".format(self._currentUser, suffix, self._random_string)), 'w')

    def _start_omc_process(self):
        if sys.platform == 'win32':
            omhome_bin = os.path.join(self.omhome, 'bin').replace("\\", "/")
            my_env = os.environ.copy()
            my_env["PATH"] = omhome_bin + os.pathsep + my_env["PATH"]
            self._omc_process = subprocess.Popen(self._omc_command, shell=True, stdout=self._omc_log_file, stderr=self._omc_log_file, env=my_env)
        else:
            self._omc_process = subprocess.Popen(self._omc_command, shell=True, stdout=self._omc_log_file, stderr=self._omc_log_file)
        return self._omc_process

    def _set_omc_command(self, omc_path, args):
        self._omc_command = "{0} {1}".format(omc_path, args)
        return self._omc_command

    def _get_omc_path(self):
        try:
            self.omhome = os.environ.get('OPENMODELICAHOME')
            if self.omhome is None:
                self.omhome = os.path.split(os.path.split(os.path.realpath(spawn.find_executable("omc")))[0])[0]
            elif os.path.exists('/opt/local/bin/omc'):
                self.omhome = '/opt/local'
            return os.path.join(self.omhome, 'bin', 'omc')
        except BaseException:
            logger.error("The OpenModelica compiler is missing in the System path (%s), please install it" % os.path.join(self.omhome, 'bin', 'omc'))
            raise

    @abc.abstractmethod
    def _connect_to_omc(self):
        pass

    # FIXME: we should have one function which interacts with OMC. Either execute OR sendExpression.
    # Execute uses OMParser.check_for_values and sendExpression uses OMTypedParser.parseString.
    # We should have one parser. Then we can get rid of one of these functions.
    @abc.abstractmethod
    def execute(self, command):
        pass

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
                res = self._omc.sendExpression(expression)
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
            logger.warning('OMPython error: {0}'.format(ex.message))
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
                logger.warning('OMParser error: {0}'.format(ex.message))
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
                logger.warning('OMParser error: {0}'.format(ex.message))
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
                             'recursive={1}, qualified={2}, sort={3}, builtin={4}, showProtected={5}'.format(
                                 str(recursive).lower(), str(qualified).lower(), str(sort).lower(),
                                 str(builtin).lower(), str(showProtected).lower()))
        return value


class OMCSession(OMCSessionBase):

    def __init__(self, readonly=False):
        OMCSessionBase.__init__(self, readonly)
        self._create_omc_log_file("objid")
        # set omc executable path and args
        self._set_omc_command(self._get_omc_path(), "--interactive=corba +c={0}".format(self._random_string))
        # start up omc executable, which is waiting for the CORBA connection
        self._start_omc_process()
        # connect to the running omc instance using CORBA
        self._connect_to_omc()

    def __del__(self):
        OMCSessionBase.__del__(self)

    def _connect_to_omc(self):
        # add OPENMODELICAHOME\lib\python to PYTHONPATH so python can load omniORB imports
        sys.path.append(os.path.join(self.omhome, 'lib', 'python'))
        # import the skeletons for the global module
        from omniORB import CORBA
        from OMPythonIDL import _OMCIDL
        # Locating and using the IOR
        if sys.platform == 'win32':
            self._ior_file = "openmodelica.objid." + self._random_string
        else:
            self._ior_file = "openmodelica." + self._currentUser + ".objid." + self._random_string
        self._ior_file = os.path.join(self._temp_dir, self._ior_file).replace("\\", "/")
        self._omc_corba_uri = "file:///" + self._ior_file
        # See if the omc server is running
        if os.path.isfile(self._ior_file):
            logger.info("OMC Server is up and running at {0}".format(self._omc_corba_uri))
        else:
            attempts = 0
            while True:
                if not os.path.isfile(self._ior_file):
                    time.sleep(0.25)
                    attempts += 1
                    if attempts == 10:
                        name = self._omc_log_file.name
                        self._omc_log_file.close()
                        logger.error("OMC Server is down. Please start it! Log-file says:\n%s" % open(name).read())
                        raise Exception
                    else:
                        continue
                else:
                    logger.info("OMC Server is up and running at {0}".format(self._omc_corba_uri))
                    break

        # initialize the ORB with maximum size for the ORB set
        sys.argv.append("-ORBgiopMaxMsgSize")
        sys.argv.append("2147483647")
        self._orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        # Read the IOR file
        with open(self._ior_file, 'r') as f_p:
            self._ior = f_p.readline()

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
        if self._omc is not None:
            result = self._omc.sendExpression(command)
            if command == "quit()":
                self._omc = None
                return result
            else:
                answer = OMParser.check_for_values(result)
                return answer
        else:
            return "No connection with OMC. Create an instance of OMCSession."

    def sendExpression(self, command, parsed=True):
        if self._omc is not None:
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
            return "No connection with OMC. Create an instance of OMCSession."


class OMCSessionZMQ(OMCSessionBase):

    def __init__(self, readonly=False):
        OMCSessionBase.__init__(self, readonly)
        self._create_omc_log_file("port")
        # set omc executable path and args
        self._set_omc_command(self._get_omc_path(), "--interactive=zmq +z={0}".format(self._random_string))
        # start up omc executable, which is waiting for the CORBA connection
        self._start_omc_process()
        # connect to the running omc instance using CORBA
        self._connect_to_omc()

    def __del__(self):
        OMCSessionBase.__del__(self)

    def _connect_to_omc(self):
        # Locating and using the IOR
        if sys.platform == 'win32':
            self._port_file = "openmodelica.port." + self._random_string
        else:
            self._port_file = "openmodelica." + self._currentUser + ".port." + self._random_string
        self._port_file = os.path.join(self._temp_dir, self._port_file).replace("\\", "/")
        self._omc_zeromq_uri = "file:///" + self._port_file
        # See if the omc server is running
        if os.path.isfile(self._port_file):
            logger.info("OMC Server is up and running at {0}".format(self._omc_zeromq_uri))
        else:
            attempts = 0
            while True:
                if not os.path.isfile(self._port_file):
                    time.sleep(0.25)
                    attempts += 1
                    if attempts == 10:
                        name = self._omc_log_file.name
                        self._omc_log_file.close()
                        logger.error("OMC Server is down. Please start it! Log-file says:\n%s" % open(name).read())
                        raise Exception
                    else:
                        continue
                else:
                    logger.info("OMC Server is up and running at {0}".format(self._omc_zeromq_uri))
                    break

        # Read the port file
        with open(self._port_file, 'r') as f_p:
            self._port = f_p.readline()

        # Create the ZeroMQ socket and connect to OMC server
        import zmq
        context = zmq.Context.instance()
        self._omc = context.socket(zmq.REQ)
        self._omc.connect(self._port)

    def execute(self, command):
        if self._omc is not None:
            self._omc.send_string(command)
            result = self._omc.recv_string()
            if command == "quit()":
                self._omc.close()
                self._omc = None
                return result
            else:
                answer = OMParser.check_for_values(result)
                return answer
        else:
            return "No connection with OMC. Create an instance of OMCSessionZMQ."

    def sendExpression(self, command, parsed=True):
        if self._omc is not None:
            self._omc.send_string(str(command))
            result = self._omc.recv_string()
            if command == "quit()":
                self._omc.close()
                self._omc = None
                return result
            else:
                if parsed is True:
                    answer = OMTypedParser.parseString(result)
                    return answer
                else:
                    return result
        else:
            return "No connection with OMC. Create an instance of OMCSessionZMQ."

# author = Sudeep Bajracharya
# sudba156@student.liu.se
# LIU(Department of Computer Science)


class Quantity(object):
    """
    To represent quantities details
    """

    def __init__(self, name, start, changable, variability, description, causality, alias, aliasvariable):
        self.name = name
        self.start = start
        self.changable = changable
        self.description = description
        self.variability = variability
        self.causality = causality
        self.alias = alias
        self.aliasvariable = aliasvariable


class ModelicaSystem(object):
    def __init__(self, fileName=None, modelName=None, lmodel=None, useCorba=False):  # 1
        """
        "constructor"
        It initializes to load file and build a model, generating object, exe, xml, mat, and json files. etc. It can be called :
            •without any arguments: In this case it neither loads a file nor build a model. This is useful when a FMU needed to convert to Modelica model
            •with two arguments as file name with ".mo" extension and the model name respectively
            •with three arguments, the first and second are file name and model name respectively and the third arguments is Modelica standard library to load a model, which is common in such models where the model is based on the standard library. For example, here is a model named "dcmotor.mo" below table 4-2, which is located in the directory of OpenModelica at "C:\OpenModelica1.9.4-dev.beta2\share\doc\omc\testmodels".
        Note: If the model file is not in the current working directory, then the path where file is located must be included together with file name. Besides, if the Modelica model contains several different models within the same package, then in order to build the specific model, in second argument, user must put the package name with dot(.) followed by specific model name.
        ex: myModel = ModelicaSystem("ModelicaModel.mo", "modelName")
        """

        if fileName is None and modelName is None and lmodel is None:  # all None
            if useCorba:
                self.getconn = OMCSession()
            else:
                self.getconn = OMCSessionZMQ()
            return

        if fileName is None:
            return "File does not exist"
        self.tree = None

        self.linearquantitiesList = []  # linearization  quantity list
        self.linearinputs = []  # linearization input list
        self.linearoutputs = []  # linearization output list
        self.linearstates = []  # linearization  states list
        self.quantitiesList = []  # detail list of all Modelica quantity variables inc. name, changable, description, etc
        self.qNamesList = []  # for all quantities name list
        self.cNamesList = []  # for continuous quantities name list
        self.cValuesList = []  # for continuous quantities value list
        self.iNamesList = []  # for input quantities name list
        self.inputsVal = []  # for input quantities value list
        self.specialNames = []
        self.oNamesList = []  # for output quantities name list
        self.pNamesList = []  # for parameter quantities name list
        self.pValuesList = []  # for parameter quantities value list
        self.oValuesList = []  # for output quantities value list
        self.simNamesList = ['startTime', 'stopTime', 'stepSize', 'tolerance', 'solver']  # simulation options list
        self.simValuesList = []  # for simulation values list
        self.optimizeOptionsNamesList = ['startTime', 'stopTime', 'numberOfIntervals', 'stepSize', 'tolerance']
        self.optimizeOptionsValuesList = [0.0, 1.0, 500, 0.002, 1e-8]
        self.linearizeOptionsNamesList = ['startTime', 'stopTime', 'numberOfIntervals', 'stepSize', 'tolerance']
        self.linearizeOptionsValuesList = [0.0, 1.0, 500, 0.002, 1e-8]
        if useCorba:
            self.getconn = OMCSession()
        else:
            self.getconn = OMCSessionZMQ()
        self.xmlFile = None
        self.lmodel = lmodel  # may be needed if model is derived from other model
        self.modelName = modelName  # Model class name
        self.fileName = fileName  # Model file/package name
        self.inputFlag = False  # for model with input quantity
        self.simulationFlag = False  # if the model is simulated?
        self.linearizationFlag = False
        self.outputFlag = False
        self.csvFile = ''  # for storing inputs condition
        if not os.path.exists(self.fileName):  # if file does not eixt
            print("File Error:" + os.path.abspath(self.fileName) + " does not exist!!!")
            return

        (head, tail) = os.path.split(self.fileName)  # to store directory/path and file)
        self.currDir = os.getcwd()
        self.modelDir = head
        self.fileName_ = tail

        if not self.modelDir:
            file_ = os.path.exists(self.fileName_)
            if (file_):  # execution from path where file is located
                self.__loadingModel(self.fileName_, self.modelName, self.lmodel)
            else:
                print("Error: File does not exist!!!")

        else:
            os.chdir(self.modelDir)
            file_ = os.path.exists(self.fileName_)
            self.model = self.fileName_[:-3]
            if (self.fileName_):  # execution from different path
                os.chdir(self.currDir)
                self.__loadingModel(self.fileName, self.modelName, self.lmodel)
            else:
                print("Error: File does not exist!!!")

    def __del__(self):
        if self.getconn is not None:
            self.requestApi('quit')

    # for loading file/package, loading model and building model
    def __loadingModel(self, fName, mName, lmodel):
        # load file
        loadfileError = ''
        loadfileResult = self.requestApi("loadFile", fName)
        loadfileError = self.requestApi("getErrorString")
        if loadfileError:
            specError = 'Parser error: Unexpected token near: optimization (IDENT)'
            if specError in loadfileError:
                self.requestApi("setCommandLineOptions", '"+g=Optimica"')
                self.requestApi("loadFile", fName)
            else:
                print('loadFile Error: ' + loadfileError)
                return

        # load Modelica standard libraries if needed
        if lmodel is not None:
            loadmodelError = ''
            loadModelResult = self.requestApi("loadModel", lmodel)
            loadmodelError = self.requestApi('getErrorString')
            if loadmodelError:
                print(loadmodelError)
                return

        # build model
        # buildModelError = ''
        self.getconn.sendExpression("setCommandLineOptions(\"+d=initialization\")")
        # buildModelResult=self.getconn.sendExpression("buildModel("+ mName +")")
        buildModelResult = self.requestApi("buildModel", mName)
        buildModelError = self.requestApi("getErrorString")

        if ('' in buildModelResult):
            print(buildModelError)
            return

        self.xmlFile = buildModelResult[1]
        self.tree = ET.parse(self.xmlFile)
        self.root = self.tree.getroot()
        self.__createQuantitiesList()  # initialize quantitiesList
        self.__getQuantitiesNames()  # initialize qNamesList
        self.__getContinuousNames()  # initialize cNamesList
        self.__getParameterNames()  # initialize pNamesList
        self.__getInputNames()  # initialize iNamesList
        self.__setInputSize()  # defing input value list size
        self.__getOutputNames()  # initialize oNamesList
        self.__getContinuousValues()  # initialize cValuesList
        self.__getParameterValues()  # initialize pValuesList
        self.__getInputValues()  # initialize input value list
        self.__getOutputValues()  # initialize oValuesList
        self.__getSimulationValues()  # initialize simulation value list

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

    # create detail quantities list
    def __createQuantitiesList(self):
        rootCQ = self.root
        if not self.quantitiesList:
            for sv in rootCQ.iter('ScalarVariable'):
                name = sv.get('name')
                changable = sv.get('isValueChangeable')
                description = sv.get('description')
                variability = sv.get('variability')
                causality = sv.get('causality')
                alias = sv.get('alias')
                aliasvariable = sv.get('aliasVariable')
                ch = sv.getchildren()
                start = None
                for att in ch:
                    start = att.get('start')
                self.quantitiesList.append(Quantity(name, start, changable, variability, description, causality, alias, aliasvariable))
        return self.quantitiesList

    # to get list of all quantities names
    def __getQuantitiesNames(self):
        if not self.qNamesList:
            for q in self.quantitiesList:
                self.qNamesList.append(q.name)
        return self.qNamesList

    # check if names exist
    def __checkAvailability(self, names, chkList, inputFlag=None):
        try:
            if isinstance(names, list):
                nonExistingList = []
                for n in names:
                    if n not in chkList:
                        nonExistingList.append(n)
                if nonExistingList:
                    print('Error!!! ' + str(nonExistingList) + ' does not exist.')
                    return False
            elif isinstance(names, str):
                if names not in chkList:
                    print('Error!!! ' + names + ' does not exist.')
                    return False
            else:
                print('Error!!! Incorrect format')
                return False
            return True

        except Exception as e:
            print(e)

    # to get details of quantities names
    def getQuantities(self, names=None):  # 3
        """
        This method returns list of dictionaries. It displays details of quantities such as name, value, changeable, and description, where changeable means  if value for corresponding quantity name is changeable or not. It can be called :
            •without argument: it returns list of dictionaries of all quantities
            •with a single argument as list of quantities name in string format: it returns list of dictionaries of only particular quantities name
            •a single argument as a single quantity name (or in list) in string format: it returns list of dictionaries of the particular quantity name
        """

        try:
            if names is not None:
                checking = self.__checkAvailability(names, self.qNamesList)
                if not checking:
                    return
                if isinstance(names, str):
                    qlistnames = []
                    for q in self.quantitiesList:
                        if names == q.name:
                            qlistnames.append({'Name': q.name, 'Value': q.start, 'Changeable': q.changable, 'Variability': q.variability, 'alias': q.alias, 'aliasvariable': q.aliasvariable, 'Description': q.description})
                            break
                    return qlistnames
                elif isinstance(names, list):
                    qlist = []
                    for n in names:
                        for q in self.quantitiesList:
                            if n == q.name:
                                qlist.append({'Name': q.name, 'Value': q.start, 'Changeable': q.changable, 'Variability': q.variability, 'alias': q.alias, 'aliasvariable': q.aliasvariable, 'Description': q.description})
                                break
                    return qlist
                else:
                    print('Error!!! Incorrect format')
            else:
                qlist = []
                for q in self.quantitiesList:
                    qlist.append({'Name': q.name, 'Value': q.start, 'Changeable': q.changable, 'Variability': q.variability, 'alias': q.alias, 'aliasvariable': q.aliasvariable, 'Description': q.description})
                return qlist
        except Exception as e:
            print(e)

    # to get list of quantities name that are continuous variability
    def __getContinuousNames(self):
        """
        This method returns list of quantities name that are continuous. It can be called:
            •only without any arguments: returns the list of quantities (continuous) names
        """
        if not self.cNamesList:
            for l in self.quantitiesList:
                if (l.variability == "continuous"):
                    self.cNamesList.append(l.name)
        return self.cNamesList

    def __checkTuple(self, names, chkList, inputFlag=None):
        if isinstance(names, tuple) and (len(n) == 1 for n in names):
            nonExistingList = []
            for n in names:
                if n not in chkList:
                    nonExistingList.append(n)
            if nonExistingList:
                print('Error!!!' + str(nonExistingList) + ' does not exist.')
                return False
            return True
        else:
            print('Error!!! Incorrect format')
            return False

    def getContinuous(self, *names):  # 4
        """
        This method returns dict. The key is continuous names and value is corresponding continuous value.
        If *name is None then the function will return dict which contain all continuous names as key and value as corresponding values. eg., getContinuous()
        Otherwise variable number of arguments can be passed as continuous name in string format separated by commas. eg., getContinuous('cName1', 'cName2')
        """

        try:
            if not self.simulationFlag:
                return self.__getXXXs(names, self.__getContinuousNames(), self.__getContinuousValues())
            else:
                if len(names) == 0:
                    cQuantities = self.__getContinuousNames()
                    cTuple = tuple(cQuantities)
                    cSol = self.getSolutions(cTuple)
                    cDict = dict()
                    for name, val in zip(cQuantities, cSol):
                        cDict[name] = val[-1]
                    return cDict
                else:
                    checking = self.__checkTuple(names, self.__getContinuousNames())
                    if not checking:
                        return
                    cSol = self.getSolutions(names)
                    cList = list()
                    for val in cSol:
                        cList.append(val[-1])
                        tupVal = tuple(cList)
                        if len(tupVal) == 1:
                            tupVal, = tupVal
                    return tupVal

        except Exception:
            if pyparsing.ParseException:
                print('Error!!! Name does not exist or incorrect format ')
            else:
                raise

    def getParameters(self, *names):  # 5
        """
        This method returns dict. The key is parameter names and value is corresponding parameter value.
        If *name is None then the function will return dict which contain all parameter names as key and value as corresponding values. eg., getParameters()
        Otherwise variable number of arguments can be passed as parameter name in string format separated by commas. eg., getParameters('paraName1', 'paraName2')
        """
        return self.__getXXXs(names, self.__getParameterNames(), self.__getParameterValues())

    def getInputs(self, *names):  # 6
        """
        This method returns dict. The key is input names and value is corresponding input value.
        If *name is None then the function will return dict which contain all input names as key and value as corresponding values. eg., getInputs()
        Otherwise variable number of arguments can be passed as input name in string format separated by commas. eg., getInputs('iName1', 'iName2')
        """
        return self.__getXXXs(names, self.__getInputNames(), self.__getInputValues())

    def getOutputs(self, *names):  # 7
        """
        This method returns dict. The key is output names and value is corresponding output value.
        If *name is None then the function will return dict which contain all output names as key and value as corresponding values. eg., getOutputs()
        Otherwise variable number of arguments can be passed as output name in string format separated by commas. eg., getOutputs(opName1', 'opName2')
        """

        try:
            if not self.simulationFlag:
                return self.__getXXXs(names, self.__getOutputNames(), self.__getOutputValues())

            else:
                if len(names) == 0:
                    op = self.__getOutputNames()
                    opTuple = tuple(op)
                    opSol = self.getSolutions(opTuple)
                    opDict = dict()
                    for name, val in zip(op, opSol):
                        opDict[name] = val[-1]
                    return opDict
                else:
                    checking = self.__checkTuple(names, self.__getOutputNames())
                    if not checking:
                        return
                    opSol = self.getSolutions(names)
                    opList = list()

                    for val in opSol:
                        opList.append(val[-1])
                        tupVal = tuple(opList)
                        if len(tupVal) == 1:
                            tupVal, = tupVal
                    return tupVal
            # else:
                # print ('The model is not simulated yet!!!')

        except Exception:
            if pyparsing.ParseException:
                print('Error!!! Name does not exist or incorrect format ')
            else:
                raise

    def __getParameterNames(self):
        """
        This method returns list of quantities name that are parameters. It can be called:
            •only without any arguments: returns list of quantities (parameter) name
        """

        if not self.pNamesList:
            for l in self.quantitiesList:
                if (l.variability == "parameter"):
                    self.pNamesList.append(l.name)
        return self.pNamesList

    # to get list of quantities name that are input
    def __getInputNames(self):
        """
        This method returns list of quantities name that are inputs. It can be called:
            •only without any arguments: returns the list of quantities (input) name
        """

        if not self.iNamesList:
            for l in self.quantitiesList:
                if (l.causality == "input"):
                    self.iNamesList.append(l.name)
        return self.iNamesList

    # set input value list size
    def __setInputSize(self):
        size = len(self.__getInputNames())
        self.inputsVal = [None] * size

    # to get list of quantities name that are output
    # Todo: has not been tested yet due to lack of the model that contains output.

    def __getOutputNames(self):
        """
        This method returns list of quantities name that are outputs. It can be called:
            •only without any arguments: returns the list of all quantities (output) name
        Note: Test has not been carried out for Output quantities due to the lack of model that contains output
        """

        if not self.oNamesList:
            for l in self.quantitiesList:
                if (l.causality == "output"):
                    self.oNamesList.append(l.name)
        return self.oNamesList

    # to get values of continuous quantities name
    def __getContinuousValues(self, contiName=None):
        """
        This method returns list of values of the quantities name that are continuous. It can be called:
            •without any arguments: returns list of values of all quantities name that are continuous
            •with a single argument as continuous name in string format: returns value of the corresponding name
            •with a single argument as list of continuous names in string format: return list of values of the corresponding names.
                1.If the list of names is more than one and it is being assigned by single variable then it returns the list of values of the corresponding names.
                2.If the list of names is more than one and it is being assigned by same number of variable as the number of element in the list then it will return the value to the variables correspondingly (python unpacking)
        """

        if contiName is None:
            if not self.cValuesList:
                for l in self.quantitiesList:
                    if (l.variability == "continuous"):
                        str_ = l.start
                        if str_ is None:
                            self.cValuesList.append(str_)
                        else:
                            self.cValuesList.append(float(str_))
            return self.cValuesList
        else:
            try:
                # if isinstance(contiName, list):
                checking = self.__checkAvailability(contiName, self.__getContinuousNames())
                # if checking is False:
                if not checking:
                    return
                if isinstance(contiName, str):
                    index_ = self.cNamesList.index(contiName)
                    return (self.cValuesList[index_])
                valList = []
                for n in contiName:
                    index_ = self.cNamesList.index(n)
                    valList.append(self.cValuesList[index_])
                return valList
            except Exception as e:
                print(e)

    # to get values of parameter quantities name
    def __getParameterValues(self, paraName=None):
        """
        This method returns list of values of the quantities name that are parameters. It can be called:
            •without any arguments: return list of values of all quantities (parameter) name
            •with a single argument as parameter name in string format: returns value of the corresponding name
            •with a single argument as list of parameter names in string format: return list of values of the corresponding names.
                1.If the list of names is more than one and it is being assigned by single variable then it returns the list of values of the corresponding names
                2.If the list of names is more than one and it is being assigned by same number of variable as the number of element in the list then it will return the value to the variables correspondingly (python unpacking)
        """

        if paraName is None:
            if not self.pValuesList:
                for l in self.quantitiesList:
                    if (l.variability == "parameter"):
                        str_ = l.start
                        if ((str_ is None) or (str_ == 'true' or str_ == 'false')):
                            if (str_ == 'true'):
                                str_ = True
                            elif str_ == 'false':
                                str_ = False
                            self.pValuesList.append(str_)
                        else:
                            self.pValuesList.append(float(str_))
            return self.pValuesList
        else:
            try:
                checking = self.__checkAvailability(paraName, self.__getParameterNames())
                if not checking:
                    return
                if isinstance(paraName, str):
                    index_ = self.pNamesList.index(paraName)
                    return (self.pValuesList[index_])
                valList = []
                for n in paraName:
                    index_ = self.pNamesList.index(n)
                    valList.append(self.pValuesList[index_])
                return valList
            except Exception as e:
                print(e)

    # to get values of input names
    def __getInputValues(self, iName=None):
        """
        This method returns list of values of the quantities name that are inputs. It can be called:
            •without any arguments: returns list of values of all quantities (input) name
            •with a single argument as input name in string format: returns list of values of the corresponding name
        """

        try:
            if iName is None:
                return self.inputsVal
            elif isinstance(iName, str):
                checking = self.__checkAvailability(iName, self.__getInputNames())
                if not checking:
                    return
                index_ = self.iNamesList.index(iName)
                return self.inputsVal[index_]
            else:
                print('Error!!! Incorrect format')
        except Exception as e:
            print(e)

    # to get values of output quantities name
    # Todo: has not been tested yet due to lack of the model that contains output.
    def __getOutputValues(self):
        """
        This method returns list of values of the quantities name that are outputs. It can be called:
            •only without any arguments: returns the list of values of all output name
        Note: Test has not been carried out for Output quantities due to the lack of model that contains output
        """

        if not self.oValuesList:
            for l in self.quantitiesList:
                if (l.causality == "output"):
                    self.oValuesList.append(l.start)
        return self.oValuesList

    # to get simulation options values
    def __getSimulationValues(self):
        if not self.simValuesList:
            root = self.tree.getroot()
            rootGSV = self.root
            for attr in rootGSV.iter('DefaultExperiment'):
                startTime = attr.get('startTime')
                self.simValuesList.append(float(startTime))
                stopTime = attr.get('stopTime')
                self.simValuesList.append(float(stopTime))
                stepSize = attr.get('stepSize')
                self.simValuesList.append(float(stepSize))
                tolerance = attr.get('tolerance')
                self.simValuesList.append(float(tolerance))
                solver = attr.get('solver')
                self.simValuesList.append(solver)
        return self.simValuesList

    def getSimulationOptions(self, *names):  # 8
        """
        This method returns dict. The key is simulation option names and value is corresponding simulation option value.
        If *name is None then the function will return dict which contain all simulation option names as key and value as corresponding values. eg., getSimulationOptions()
        Otherwise variable number of arguments can be passed as simulation option name in string format separated by commas. eg., getSimulationOptions('simName1', 'simName2')
        """
        return self.__getXXXs(names, self.simNamesList, self.simValuesList)

    def getLinearizationOptions(self, *names):  # 9
        """
        This method returns dict. The key is linearize option names and value is corresponding linearize option value.
        If *name is None then the function will return dict which contain all linearize option names as key and value as corresponding values. eg., getLinearizationOptions()
        Otherwise variable number of arguments can be passed as simulation option name in string format separated by commas. eg., getLinearizationOptions('linName1', 'linName2')
        """
        return self.__getXXXs(names, self.linearizeOptionsNamesList, self.linearizeOptionsValuesList)

    def __getXXXs(self, names, namesList, valList):
        # todo: check_Tuple is not working for tuple format
        if not self.linearizationFlag:
            checking = self.__checkTuple(names, namesList)
            if not checking:
                return
        try:
            if len(names) == 0:
                xxxDict = dict()
                for name, val in zip(namesList, valList):
                    try:
                        if float(val) or float(val) == 0.0:
                            xxxDict[name] = float(val)
                    except Exception:
                        if ValueError:
                            xxxDict[name] = val
                return xxxDict
            elif len(names) > 1:
                val = []
                for n in names:
                    index_ = namesList.index(n)
                    val.append(valList[index_])
                tupVal = tuple(val)
                return tupVal
            elif len(names) == 1:
                n, = names
                if (hasattr(n, '__iter__')):
                    val = []
                    for i in n:
                        index_ = namesList.index(i)
                        val.append(valList[index_])
                    tupVal = tuple(val)
                    return tupVal
                else:
                    index_ = namesList.index(n)
                    return valList[index_]
        except ValueError as e:
            print(e)

    def getOptimizationOptions(self, *names):  # 10
        return self.__getXXXs(names, self.optimizeOptionsNamesList, self.optimizeOptionsValuesList)

    # to simulate or re-simulate model
    def simulate(self):  # 11
        """
        This method simulates model according to the simulation options. It can be called:
            •only without any arguments: simulate the model
        """
        # if (self.inputFlag == True):
        if (self.inputFlag):  # if model has input quantities
            inpVal = self.__getInputValues()
            ind = 0
            for i in inpVal:
                if self.simValuesList[0] != i[0][0] or self.simValuesList[1] != i[-1][0]:
                    inpName = self.iNamesList[ind]
                    print('!!! startTime / stopTime not defined for Input ' + inpName)
                    return
                ind += 1
            nameVal = self.getInputs()
            for n in nameVal:
                tupleList = nameVal.get(n)
                for l in tupleList:
                    if l[0] < float(self.simValuesList[0]):
                        print('Input time value is less than simulation startTime')
                        return
            self.__simInput()  # create csv file

            if (platform.system() == "Windows"):
                getExeFile = os.path.join(os.getcwd(), '{}.{}'.format(self.modelName, "exe")).replace("\\", "/")
            else:
                getExeFile = os.path.join(os.getcwd(), self.modelName).replace("\\", "/")

            # getExeFile = '{}.{}'.format(self.modelName)

            check_exeFile_ = os.path.exists(getExeFile)
            if (check_exeFile_):
                cmd = getExeFile + " -csvInput=" + self.csvFile
                if (platform.system() == "Windows"):
                    omhome = os.path.join(os.environ.get("OPENMODELICAHOME"), 'bin').replace("\\", "/")
                    my_env = os.environ.copy()
                    my_env["PATH"] = omhome + os.pathsep + my_env["PATH"]
                    p = subprocess.Popen(cmd, env=my_env)
                    p.wait()
                    p.terminate()
                else:
                    os.system(cmd)
                # subprocess.call(cmd, shell = False)
                self.simulationFlag = True
                resultfilename = self.modelName + '_res.mat'
                return
            else:
                print("Error: application file not generated yet")
                return
        else:
            if (platform.system() == "Windows"):
                getExeFile = os.path.join(os.getcwd(), '{}.{}'.format(self.modelName, "exe")).replace("\\", "/")
            else:
                getExeFile = os.path.join(os.getcwd(), self.modelName).replace("\\", "/")
                # getExeFile = '{}.{}'.format(self.modelName, "exe")

            check_exeFile_ = os.path.exists(getExeFile)

            if (check_exeFile_):
                cmd = getExeFile
                if (platform.system() == "Windows"):
                    omhome = os.path.join(os.environ.get("OPENMODELICAHOME"), 'bin').replace("\\", "/")
                    my_env = os.environ.copy()
                    my_env["PATH"] = omhome + os.pathsep + my_env["PATH"]
                    p = subprocess.Popen(cmd, env=my_env)
                    p.wait()
                    p.terminate()
                else:
                    os.system(cmd)
                self.simulationFlag = True
                # self.outputFlag = True
                resultfilename = self.modelName + '_res.mat'
                return
            else:
                print("Error: application file not generated yet")

    # to extract simulation results
    def getSolutions(self, *varList):  # 12
        """
        This method returns tuple of numpy arrays. It can be called:
            •with a list of quantities name in string format as argument: it returns the simulation results of the corresponding names in the same order. Here it supports Python unpacking depending upon the number of variables assigned.
        """
        # check for result file exits
        res_mat = '_res.mat'
        resFile = "".join([self.modelName, res_mat])
        if (not os.path.exists(resFile)):
            print("Error: Result file does not exist")
            exit()
        else:
            if len(varList) == 0:
                # validSolution = ['time'] + self.__getInputNames() + self.__getContinuousNames() + self.__getParameterNames()
                validSolution = self.getconn.sendExpression("readSimulationResultVars(\"" + resFile + "\")")
                return validSolution

            # if isinstance(varList, tuple) and all(len(a)==1 for a in varList):
            elif isinstance(varList, tuple) and all(isinstance(a, str) for a in varList):
                for v in varList:
                    if v == 'time':
                        continue
                    if v not in [l.name for l in self.quantitiesList]:
                        print('!!! ', v, ' does not exist\n')
                        return
                variables = ",".join(varList)
                exp = "readSimulationResult(\"" + resFile + '",{' + variables + "})"
                res = self.getconn.sendExpression(exp)
                npRes = np.array(res)
                exp2 = "closeSimulationResultFile()"
                self.getconn.sendExpression(exp2)
                if len(npRes) == 1:
                    tup = (npRes.ravel())
                    return tup
                else:
                    tup = tuple(npRes)
                    return tup

            elif isinstance(varList, tuple) and len(varList) == 1:
                varList, = varList
                variables = ",".join(varList)
                exp = "readSimulationResult(\"" + resFile + '",{' + variables + "})"
                res = self.getconn.sendExpression(exp)
                npRes = np.array(res)
                exp2 = "closeSimulationResultFile()"
                self.getconn.sendExpression(exp2)
                return npRes

    # to set continuous quantities values
    def setContinuous(self, **cvals):  # 13
        """
        This method is used to set continuous values. It can be called:
            •with a sequence of continuous name and assigning corresponding values as arguments as show in the example below:
            setContinuousValues(cName1 = 10.9, cName2 = 0.066)
        """
        self.__setValue(cvals, self.__getContinuousNames(), self.cValuesList, 'continuous', 0)

    # to set parameter quantities values
    def setParameters(self, **pvals):  # 14
        """
        This method is used to set parameter values. It can be called:
            •with a sequence of parameter name and assigning corresponding value as arguments as show in the example below:
            setParameterValues(pName1 = 10.9, pName2 = 0.066)
        """
        self.__setValue(pvals, self.__getParameterNames(), self.__getParameterValues(), 'parameter', 0)

    # to set input quantities value
    def setInputs(self, **nameVal):  # 15
        """
        This method is used to set input values. It can be called:
            •with a sequence of input name and assigning corresponding values as arguments as show in the example below:
            setParameterValues(iName = [(t0, v0), (t1, v0), (t1, v2), (t3, v2)...]), where tj<=tj+1
        """

        try:
            for n in nameVal:
                tupleList = nameVal.get(n)
                if isinstance(tupleList, list):
                    if tupleList != sorted(tupleList, key=lambda x: x[0]):
                        print('Time value should be in increasing order')
                        return
                    for l in tupleList:
                        if isinstance(l, tuple):
                            if l[0] < float(self.simValuesList[0]):
                                print('Input time value is less than simulation startTime')
                                return
                            if len(l) != 2:
                                print('Value for ' + n + ' is in incorrect format!')
                                return
                        else:
                            print('Error!!! Value must be in tuple format')
                            return
                elif isinstance(tupleList, int) or isinstance(tupleList, float):
                    continue
                else:
                    print('Error!!! Input values should be tuple list for ' + n)
                    return
            lst2 = []
            lstInd = []
            for n in nameVal:
                if not self.specialNames:
                    index = self.iNamesList.index(n)
                    if isinstance(nameVal.get(n), int) or isinstance(nameVal.get(n), float):
                        self.specialNames.append((n, nameVal.get(n), True))
                        self.inputsVal[index] = [(float(self.simValuesList[0]), nameVal.get(n)), (float(self.simValuesList[1]), nameVal.get(n))]
                    else:
                        self.inputsVal[index] = nameVal.get(n)
                else:
                    if n in [s[0] for s in self.specialNames]:
                        s_, = tuple([item for item in self.specialNames if n in item])

                        index = self.iNamesList.index(n)
                        if isinstance(nameVal.get(n), int) or isinstance(nameVal.get(n), float):
                            self.inputsVal[index] = [(float(self.simValuesList[0]), nameVal.get(n)), (float(self.simValuesList[1]), nameVal.get(n))]
                        else:
                            ind = self.specialNames.index(s_)
                            self.specialNames.pop(ind)

                            index = self.iNamesList.index(n)
                            self.inputsVal[index] = nameVal.get(n)
                    else:
                        index = self.iNamesList.index(n)
                        if isinstance(nameVal.get(n), int) or isinstance(nameVal.get(n), float):
                            self.specialNames.append((n, nameVal.get(n), True))
                            self.inputsVal[index] = [(float(self.simValuesList[0]), nameVal.get(n)), (float(self.simValuesList[1]), nameVal.get(n))]
                        else:
                            self.inputsVal[index] = nameVal.get(n)
                self.inputFlag = True

        except Exception:
            print("Error:!!! " + n + " is not an input")
            return

    # To create csv file for inputs
    def __simInput(self):
        sl = list()  # Actual timestamps
        skip = False
        inp = list()
        inp = deepcopy(self.__getInputValues())
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
        name = ','.join(self.__getInputNames())
        name = '{},{},{}'.format(name_, name, 'end')

        a = ''
        l = []
        l.append(name)
        for i in range(0, len(sl)):
            a = ("%s,%s" % (str(float(sl[i])), ",".join(list(str(float(inppp[i])) for inppp in interpolated_inputs_all)))) + ',0'
            l.append(a)

        self.csvFile = '{}.csv'.format(self.modelName)
        with open(self.csvFile, "w") as f:
            writer = csv.writer(f, delimiter='\n')
            writer.writerow(l)

    # to set values for continuous and parameter quantities
    def __setValue(self, nameVal, namesList, valuesList, quantity, index):
        try:
            for n in nameVal:
                if n in namesList:
                    for l in self.quantitiesList:
                        if (l.name == n):
                            if l.changable == 'false':
                                print("!!! value cannot be set for " + n)
                            else:
                                l.start = float(nameVal.get(n))
                                index_ = namesList.index(n)
                                valuesList[index_] = l.start

                                rootSet = self.root
                                for paramVar in rootSet.iter('ScalarVariable'):
                                    if paramVar.get('name') == str(n):
                                        c = paramVar.getchildren()
                                        for attr in c:
                                            val = float(nameVal.get(n))
                                            attr.set('start', str(val))
                                            self.tree.write(self.xmlFile, encoding='UTF-8', xml_declaration=True)
                                index = index + 1
                else:
                    print('Error: ' + n + ' is not ' + quantity)

        except Exception as e:
            print(e)

    # to set simulation options values
    def setSimulationOptions(self, **simOptions):  # 16
        """
        This method is used to set simulation options. It can be called:
            •with a sequence of simulation options name and assigning corresponding values as arguments as show in the example below:
            setSimulationOptions(stopTime = 100, solver = 'euler')
        """
        return self.__setOptions(simOptions, self.simNamesList, self.simValuesList, 0)

    # to set optimization options values
    def setOptimizationOptions(self, **optimizationOptions):  # 17
        """
        This method is used to set optimization options. It can be called:
            •with a sequence of optimization options name and assigning corresponding values as arguments as show in the example below:
            setOptimizationOptions(stopTime = 10,simflags = '-lv LOG_IPOPT -optimizerNP 1')
        """
        return self.__setOptions(optimizationOptions, self.optimizeOptionsNamesList, self.optimizeOptionsValuesList)

    # to set linearization options values
    def setLinearizationOptions(self, **linearizationOptions):  # 18
        """
        This method is used to set linearization options. It can be called:
            •with a sequence of linearization options name and assigning corresponding value as arguments as show in the example below
            setLinearizationOptions(stopTime=0, stepSize = 10)
        """
        return self.__setOptions(linearizationOptions, self.linearizeOptionsNamesList, self.linearizeOptionsValuesList)

    # to set options for simulation, optimization and linearization
    def __setOptions(self, options, namesList, valuesList, index=None):
        try:
            for opt in options:
                if opt in namesList:
                    if opt == 'stopTime':
                        if float(options.get(opt)) <= float(valuesList[0]):
                            print('!!! stoptTime should be greater than startTime')
                            return
                    if opt == 'startTime':
                        if float(options.get(opt)) >= float(valuesList[1]):
                            print('!!! startTime should be less than stopTime')
                            return
                    index_ = namesList.index(opt)
                    valuesList[index_] = options.get(opt)
                else:
                    print('!!!' + opt + ' is not an option')
                    continue
                if index is not None:
                    rootSSC = self.root
                    for sim in rootSSC.iter('DefaultExperiment'):
                        sim.set(opt, str(options.get(opt)))
                        self.tree.write(self.xmlFile, encoding='UTF-8', xml_declaration=True)
                    index = index + 1
            if index is not None and self.specialNames:
                for n in self.specialNames:
                    if n[2]:
                        index = self.iNamesList.index(n[0])
                        self.inputsVal[index] = [(float(self.simValuesList[0]), n[1]), (float(self.simValuesList[1]), n[1])]

        except Exception as e:
            print(e)

    # to convert Modelica model to FMU
    def convertMo2Fmu(self):  # 19
        """
        This method is used to generate FMU from the given Modelica model. It creates "modelName.fmu" in the current working directory. It can be called:
            •only without any arguments
        """

        convertMo2FmuError = ''
        translateModelFMUResult = self.requestApi('translateModelFMU', self.modelName)
        if convertMo2FmuError:
            print(convertMo2FmuError)

        return translateModelFMUResult

    # to convert FMU to Modelica model
    def convertFmu2Mo(self, fmuName):  # 20
        """
        In order to load FMU, at first it needs to be translated into Modelica model. This method is used to generate Modelica model from the given FMU. It generates "fmuName_me_FMU.mo". It can be called:
            •only without any arguments
        Currently, it only supports Model Exchange conversion.

        - Input arguments: s1
            * s1: name of FMU file, including extension .fmu
        """

        convertFmu2MoError = ''
        importResult = self.requestApi('importFMU', fmuName)
        convertFmu2MoError = self.requestApi('getErrorString')
        if convertFmu2MoError:
            print(convertFmu2MoError)

        return importResult

    # to optimize model
    def optimize(self):  # 21
        """
        This method optimizes model according to the optimized options. It can be called:
            •only without any arguments
        """

        cName = self.modelName
        properties = '{}={}, {}={}, {}={}, {}={}, {}={}'.format(self.optimizeOptionsNamesList[0], self.optimizeOptionsValuesList[0], self.optimizeOptionsNamesList[1], self.optimizeOptionsValuesList[1], self.optimizeOptionsNamesList[2], self.optimizeOptionsValuesList[2], self.optimizeOptionsNamesList[3], self.optimizeOptionsValuesList[3], self.optimizeOptionsNamesList[4], self.optimizeOptionsValuesList[4])

        optimizeError = ''
        self.getconn.sendExpression("setCommandLineOptions(\"-g=Optimica\")")
        optimizeResult = self.requestApi('optimize', cName, properties)
        optimizeError = self.requestApi('getErrorString')
        if optimizeError:
            print(optimizeError)

        return optimizeResult

    # to linearize model
    def linearize(self):  # 22
        """
        This method linearizes model according to the linearized options. This will generate a linear model that consists of matrices A, B, C and D.  It can be called:
            •only without any arguments
        """

        try:
            cName = self.modelName
            # self.requestApi("setCommandLineOptions", "+generateSymbolicLinearization")
            self.getconn.sendExpression("setCommandLineOptions(\"+generateSymbolicLinearization\")")
            properties = "{}={}, {}={}, {}={}, {}={}, {}={}".format(self.linearizeOptionsNamesList[0], self.linearizeOptionsValuesList[0], self.linearizeOptionsNamesList[1], self.linearizeOptionsValuesList[1], self.linearizeOptionsNamesList[2], self.linearizeOptionsValuesList[2], self.linearizeOptionsNamesList[3], self.linearizeOptionsValuesList[3], self.linearizeOptionsNamesList[4], self.linearizeOptionsValuesList[4])
            x = self.getParameters()
            getparamvalues = ','.join("%s=%r" % (key, val) for (key, val) in list(x.items()))
            override = "-override=" + getparamvalues
            if self.inputFlag:
                nameVal = self.getInputs()
                for n in nameVal:
                    tupleList = nameVal.get(n)
                    for l in tupleList:
                        if l[0] < float(self.simValuesList[0]):
                            print('Input time value is less than simulation startTime')
                            return
                self.__simInput()
                flags = "-csvInput=" + self.csvFile + " " + override
                self.getconn.sendExpression("linearize(" + self.modelName + "," + properties + ", simflags=\" " + flags + " \")")
                linearizeError = ''
                linearizeError = self.requestApi('getErrorString')
                if linearizeError:
                    print(linearizeError)
            else:
                linearizeError = ''
                self.getconn.sendExpression("linearize(" + self.modelName + "," + properties + ", simflags=\" " + override + " \")")
                # linearizeResult = self.requestApi('linearize', cName, properties, simflags)
                linearizeError = self.requestApi('getErrorString')
                if linearizeError:
                    print(linearizeError)

            # code to get the matrix and linear inputs, outputs and states
            getLinFile = '{}_{}.{}'.format('linear', self.modelName, 'mo')
            checkLinFile = os.path.exists(getLinFile)
            if checkLinFile:
                self.requestApi('loadFile', getLinFile)
                cNames = self.requestApi('getClassNames')
                linModelName = cNames[0]
                self.requestApi('buildModel', linModelName)
                lin = ModelicaSystem(getLinFile, linModelName)
                lin.linearizationFlag = True
                self.linearquantitiesList = lin.getQuantities()
                self.getLinearQuantityInformation()
                A = []
                B = []
                C = []
                D = []
                matrices = []
                A = lin.__getMatrixA()
                B = lin.__getMatrixB()
                C = lin.__getMatrixC()
                D = lin.__getMatrixD()

                matrices.append(A)
                matrices.append(B)
                matrices.append(C)
                matrices.append(D)

                lin.linearizationFlag = False
                del lin
                self.linearizationFlag = False
                return matrices

        except Exception as e:
            raise e

    def getLinearQuantityInformation(self):
        # function which extracts linearised states, inputs and outputs
        for i in range(len(self.linearquantitiesList)):
            if (self.linearquantitiesList[i]['alias'] == 'alias'):
                name = self.linearquantitiesList[i]['Name']
                if (name[1] == 'x'):
                    self.linearstates.append(name[3:-1])
                if (name[1] == 'u'):
                    self.linearinputs.append(name[3:-1])
                if (name[1] == 'y'):
                    self.linearoutputs.append(name[3:-1])

    def getLinearInputs(self):
        return self.linearinputs

    def getLinearOutputs(self):
        return self.linearoutputs

    def getLinearStates(self):
        return self.linearstates

    def __getMatrix(self, xParameter, sizeParameter):
        paraKeys = self.__getParameterNames()
        xElemNames = []
        for k in paraKeys:
            if xParameter in k:
                xElemNames.append(k)
        xElemNames.sort()
        xElemNames.sort(key=len)
        sortedX = xElemNames
        size_ = int(self.getParameters(sizeParameter))
        matX = []
        matX = [[] for i in range(size_)]
        for i in range(size_):
            for a in sortedX:
                if float(a.partition('[')[-1].rpartition(',')[0]) == float(i + 1):
                    matX[i].append(a)
        a_ = []
        for i in matX:
            a_.append(i)
        xValues = []
        for i in matX:
            tup = tuple(i)
            xValues.append(self.getParameters(tup))
        xValues = np.array(xValues)
        return xValues

    def __getMatrixA(self):
        return self.__getMatrix('A[', 'n')

    def __getMatrixB(self):
        return self.__getMatrix('B[', 'n')

    def __getMatrixC(self):
        return self.__getMatrix('C[', 'l')

    def __getMatrixD(self):
        return self.__getMatrix('D[', 'l')
