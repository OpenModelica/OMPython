# -*- coding: utf-8 -*-
"""
Definition of main class to run Modelica simulations - ModelicaSystem.
"""

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

import csv
import logging
import os
import platform
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import numpy as np
import importlib
import pathlib

from OMPython.OMCSession import OMCSessionBase, OMCSessionZMQ

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaSystemError(Exception):
    pass


class ModelicaSystem:
    def __init__(self, fileName=None, modelName=None, lmodel=None, commandLineOptions=None,
                 variableFilter=None, customBuildDirectory=None, verbose=True, raiseerrors=False,
                 omhome: str = None, session: OMCSessionBase = None):  # 1
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
            raise Exception("Cannot create ModelicaSystem object without any arguments")
            return

        self.tree = None
        self.quantitiesList = []
        self.paramlist = {}
        self.inputlist = {}
        self.outputlist = {}
        self.continuouslist = {}
        self.simulateOptions = {}
        self.overridevariables = {}
        self.simoptionsoverride = {}
        self.linearOptions = {'startTime': 0.0, 'stopTime': 1.0, 'stepSize': 0.002, 'tolerance': 1e-8}
        self.optimizeOptions = {'startTime': 0.0, 'stopTime': 1.0, 'numberOfIntervals': 500, 'stepSize': 0.002,
                                'tolerance': 1e-8}
        self.linearinputs = []  # linearization input list
        self.linearoutputs = []  # linearization output list
        self.linearstates = []  # linearization  states list
        self.tempdir = ""

        self._verbose = verbose

        if session is not None:
            self.getconn = session
        else:
            self.getconn = OMCSessionZMQ(omhome=omhome)

        # needed for properly deleting the session
        self._omc_log_file = self.getconn._omc_log_file
        self._omc_process = self.getconn._omc_process

        # set commandLineOptions if provided by users
        self.setCommandLineOptions(commandLineOptions=commandLineOptions)

        if lmodel is None:
            lmodel = []

        self.xmlFile = None
        self.lmodel = lmodel  # may be needed if model is derived from other model
        self.modelName = modelName  # Model class name
        self.fileName = pathlib.Path(fileName).resolve() if fileName is not None else None  # Model file/package name
        self.inputFlag = False  # for model with input quantity
        self.simulationFlag = False  # if the model is simulated?
        self.outputFlag = False
        self.csvFile = ''  # for storing inputs condition
        self.resultfile = ""  # for storing result file
        self.variableFilter = variableFilter

        self._raiseerrors = raiseerrors

        if fileName is not None and not self.fileName.is_file():  # if file does not exist
            raise IOError(f"File Error: {self.fileName} does not exist!!!")

        # set default command Line Options for linearization as
        # linearize() will use the simulation executable and runtime
        # flag -l to perform linearization
        self.sendExpression("setCommandLineOptions(\"--linearizationDumpLanguage=python\")")
        self.sendExpression("setCommandLineOptions(\"--generateSymbolicLinearization\")")

        self.setTempDirectory(customBuildDirectory)

        if fileName is not None:
            self.loadLibrary()
            self.loadFile()

        # allow directly loading models from MSL without fileName
        if fileName is None and modelName is not None:
            self.loadLibrary()

        self.buildModel(variableFilter)

    def setCommandLineOptions(self, commandLineOptions: str):
        # set commandLineOptions if provided by users
        if commandLineOptions is not None:
            exp = "".join(["setCommandLineOptions(", "\"", commandLineOptions, "\"", ")"])
            cmdexp = self.sendExpression(exp)
            if not cmdexp:
                self._check_error()

    def loadFile(self):
        # load file
        loadMsg = self.sendExpression(f'loadFile("{self.fileName.as_posix()}")')
        # Show notification or warnings to the user when verbose=True OR if some error occurred i.e., not result
        if self._verbose or not loadMsg:
            self._check_error()

    # for loading file/package, loading model and building model
    def loadLibrary(self):
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
                    raise ModelicaSystemError("loadLibrary() failed, Unknown type detected: " +
                                              "{} is of type {}, ".format(element, type(element)) +
                                              "The following patterns are supported:\n" +
                                              "1)[\"Modelica\"]\n" +
                                              "2)[(\"Modelica\",\"3.2.3\"), \"PowerSystems\"]\n")
                # Show notification or warnings to the user when verbose=True OR if some error occurred i.e., not result
                if self._verbose or not result:
                    self._check_error()

    def setTempDirectory(self, customBuildDirectory):
        # create a unique temp directory for each session and build the model in that directory
        if customBuildDirectory is not None:
            if not os.path.exists(customBuildDirectory):
                raise IOError(customBuildDirectory, " does not exist")
            self.tempdir = customBuildDirectory
        else:
            self.tempdir = tempfile.mkdtemp()
            if not os.path.exists(self.tempdir):
                raise IOError(self.tempdir, " cannot be created")

        logger.info("Define tempdir as {}".format(self.tempdir))
        exp = "".join(["cd(", "\"", self.tempdir, "\"", ")"]).replace("\\", "/")
        self.sendExpression(exp)

    def getWorkDirectory(self):
        return self.tempdir

    def _run_cmd(self, cmd: list):
        logger.debug("Run OM command {} in {}".format(cmd, self.tempdir))

        if platform.system() == "Windows":
            dllPath = ""

            # set the process environment from the generated .bat file in windows which should have all the dependencies
            batFilePath = os.path.join(self.tempdir, '{}.{}'.format(self.modelName, "bat")).replace("\\", "/")
            if (not os.path.exists(batFilePath)):
                ModelicaSystemError("Batch file (*.bat) does not exist " + batFilePath)

            with open(batFilePath, 'r') as file:
                for line in file:
                    match = re.match(r"^SET PATH=([^%]*)", line, re.IGNORECASE)
                    if match:
                        dllPath = match.group(1).strip(';')  # Remove any trailing semicolons
            my_env = os.environ.copy()
            my_env["PATH"] = dllPath + os.pathsep + my_env["PATH"]
        else:
            # TODO: how to handle path to resources of external libraries for any system not Windows?
            my_env = None

        currentDir = os.getcwd()
        try:
            os.chdir(self.tempdir)
            p = subprocess.Popen(cmd, env=my_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()

            stdout = stdout.decode('ascii').strip()
            stderr = stderr.decode('ascii').strip()
            if stderr:
                raise ModelicaSystemError("Error running command {}: {}".format(cmd, stderr))
            if self._verbose and stdout:
                logger.info("OM output for command {}:\n{}".format(cmd, stdout))
            p.wait()
            p.terminate()
            os.chdir(currentDir)
        except Exception as e:
            os.chdir(currentDir)
            raise ModelicaSystemError("Exception {} running command {}: {}".format(type(e), cmd, e))

    def _check_error(self):
        errstr = self.sendExpression("getErrorString()")
        if errstr is None or not errstr:
            return

        self._raise_error(errstr=errstr)

    def _raise_error(self, errstr: str):
        if self._raiseerrors:
            raise ModelicaSystemError("OM error: {}".format(errstr))
        else:
            logger.error(errstr)

    def buildModel(self, variableFilter=None):
        if variableFilter is not None:
            self.variableFilter = variableFilter

        if self.variableFilter is not None:
            varFilter = "variableFilter=" + "\"" + self.variableFilter + "\""
        else:
            varFilter = "variableFilter=" + "\".*""\""
        logger.debug(varFilter)
        # buildModelResult=self.sendExpression("buildModel("+ mName +")")
        buildModelResult = self.requestApi("buildModel", self.modelName, properties=varFilter)
        if self._verbose:
            logger.info("OM model build result: {}".format(buildModelResult))
        self._check_error()

        self.xmlFile = os.path.join(os.path.dirname(buildModelResult[0]), buildModelResult[1]).replace("\\", "/")
        self.xmlparse()

    def sendExpression(self, expr, parsed=True):
        logger.debug("sendExpression(%r, %r)", expr, parsed)
        return self.getconn.sendExpression(expr, parsed)

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
            res = self.sendExpression(exp)
        except Exception as e:
            errstr = "Exception {} raised: {}".format(type(e), e)
            self._raise_error(errstr=errstr)
            res = None
        return res

    def xmlparse(self):
        if (os.path.exists(self.xmlFile)):
            self.tree = ET.parse(self.xmlFile)
            self.root = self.tree.getroot()
            rootCQ = self.root
            for attr in rootCQ.iter('DefaultExperiment'):
                self.simulateOptions["startTime"] = attr.get('startTime')
                self.simulateOptions["stopTime"] = attr.get('stopTime')
                self.simulateOptions["stepSize"] = attr.get('stepSize')
                self.simulateOptions["tolerance"] = attr.get('tolerance')
                self.simulateOptions["solver"] = attr.get('solver')
                self.simulateOptions["outputFormat"] = attr.get('outputFormat')

            for sv in rootCQ.iter('ScalarVariable'):
                scalar = {}
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
                scalar["start"] = start
                scalar["min"] = min
                scalar["max"] = max
                scalar["unit"] = unit

                if (scalar["variability"] == "parameter"):
                    if scalar["name"] in self.overridevariables:
                        self.paramlist[scalar["name"]] = self.overridevariables[scalar["name"]]
                    else:
                        self.paramlist[scalar["name"]] = scalar["start"]
                if (scalar["variability"] == "continuous"):
                    self.continuouslist[scalar["name"]] = scalar["start"]
                if (scalar["causality"] == "input"):
                    self.inputlist[scalar["name"]] = scalar["start"]
                if (scalar["causality"] == "output"):
                    self.outputlist[scalar["name"]] = scalar["start"]

                self.quantitiesList.append(scalar)
        else:
            errstr = "XML file not generated: " + self.xmlFile
            self._raise_error(errstr=errstr)

    def getQuantities(self, names=None):  # 3
        """
        This method returns list of dictionaries. It displays details of quantities such as name, value, changeable, and description, where changeable means  if value for corresponding quantity name is changeable or not. It can be called :
        usage:
        >>> getQuantities()
        >>> getQuantities("Name1")
        >>> getQuantities(["Name1","Name2"])
        """
        if names is None:
            return self.quantitiesList
        elif (isinstance(names, str)):
            return [x for x in self.quantitiesList if x["name"] == names]
        elif isinstance(names, list):
            return [x for y in names for x in self.quantitiesList if x["name"] == y]

    def getContinuous(self, names=None):  # 4
        """
        This method returns dict. The key is continuous names and value is corresponding continuous value.
        usage:
        >>> getContinuous()
        >>> getContinuous("Name1")
        >>> getContinuous(["Name1","Name2"])
        """
        if not self.simulationFlag:
            if names is None:
                return self.continuouslist
            elif isinstance(names, str):
                return [self.continuouslist.get(names, "NotExist")]
            elif isinstance(names, list):
                return [self.continuouslist.get(x, "NotExist") for x in names]
        else:
            if names is None:
                for i in self.continuouslist:
                    try:
                        value = self.getSolutions(i)
                        self.continuouslist[i] = value[0][-1]
                    except Exception:
                        raise ModelicaSystemError("OM error: {} could not be computed".format(i))
                return self.continuouslist

            elif (isinstance(names, str)):
                if names in self.continuouslist:
                    value = self.getSolutions(names)
                    self.continuouslist[names] = value[0][-1]
                    return [self.continuouslist.get(names)]
                else:
                    raise ModelicaSystemError("OM error: {} is not continuous".format(names))

            elif (isinstance(names, list)):
                valuelist = []
                for i in names:
                    if i in self.continuouslist:
                        value = self.getSolutions(i)
                        self.continuouslist[i] = value[0][-1]
                        valuelist.append(value[0][-1])
                    else:
                        raise ModelicaSystemError("OM error: {} is not continuous".format(i))
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
        if names is None:
            return self.paramlist
        elif (isinstance(names, str)):
            return [self.paramlist.get(names, "NotExist")]
        elif (isinstance(names, list)):
            return ([self.paramlist.get(x, "NotExist") for x in names])

    def getlinearParameters(self, names=None):  # 5
        """
        This method returns dict. The key is parameter names and value is corresponding parameter value.
        If *name is None then the function will return dict which contain all parameter names as key and value as corresponding values. eg., getParameters()
        Otherwise variable number of arguments can be passed as parameter name in string format separated by commas. eg., getParameters('paraName1', 'paraName2')
        """
        if (names == 0):
            return self.linearparameters
        elif (isinstance(names, str)):
            return [self.linearparameters.get(names, "NotExist")]
        else:
            return ([self.linearparameters.get(x, "NotExist") for x in names])

    def getInputs(self, names=None):  # 6
        """
        This method returns dict. The key is input names and value is corresponding input value.
        If *name is None then the function will return dict which contain all input names as key and value as corresponding values. eg., getInputs()
        Otherwise variable number of arguments can be passed as input name in string format separated by commas. eg., getInputs('iName1', 'iName2')
        """
        if names is None:
            return self.inputlist
        elif (isinstance(names, str)):
            return [self.inputlist.get(names, "NotExist")]
        elif (isinstance(names, list)):
            return ([self.inputlist.get(x, "NotExist") for x in names])

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
            if names is None:
                return self.outputlist
            elif (isinstance(names, str)):
                return [self.outputlist.get(names, "NotExist")]
            else:
                return ([self.outputlist.get(x, "NotExist") for x in names])
        else:
            if names is None:
                for i in self.outputlist:
                    value = self.getSolutions(i)
                    self.outputlist[i] = value[0][-1]
                return self.outputlist
            elif (isinstance(names, str)):
                if names in self.outputlist:
                    value = self.getSolutions(names)
                    self.outputlist[names] = value[0][-1]
                    return [self.outputlist.get(names)]
                else:
                    return (names, " is not Output")
            elif (isinstance(names, list)):
                valuelist = []
                for i in names:
                    if i in self.outputlist:
                        value = self.getSolutions(i)
                        self.outputlist[i] = value[0][-1]
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
        if names is None:
            return self.simulateOptions
        elif (isinstance(names, str)):
            return [self.simulateOptions.get(names, "NotExist")]
        elif (isinstance(names, list)):
            return ([self.simulateOptions.get(x, "NotExist") for x in names])

    def getLinearizationOptions(self, names=None):  # 9
        """
        This method returns dict. The key is linearize option names and value is corresponding linearize option value.
        If name is None then the function will return dict which contain all linearize option names as key and value as corresponding values. eg., getLinearizationOptions()
        usage:
        >>> getLinearizationOptions()
        >>> getLinearizationOptions("Name1")
        >>> getLinearizationOptions(["Name1","Name2"])
        """
        if names is None:
            return self.linearOptions
        elif (isinstance(names, str)):
            return [self.linearOptions.get(names, "NotExist")]
        elif (isinstance(names, list)):
            return ([self.linearOptions.get(x, "NotExist") for x in names])

    def getOptimizationOptions(self, names=None):  # 10
        """
        usage:
        >>> getOptimizationOptions()
        >>> getOptimizationOptions("Name1")
        >>> getOptimizationOptions(["Name1","Name2"])
        """
        if names is None:
            return self.optimizeOptions
        elif (isinstance(names, str)):
            return [self.optimizeOptions.get(names, "NotExist")]
        elif (isinstance(names, list)):
            return ([self.optimizeOptions.get(x, "NotExist") for x in names])

    # to simulate or re-simulate model
    def simulate(self, resultfile=None, simflags=None):  # 11
        """
        This method simulates model according to the simulation options.
        usage
        >>> simulate()
        >>> simulate(resultfile="a.mat")
        >>> simulate(simflags="-noEventEmit -noRestart -override=e=0.3,g=10")  # set runtime simulation flags
        """
        if (resultfile is None):
            r = ""
            self.resultfile = os.path.join(self.tempdir, self.modelName + "_res.mat").replace("\\", "/")
        else:
            if os.path.exists(resultfile):
                r = " -r=" + resultfile
                self.resultfile = resultfile
            else:
                r = " -r=" + os.path.join(self.tempdir, resultfile).replace("\\", "/")
                self.resultfile = os.path.join(self.tempdir, resultfile).replace("\\", "/")

        # allow runtime simulation flags from user input
        if (simflags is None):
            simflags = ""
        else:
            simflags = " " + simflags

        overrideFile = os.path.join(self.tempdir, '{}.{}'.format(self.modelName + "_override", "txt")).replace("\\",
                                                                                                               "/")
        if (self.overridevariables or self.simoptionsoverride):
            tmpdict = self.overridevariables.copy()
            tmpdict.update(self.simoptionsoverride)
            # write to override file
            file = open(overrideFile, "w")
            for (key, value) in tmpdict.items():
                name = key + "=" + value + "\n"
                file.write(name)
            file.close()
            override = " -overrideFile=" + overrideFile
        else:
            override = ""

        if (self.inputFlag):  # if model has input quantities
            for i in self.inputlist:
                val = self.inputlist[i]
                if val is None:
                    val = [(float(self.simulateOptions["startTime"]), 0.0),
                           (float(self.simulateOptions["stopTime"]), 0.0)]
                    self.inputlist[i] = [(float(self.simulateOptions["startTime"]), 0.0),
                                         (float(self.simulateOptions["stopTime"]), 0.0)]
                if float(self.simulateOptions["startTime"]) != val[0][0]:
                    errstr = "!!! startTime not matched for Input {}".format(i)
                    self._raise_error(errstr=errstr)
                    return
                if float(self.simulateOptions["stopTime"]) != val[-1][0]:
                    errstr = "!!! stopTime not matched for Input {}".format(i)
                    self._raise_error(errstr=errstr)
                    return
                if val[0][0] < float(self.simulateOptions["startTime"]):
                    errstr = "Input time value is less than simulation startTime for inputs {}".format(i)
                    self._raise_error(errstr=errstr)
                    return
            self.createCSVData()  # create csv file
            csvinput = " -csvInput=" + self.csvFile
        else:
            csvinput = ""

        if (platform.system() == "Windows"):
            getExeFile = os.path.join(self.tempdir, '{}.{}'.format(self.modelName, "exe")).replace("\\", "/")
        else:
            getExeFile = os.path.join(self.tempdir, self.modelName).replace("\\", "/")

        if os.path.exists(getExeFile):
            cmd = getExeFile + override + csvinput + r + simflags
            cmd = cmd.split(" ")
            self._run_cmd(cmd=cmd)

            self.simulationFlag = True
        else:
            raise Exception("Error: Application file path not found: " + getExeFile)

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
        if resultfile is None:
            resFile = self.resultfile
        else:
            resFile = resultfile

        # check for result file exits
        if (not os.path.exists(resFile)):
            errstr = "Error: Result file does not exist {}".format(resFile)
            self._raise_error(errstr=errstr)
            return
            # exit()
        else:
            resultVars = self.sendExpression("readSimulationResultVars(\"" + resFile + "\")")
            self.sendExpression("closeSimulationResultFile()")
            if varList is None:
                return resultVars
            elif (isinstance(varList, str)):
                if (varList not in resultVars and varList != "time"):
                    errstr = '!!! ' + varList + ' does not exist'
                    self._raise_error(errstr=errstr)
                    return
                exp = "readSimulationResult(\"" + resFile + '",{' + varList + "})"
                res = self.sendExpression(exp)
                npRes = np.array(res)
                exp2 = "closeSimulationResultFile()"
                self.sendExpression(exp2)
                return npRes
            elif (isinstance(varList, list)):
                # varList, = varList
                for v in varList:
                    if v == "time":
                        continue
                    if v not in resultVars:
                        errstr = '!!! ' + v + ' does not exist'
                        self._raise_error(errstr=errstr)
                        return
                variables = ",".join(varList)
                exp = "readSimulationResult(\"" + resFile + '",{' + variables + "})"
                res = self.sendExpression(exp)
                npRes = np.array(res)
                exp2 = "closeSimulationResultFile()"
                self.sendExpression(exp2)
                return npRes

    def strip_space(self, name):
        if (isinstance(name, str)):
            return name.replace(" ", "")
        elif (isinstance(name, list)):
            return [x.replace(" ", "") for x in name]

    def setMethodHelper(self, args1, args2, args3, args4=None):
        """
        Helper function for setParameter(),setContinuous(),setSimulationOptions(),setLinearizationOption(),setOptimizationOption()
        args1 - string or list of string given by user
        args2 - dict() containing the values of different variables(eg:, parameter,continuous,simulation parameters)
        args3 - function name (eg; continuous, parameter, simulation, linearization,optimization)
        args4 - dict() which stores the new override variables list,
        """
        def apply_single(args1):
            args1 = self.strip_space(args1)
            value = args1.split("=")
            if value[0] in args2:
                if args3 == "parameter" and self.isParameterChangeable(value[0], value[1]):
                    args2[value[0]] = value[1]
                    if args4 is not None:
                        args4[value[0]] = value[1]
                elif args3 != "parameter":
                    args2[value[0]] = value[1]
                    if args4 is not None:
                        args4[value[0]] = value[1]

                return True

            else:
                errstr = "\"" + value[0] + "\"" + " is not a" + args3 + " variable"
                self._raise_error(errstr=errstr)

        result = []
        if (isinstance(args1, str)):
            result = [apply_single(args1)]

        elif (isinstance(args1, list)):
            result = []
            args1 = self.strip_space(args1)
            for var in args1:
                result.append(apply_single(var))

        return all(result)

    def setContinuous(self, cvals):  # 13
        """
        This method is used to set continuous values. It can be called:
        with a sequence of continuous name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setContinuous("Name=value")
        >>> setContinuous(["Name1=value1","Name2=value2"])
        """
        return self.setMethodHelper(cvals, self.continuouslist, "continuous", self.overridevariables)

    def setParameters(self, pvals):  # 14
        """
        This method is used to set parameter values. It can be called:
        with a sequence of parameter name and assigning corresponding value as arguments as show in the example below:
        usage
        >>> setParameters("Name=value")
        >>> setParameters(["Name1=value1","Name2=value2"])
        """
        return self.setMethodHelper(pvals, self.paramlist, "parameter", self.overridevariables)

    def isParameterChangeable(self, name, value):
        q = self.getQuantities(name)
        if (q[0]["changeable"] == "false"):
            if self._verbose:
                logger.info("setParameters() failed : It is not possible to set " +
                            "the following signal \"{}\", ".format(name) + "It seems to be structural, final, " +
                            "protected or evaluated or has a non-constant binding, use sendExpression(" +
                            "setParameterValue({}, {}, {}), ".format(self.modelName, name, value) +
                            "parsed=false) and rebuild the model using buildModel() API")
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
        return self.setMethodHelper(simOptions, self.simulateOptions, "simulation-option", self.simoptionsoverride)

    def setLinearizationOptions(self, linearizationOptions):  # 18
        """
        This method is used to set linearization options. It can be called:
        with a sequence of linearization options name and assigning corresponding value as arguments as show in the example below
        usage
        >>> setLinearizationOptions("Name=value")
        >>> setLinearizationOptions(["Name1=value1","Name2=value2"])
        """
        return self.setMethodHelper(linearizationOptions, self.linearOptions, "Linearization-option", None)

    def setOptimizationOptions(self, optimizationOptions):  # 17
        """
        This method is used to set optimization options. It can be called:
        with a sequence of optimization options name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setOptimizationOptions("Name=value")
        >>> setOptimizationOptions(["Name1=value1","Name2=value2"])
        """
        return self.setMethodHelper(optimizationOptions, self.optimizeOptions, "optimization-option", None)

    def setInputs(self, name):  # 15
        """
        This method is used to set input values. It can be called:
        with a sequence of input name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setInputs("Name=value")
        >>> setInputs(["Name1=value1","Name2=value2"])
        """
        if (isinstance(name, str)):
            name = self.strip_space(name)
            value = name.split("=")
            if value[0] in self.inputlist:
                tmpvalue = eval(value[1])
                if (isinstance(tmpvalue, int) or isinstance(tmpvalue, float)):
                    self.inputlist[value[0]] = [(float(self.simulateOptions["startTime"]), float(value[1])),
                                                (float(self.simulateOptions["stopTime"]), float(value[1]))]
                elif (isinstance(tmpvalue, list)):
                    self.checkValidInputs(tmpvalue)
                    self.inputlist[value[0]] = tmpvalue
                self.inputFlag = True
            else:
                errstr = value[0] + " is not an input"
                self._raise_error(errstr=errstr)
        elif (isinstance(name, list)):
            name = self.strip_space(name)
            for var in name:
                value = var.split("=")
                if value[0] in self.inputlist:
                    tmpvalue = eval(value[1])
                    if (isinstance(tmpvalue, int) or isinstance(tmpvalue, float)):
                        self.inputlist[value[0]] = [(float(self.simulateOptions["startTime"]), float(value[1])),
                                                    (float(self.simulateOptions["stopTime"]), float(value[1]))]
                    elif (isinstance(tmpvalue, list)):
                        self.checkValidInputs(tmpvalue)
                        self.inputlist[value[0]] = tmpvalue
                    self.inputFlag = True
                else:
                    errstr = value[0] + " is not an input"
                    self._raise_error(errstr=errstr)

    def checkValidInputs(self, name):
        if name != sorted(name, key=lambda x: x[0]):
            raise ModelicaSystemError('Time value should be in increasing order')
        for l in name:
            if isinstance(l, tuple):
                # if l[0] < float(self.simValuesList[0]):
                if l[0] < float(self.simulateOptions["startTime"]):
                    ModelicaSystemError('Input time value is less than simulation startTime')
                if len(l) != 2:
                    ModelicaSystemError('Value for ' + l + ' is in incorrect format!')
            else:
                ModelicaSystemError('Error!!! Value must be in tuple format')

    # To create csv file for inputs
    def createCSVData(self):
        sl = list()  # Actual timestamps
        skip = False

        # check for NONE in input list and replace with proper data (e.g) [(startTime, 0.0), (stopTime, 0.0)]
        tmpinputlist = {}
        for (key, value) in self.inputlist.items():
            if (value is None):
                tmpinputlist[key] = [(float(self.simulateOptions["startTime"]), 0.0),
                                     (float(self.simulateOptions["stopTime"]), 0.0)]
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
        # name = ','.join(self.__getInputNames())
        name = ','.join(list(self.inputlist.keys()))
        name = '{},{},{}'.format(name_, name, 'end')

        a = ''
        l = []
        l.append(name)
        for i in range(0, len(sl)):
            a = ("%s,%s" % (str(float(sl[i])), ",".join(list(str(float(inppp[i]))
                                                             for inppp in interpolated_inputs_all)))) + ',0'
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
        properties = 'version="{}", fmuType="{}", fileNamePrefix="{}", includeResources={}'.format(version, fmuType,
                                                                                                   fileNamePrefix,
                                                                                                   includeResourcesStr)
        fmu = self.requestApi('buildModelFMU', self.modelName, properties)

        # report proper error message
        if not os.path.exists(fmu):
            self._check_error()

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

        # report proper error message
        if not os.path.exists(fileName):
            self._check_error()

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
        self.sendExpression("setCommandLineOptions(\"-g=Optimica\")")
        optimizeResult = self.requestApi('optimize', cName, properties)
        self._check_error()

        return optimizeResult

    # to linearize model
    def linearize(self, lintime=None, simflags=None):  # 22
        """
        This method linearizes model according to the linearized options. This will generate a linear model that consists of matrices A, B, C and D.  It can be called:
        only without any arguments
        usage
        >>> linearize()
        """

        if self.xmlFile is None:
            raise IOError("Linearization cannot be performed as the model is not build, "
                          "use ModelicaSystem() to build the model first")

        overrideLinearFile = os.path.join(self.tempdir,
                                          '{}.{}'.format(self.modelName + "_override_linear", "txt")).replace("\\", "/")

        file = open(overrideLinearFile, "w")
        for (key, value) in self.overridevariables.items():
            name = key + "=" + value + "\n"
            file.write(name)
        for (key, value) in self.linearOptions.items():
            name = key + "=" + str(value) + "\n"
            file.write(name)
        file.close()

        override = " -overrideFile=" + overrideLinearFile
        logger.debug(f"overwrite = {override}")

        if self.inputFlag:
            nameVal = self.getInputs()
            for n in nameVal:
                tupleList = nameVal.get(n)
                if tupleList is not None:
                    for l in tupleList:
                        if l[0] < float(self.simulateOptions["startTime"]):
                            raise ModelicaSystemError('Input time value is less than simulation startTime')
            self.createCSVData()
            csvinput = " -csvInput=" + self.csvFile
        else:
            csvinput = ""

        # prepare the linearization runtime command
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
        else:
            simflags = " " + simflags

        if (os.path.exists(getExeFile)):
            cmd = getExeFile + linruntime + override + csvinput + simflags
            cmd = cmd.split(' ')
            self._run_cmd(cmd=cmd)
        else:
            raise Exception("Error: Application file path not found: " + getExeFile)

        # code to get the matrix and linear inputs, outputs and states
        linearFile = os.path.join(self.tempdir, "linearized_model.py").replace("\\", "/")

        # support older openmodelica versions before OpenModelica v1.16.2 where linearize() generates "linear_modelname.mo" file
        if not os.path.exists(linearFile):
            linearFile = '{}_{}.{}'.format('linear', self.modelName, 'py')

        if os.path.exists(linearFile):
            # this function is called from the generated python code linearized_model.py at runtime,
            # to improve the performance by directly reading the matrices A, B, C and D from the julia code and avoid building the linearized modelica model
            try:
                # do not add the linearfile directory to path, as multiple execution of linearization will always use the first added path, instead execute the file
                # https://github.com/OpenModelica/OMPython/issues/196
                module = importlib.machinery.SourceFileLoader("linearized_model", linearFile).load_module()
                result = module.linearized_model()
                (n, m, p, x0, u0, A, B, C, D, stateVars, inputVars, outputVars) = result
                self.linearinputs = inputVars
                self.linearoutputs = outputVars
                self.linearstates = stateVars
                return [A, B, C, D]
            except ModuleNotFoundError:
                raise Exception("ModuleNotFoundError: No module named 'linearized_model'")
        else:
            errormsg = self.sendExpression("getErrorString()")
            raise ModelicaSystemError("Linearization failed: {} not found: {}".format(repr(linearFile), errormsg))

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
