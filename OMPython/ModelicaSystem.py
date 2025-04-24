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
from dataclasses import dataclass
from typing import Optional

from OMPython.OMCSession import OMCSessionBase, OMCSessionZMQ

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaSystemError(Exception):
    pass


@dataclass
class LinearizationResult:
    """Modelica model linearization results.

    Attributes:
        n: number of states
        m: number of inputs
        p: number of outputs
        A: state matrix (n x n)
        B: input matrix (n x m)
        C: output matrix (p x n)
        D: feedthrough matrix (p x m)
        x0: fixed point
        u0: input corresponding to the fixed point
        stateVars: names of state variables
        inputVars: names of inputs
        outputVars: names of outputs
    """

    n: int
    m: int
    p: int

    A: list
    B: list
    C: list
    D: list

    x0: list[float]
    u0: list[float]

    stateVars: list[str]
    inputVars: list[str]
    outputVars: list[str]

    def __iter__(self):
        """Allow unpacking A, B, C, D = result."""
        yield self.A
        yield self.B
        yield self.C
        yield self.D

    def __getitem__(self, index: int):
        """Allow accessing A, B, C, D via result[0] through result[3].

        This is needed for backwards compatibility, because
        ModelicaSystem.linearize() used to return [A, B, C, D].
        """
        return {0: self.A, 1: self.B, 2: self.C, 3: self.D}[index]


class ModelicaSystem:
    def __init__(
            self,
            fileName: Optional[str | os.PathLike] = None,
            modelName: Optional[str] = None,
            lmodel: Optional[list[str | tuple[str, str]]] = None,
            commandLineOptions: Optional[str] = None,
            variableFilter: Optional[str] = None,
            customBuildDirectory: Optional[str | os.PathLike] = None,
            verbose: bool = True,
            raiseerrors: bool = False,
            omhome: Optional[str] = None,
            session: Optional[OMCSessionBase] = None
            ):
        """Initialize, load and build a model.

        The constructor loads the model file and builds it, generating exe and
        xml files, etc.

        Args:
            fileName: Path to the model file. Either absolute or relative to
              the current working directory.
            modelName: The name of the model class. If it is contained within
              a package, "PackageName.ModelName" should be used.
            lmodel: List of libraries to be loaded before the model itself is
              loaded. Two formats are supported for the list elements:
              lmodel=["Modelica"] for just the library name
              and lmodel=[("Modelica","3.2.3")] for specifying both the name
              and the version.
            commandLineOptions: String with extra command line options to be
              provided to omc via setCommandLineOptions().
            variableFilter: A regular expression. Only variables fully
              matching the regexp will be stored in the result file.
              Leaving it unspecified is equivalent to ".*".
            customBuildDirectory: Path to a directory to be used for temporary
              files like the model executable. If left unspecified, a tmp
              directory will be created.
            verbose: If True, enable verbose logging.
            raiseerrors: If True, raise exceptions instead of just logging
              OpenModelica errors.
            omhome: OPENMODELICAHOME value to be used when creating the OMC
              session.
            session: OMC session to be used. If unspecified, a new session
              will be created.

        Examples:
            mod = ModelicaSystem("ModelicaModel.mo", "modelName")
            mod = ModelicaSystem("ModelicaModel.mo", "modelName", ["Modelica"])
            mod = ModelicaSystem("ModelicaModel.mo", "modelName", [("Modelica","3.2.3"), "PowerSystems"])
        """
        if fileName is None and modelName is None and not lmodel:  # all None
            raise Exception("Cannot create ModelicaSystem object without any arguments")

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
        self.setCommandLineOptions("--linearizationDumpLanguage=python")
        self.setCommandLineOptions("--generateSymbolicLinearization")

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
        if commandLineOptions is None:
            return
        exp = f'setCommandLineOptions("{commandLineOptions}")'
        if not self.sendExpression(exp):
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
                        libname = f"loadModel({element[0]})"
                    else:
                        libname = f'loadModel({element[0]}, {{"{element[1]}"}})'
                    result = self.sendExpression(libname)
                else:
                    raise ModelicaSystemError("loadLibrary() failed, Unknown type detected: "
                                              f"{element} is of type {type(element)}, "
                                              "The following patterns are supported:\n"
                                              '1)["Modelica"]\n'
                                              '2)[("Modelica","3.2.3"), "PowerSystems"]\n')
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

        logger.info("Define tempdir as %s", self.tempdir)
        exp = f'cd("{pathlib.Path(self.tempdir).as_posix()}")'
        self.sendExpression(exp)

    def getWorkDirectory(self):
        return self.tempdir

    def _run_cmd(self, cmd: list):
        logger.debug("Run OM command %s in %s", cmd, self.tempdir)

        if platform.system() == "Windows":
            dllPath = ""

            # set the process environment from the generated .bat file in windows which should have all the dependencies
            batFilePath = pathlib.Path(self.tempdir) / f"{self.modelName}.bat"
            if not batFilePath.exists():
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

        try:
            cmdres = subprocess.run(cmd, capture_output=True, text=True, env=my_env, cwd=self.tempdir)
            stdout = cmdres.stdout.strip()
            stderr = cmdres.stderr.strip()
            if cmdres.returncode != 0 or stderr:
                raise ModelicaSystemError(f"Error running command {cmd}: {stderr}")
            if self._verbose and stdout:
                logger.info("OM output for command %s:\n%s", cmd, stdout)
        except Exception as e:
            raise ModelicaSystemError(f"Exception {type(e)} running command {cmd}: {e}")

    def _check_error(self):
        errstr = self.sendExpression("getErrorString()")
        if not errstr:
            return
        self._raise_error(errstr=errstr)

    def _raise_error(self, errstr: str):
        if self._raiseerrors:
            raise ModelicaSystemError(f"OM error: {errstr}")
        else:
            logger.error(errstr)

    def buildModel(self, variableFilter=None):
        if variableFilter is not None:
            self.variableFilter = variableFilter

        if self.variableFilter is not None:
            varFilter = f'variableFilter="{self.variableFilter}"'
        else:
            varFilter = 'variableFilter=".*"'
        logger.debug("varFilter=%s", varFilter)
        buildModelResult = self.requestApi("buildModel", self.modelName, properties=varFilter)
        if self._verbose:
            logger.info("OM model build result: %s", buildModelResult)
        self._check_error()

        self.xmlFile = pathlib.Path(buildModelResult[0]).parent / buildModelResult[1]
        self.xmlparse()

    def sendExpression(self, expr, parsed=True):
        logger.debug("sendExpression(%r, %r)", expr, parsed)
        return self.getconn.sendExpression(expr, parsed)

    # request to OMC
    def requestApi(self, apiName, entity=None, properties=None):  # 2
        if entity is not None and properties is not None:
            exp = f'{apiName}({entity}, {properties})'
        elif entity is not None and properties is None:
            if apiName in ("loadFile", "importFMU"):
                exp = f'{apiName}("{entity}")'
            else:
                exp = f'{apiName}({entity})'
        else:
            exp = f'{apiName}()'
        try:
            res = self.sendExpression(exp)
        except Exception as e:
            self._raise_error(errstr=f"Exception {type(e)} raised: {e}")
            res = None
        return res

    def xmlparse(self):
        if not self.xmlFile.exists():
            self._raise_error(errstr=f"XML file not generated: {self.xmlFile}")
            return

        tree = ET.parse(self.xmlFile)
        rootCQ = tree.getroot()
        for attr in rootCQ.iter('DefaultExperiment'):
            for key in ("startTime", "stopTime", "stepSize", "tolerance",
                        "solver", "outputFormat"):
                self.simulateOptions[key] = attr.get(key)

        for sv in rootCQ.iter('ScalarVariable'):
            scalar = {}
            for key in ("name", "description", "variability", "causality", "alias"):
                scalar[key] = sv.get(key)
            scalar["changeable"] = sv.get('isValueChangeable')
            scalar["aliasvariable"] = sv.get('aliasVariable')
            ch = list(sv)
            for att in ch:
                scalar["start"] = att.get('start')
                scalar["min"] = att.get('min')
                scalar["max"] = att.get('max')
                scalar["unit"] = att.get('unit')

            if scalar["variability"] == "parameter":
                if scalar["name"] in self.overridevariables:
                    self.paramlist[scalar["name"]] = self.overridevariables[scalar["name"]]
                else:
                    self.paramlist[scalar["name"]] = scalar["start"]
            if scalar["variability"] == "continuous":
                self.continuouslist[scalar["name"]] = scalar["start"]
            if scalar["causality"] == "input":
                self.inputlist[scalar["name"]] = scalar["start"]
            if scalar["causality"] == "output":
                self.outputlist[scalar["name"]] = scalar["start"]

            self.quantitiesList.append(scalar)

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
        elif isinstance(names, str):
            return [x for x in self.quantitiesList if x["name"] == names]
        elif isinstance(names, list):
            return [x for y in names for x in self.quantitiesList if x["name"] == y]

        raise ModelicaSystemError("Unhandled input for getQuantities()")

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
                        raise ModelicaSystemError(f"OM error: {i} could not be computed")
                return self.continuouslist

            elif isinstance(names, str):
                if names in self.continuouslist:
                    value = self.getSolutions(names)
                    self.continuouslist[names] = value[0][-1]
                    return [self.continuouslist.get(names)]
                else:
                    raise ModelicaSystemError(f"OM error: {names} is not continuous")

            elif isinstance(names, list):
                valuelist = []
                for i in names:
                    if i in self.continuouslist:
                        value = self.getSolutions(i)
                        self.continuouslist[i] = value[0][-1]
                        valuelist.append(value[0][-1])
                    else:
                        raise ModelicaSystemError(f"OM error: {i} is not continuous")
                return valuelist

        raise ModelicaSystemError("Unhandled input for getContinous()")

    def getParameters(self, names: Optional[str | list[str]] = None) -> dict[str, str] | list[str]:  # 5
        """Get parameter values.

        Args:
            names: Either None (default), a string with the parameter name,
              or a list of parameter name strings.
        Returns:
            If `names` is None, a dict in the format
            {parameter_name: parameter_value} is returned.
            If `names` is a string, a single element list is returned.
            If `names` is a list, a list with one value for each parameter name
            in names is returned.
            In all cases, parameter values are returned as strings.

        Examples:
            >>> mod.getParameters()
            {'Name1': '1.23', 'Name2': '4.56'}
            >>> mod.getParameters("Name1")
            ['1.23']
            >>> mod.getParameters(["Name1","Name2"])
            ['1.23', '4.56']
        """
        if names is None:
            return self.paramlist
        elif isinstance(names, str):
            return [self.paramlist.get(names, "NotExist")]
        elif isinstance(names, list):
            return [self.paramlist.get(x, "NotExist") for x in names]

        raise ModelicaSystemError("Unhandled input for getParameters()")

    def getInputs(self, names: Optional[str | list[str]] = None) -> dict | list:  # 6
        """Get input values.

        Args:
            names: Either None (default), a string with the input name,
              or a list of input name strings.
        Returns:
            If `names` is None, a dict in the format
            {input_name: input_value} is returned.
            If `names` is a string, a single element list [input_value] is
            returned.
            If `names` is a list, a list with one value for each input name
            in names is returned: [input1_values, input2_values, ...].
            In all cases, input values are returned as a list of tuples,
            where the first element in the tuple is the time and the second
            element is the input value.

        Examples:
            >>> mod.getInputs()
            {'Name1': [(0.0, 0.0), (1.0, 1.0)], 'Name2': None}
            >>> mod.getInputs("Name1")
            [[(0.0, 0.0), (1.0, 1.0)]]
            >>> mod.getInputs(["Name1","Name2"])
            [[(0.0, 0.0), (1.0, 1.0)], None]
            >>> mod.getInputs("ThisInputDoesNotExist")
            ['NotExist']
        """
        if names is None:
            return self.inputlist
        elif isinstance(names, str):
            return [self.inputlist.get(names, "NotExist")]
        elif isinstance(names, list):
            return [self.inputlist.get(x, "NotExist") for x in names]

        raise ModelicaSystemError("Unhandled input for getInputs()")

    def getOutputs(self, names: Optional[str | list[str]] = None):  # 7
        """Get output values.

        If called before simulate(), the initial values are returned as
        strings. If called after simulate(), the final values (at stopTime)
        are returned as numpy.float64.

        Args:
            names: Either None (default), a string with the output name,
              or a list of output name strings.
        Returns:
            If `names` is None, a dict in the format
            {output_name: output_value} is returned.
            If `names` is a string, a single element list [output_value] is
            returned.
            If `names` is a list, a list with one value for each output name
            in names is returned: [output1_value, output2_value, ...].

        Examples:
            Before simulate():
            >>> mod.getOutputs()
            {'out1': '-0.4', 'out2': '1.2'}
            >>> mod.getOutputs("out1")
            ['-0.4']
            >>> mod.getOutputs(["out1","out2"])
            ['-0.4', '1.2']
            >>> mod.getOutputs("ThisOutputDoesNotExist")
            ['NotExist']

            After simulate():
            >>> mod.getOutputs()
            {'out1': np.float64(-0.1234), 'out2': np.float64(2.1)}
            >>> mod.getOutputs("out1")
            [np.float64(-0.1234)]
            >>> mod.getOutputs(["out1","out2"])
            [np.float64(-0.1234), np.float64(2.1)]
        """
        if not self.simulationFlag:
            if names is None:
                return self.outputlist
            elif isinstance(names, str):
                return [self.outputlist.get(names, "NotExist")]
            else:
                return [self.outputlist.get(x, "NotExist") for x in names]
        else:
            if names is None:
                for i in self.outputlist:
                    value = self.getSolutions(i)
                    self.outputlist[i] = value[0][-1]
                return self.outputlist
            elif isinstance(names, str):
                if names in self.outputlist:
                    value = self.getSolutions(names)
                    self.outputlist[names] = value[0][-1]
                    return [self.outputlist.get(names)]
                else:
                    return names, " is not Output"
            elif isinstance(names, list):
                valuelist = []
                for i in names:
                    if i in self.outputlist:
                        value = self.getSolutions(i)
                        self.outputlist[i] = value[0][-1]
                        valuelist.append(value[0][-1])
                    else:
                        return i, "is not Output"
                return valuelist

        raise ModelicaSystemError("Unhandled input for getOutputs()")

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
        elif isinstance(names, str):
            return [self.simulateOptions.get(names, "NotExist")]
        elif isinstance(names, list):
            return [self.simulateOptions.get(x, "NotExist") for x in names]

        raise ModelicaSystemError("Unhandled input for getSimulationOptions()")

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
        elif isinstance(names, str):
            return [self.linearOptions.get(names, "NotExist")]
        elif isinstance(names, list):
            return [self.linearOptions.get(x, "NotExist") for x in names]

        raise ModelicaSystemError("Unhandled input for getLinearizationOptions()")

    def getOptimizationOptions(self, names=None):  # 10
        """
        usage:
        >>> getOptimizationOptions()
        >>> getOptimizationOptions("Name1")
        >>> getOptimizationOptions(["Name1","Name2"])
        """
        if names is None:
            return self.optimizeOptions
        elif isinstance(names, str):
            return [self.optimizeOptions.get(names, "NotExist")]
        elif isinstance(names, list):
            return [self.optimizeOptions.get(x, "NotExist") for x in names]

        raise ModelicaSystemError("Unhandled input for getOptimizationOptions()")

    def get_exe_file(self) -> pathlib.Path:
        """Get path to model executable."""
        if platform.system() == "Windows":
            return pathlib.Path(self.tempdir) / f"{self.modelName}.exe"
        else:
            return pathlib.Path(self.tempdir) / self.modelName

    def simulate(self, resultfile=None, simflags=None):  # 11
        """
        This method simulates model according to the simulation options.
        usage
        >>> simulate()
        >>> simulate(resultfile="a.mat")
        >>> simulate(simflags="-noEventEmit -noRestart -override=e=0.3,g=10")  # set runtime simulation flags
        """
        if resultfile is None:
            r = ""
            self.resultfile = (pathlib.Path(self.tempdir) / f"{self.modelName}_res.mat").as_posix()
        else:
            if os.path.exists(resultfile):
                self.resultfile = resultfile
            else:
                self.resultfile = (pathlib.Path(self.tempdir) / resultfile).as_posix()
            r = " -r=" + self.resultfile

        # allow runtime simulation flags from user input
        if simflags is None:
            simflags = ""
        else:
            simflags = " " + simflags

        overrideFile = pathlib.Path(self.tempdir) / f"{self.modelName}_override.txt"
        if self.overridevariables or self.simoptionsoverride:
            tmpdict = self.overridevariables.copy()
            tmpdict.update(self.simoptionsoverride)
            # write to override file
            with open(overrideFile, "w") as file:
                for key, value in tmpdict.items():
                    file.write(f"{key}={value}\n")
            override = " -overrideFile=" + overrideFile.as_posix()
        else:
            override = ""

        if self.inputFlag:  # if model has input quantities
            for i in self.inputlist:
                val = self.inputlist[i]
                if val is None:
                    val = [(float(self.simulateOptions["startTime"]), 0.0),
                           (float(self.simulateOptions["stopTime"]), 0.0)]
                    self.inputlist[i] = [(float(self.simulateOptions["startTime"]), 0.0),
                                         (float(self.simulateOptions["stopTime"]), 0.0)]
                if float(self.simulateOptions["startTime"]) != val[0][0]:
                    errstr = f"!!! startTime not matched for Input {i}"
                    self._raise_error(errstr=errstr)
                    return
                if float(self.simulateOptions["stopTime"]) != val[-1][0]:
                    errstr = f"!!! stopTime not matched for Input {i}"
                    self._raise_error(errstr=errstr)
                    return
            self.createCSVData()  # create csv file
            csvinput = " -csvInput=" + self.csvFile
        else:
            csvinput = ""

        exe_file = self.get_exe_file()
        if not exe_file.exists():
            raise Exception(f"Error: Application file path not found: {exe_file}")

        cmd = exe_file.as_posix() + override + csvinput + r + simflags
        cmd = [s for s in cmd.split(' ') if s]
        self._run_cmd(cmd=cmd)
        self.simulationFlag = True

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
        if not os.path.exists(resFile):
            raise ModelicaSystemError(f"Result file does not exist {resFile}")
        resultVars = self.sendExpression(f'readSimulationResultVars("{resFile}")')
        self.sendExpression("closeSimulationResultFile()")
        if varList is None:
            return resultVars
        elif isinstance(varList, str):
            if varList not in resultVars and varList != "time":
                raise ModelicaSystemError(f"Requested data {repr(varList)} does not exist")
            res = self.sendExpression(f'readSimulationResult("{resFile}", {{{varList}}})')
            npRes = np.array(res)
            self.sendExpression("closeSimulationResultFile()")
            return npRes
        elif isinstance(varList, list):
            for var in varList:
                if var == "time":
                    continue
                if var not in resultVars:
                    raise ModelicaSystemError(f"Requested data {repr(var)} does not exist")
            variables = ",".join(varList)
            res = self.sendExpression(f'readSimulationResult("{resFile}",{{{variables}}})')
            npRes = np.array(res)
            self.sendExpression("closeSimulationResultFile()")
            return npRes

        raise ModelicaSystemError("Unhandled input for getSolutions()")

    def strip_space(self, name):
        if isinstance(name, str):
            return name.replace(" ", "")
        elif isinstance(name, list):
            return [x.replace(" ", "") for x in name]

        raise ModelicaSystemError("Unhandled input for strip_space()")

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
                raise ModelicaSystemError("Unhandled case in setMethodHelper.apply_single() - "
                                          f"{repr(value[0])} is not a {repr(args3)} variable")

        result = []
        if isinstance(args1, str):
            result = [apply_single(args1)]

        elif isinstance(args1, list):
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
        if q[0]["changeable"] == "false":
            if self._verbose:
                logger.info("setParameters() failed : It is not possible to set "
                            f'the following signal "{name}", It seems to be structural, final, '
                            "protected or evaluated or has a non-constant binding, use sendExpression("
                            f"setParameterValue({self.modelName}, {name}, {value}), "
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
        if isinstance(name, str):
            name = self.strip_space(name)
            value = name.split("=")
            if value[0] in self.inputlist:
                tmpvalue = eval(value[1])
                if isinstance(tmpvalue, int) or isinstance(tmpvalue, float):
                    self.inputlist[value[0]] = [(float(self.simulateOptions["startTime"]), float(value[1])),
                                                (float(self.simulateOptions["stopTime"]), float(value[1]))]
                elif isinstance(tmpvalue, list):
                    self.checkValidInputs(tmpvalue)
                    self.inputlist[value[0]] = tmpvalue
                self.inputFlag = True
            else:
                errstr = value[0] + " is not an input"
                self._raise_error(errstr=errstr)
        elif isinstance(name, list):
            name = self.strip_space(name)
            for var in name:
                value = var.split("=")
                if value[0] in self.inputlist:
                    tmpvalue = eval(value[1])
                    if isinstance(tmpvalue, int) or isinstance(tmpvalue, float):
                        self.inputlist[value[0]] = [(float(self.simulateOptions["startTime"]), float(value[1])),
                                                    (float(self.simulateOptions["stopTime"]), float(value[1]))]
                    elif isinstance(tmpvalue, list):
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
                    ModelicaSystemError(f'Value for {l} is in incorrect format!')
            else:
                ModelicaSystemError('Error!!! Value must be in tuple format')

    def createCSVData(self) -> None:
        start_time: float = float(self.simulateOptions["startTime"])
        stop_time: float = float(self.simulateOptions["stopTime"])

        # Replace None inputs with a default constant zero signal
        inputs: dict[str, list[tuple[float, float]]] = {}
        for input_name, input_signal in self.inputlist.items():
            if input_signal is None:
                inputs[input_name] = [(start_time, 0.0), (stop_time, 0.0)]
            else:
                inputs[input_name] = input_signal

        # Collect all unique timestamps across all input signals
        all_times = np.array(
            sorted({t for signal in inputs.values() for t, _ in signal}),
            dtype=float
        )

        # Interpolate missing values
        interpolated_inputs: dict[str, np.ndarray] = {}
        for signal_name, signal_values in inputs.items():
            signal = np.array(signal_values)
            interpolated_inputs[signal_name] = np.interp(
                all_times,
                signal[:, 0],  # times
                signal[:, 1]  # values
            )

        # Write CSV file
        input_names = list(interpolated_inputs.keys())
        header = ['time'] + input_names + ['end']

        csv_rows = [header]
        for i, t in enumerate(all_times):
            row = [
                t,  # time
                *(interpolated_inputs[name][i] for name in input_names),  # input values
                0  # trailing 'end' column
            ]
            csv_rows.append(row)

        self.csvFile: str = (pathlib.Path(self.tempdir) / f'{self.modelName}.csv').as_posix()

        with open(self.csvFile, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)

    # to convert Modelica model to FMU
    def convertMo2Fmu(self, version="2.0", fmuType="me_cs", fileNamePrefix="<default>", includeResources=True):  # 19
        """
        This method is used to generate FMU from the given Modelica model. It creates "modelName.fmu" in the current working directory. It can be called:
        with no arguments
        with arguments of https://build.openmodelica.org/Documentation/OpenModelica.Scripting.translateModelFMU.html
        usage
        >>> convertMo2Fmu()
        >>> convertMo2Fmu(version="2.0", fmuType="me|cs|me_cs", fileNamePrefix="<default>", includeResources=True)
        """

        if fileNamePrefix == "<default>":
            fileNamePrefix = self.modelName
        if includeResources:
            includeResourcesStr = "true"
        else:
            includeResourcesStr = "false"
        properties = f'version="{version}", fmuType="{fmuType}", fileNamePrefix="{fileNamePrefix}", includeResources={includeResourcesStr}'
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
        properties = ','.join(f"{key}={val}" for key, val in self.optimizeOptions.items())
        self.setCommandLineOptions("-g=Optimica")
        optimizeResult = self.requestApi('optimize', cName, properties)
        self._check_error()

        return optimizeResult

    def linearize(self, lintime: Optional[float] = None, simflags: Optional[str] = None) -> LinearizationResult:
        """Linearize the model according to linearOptions.

        Args:
            lintime: Override linearOptions["stopTime"] value.
            simflags: A string of extra command line flags for the model
              binary.

        Returns:
            A LinearizationResult object is returned. This allows several
            uses:
            * `(A, B, C, D) = linearize()` to get just the matrices,
            * `result = linearize(); result.A` to get everything and access the
              attributes one by one,
            * `result = linearize(); A = result[0]` mostly just for backwards
              compatibility, because linearize() used to return `[A, B, C, D]`.
        """

        if self.xmlFile is None:
            raise IOError("Linearization cannot be performed as the model is not build, "
                          "use ModelicaSystem() to build the model first")

        overrideLinearFile = pathlib.Path(self.tempdir) / f'{self.modelName}_override_linear.txt'

        with open(overrideLinearFile, "w") as file:
            for key, value in self.overridevariables.items():
                file.write(f"{key}={value}\n")
            for key, value in self.linearOptions.items():
                file.write(f"{key}={value}\n")

        override = " -overrideFile=" + overrideLinearFile.as_posix()
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
        exe_file = self.get_exe_file()

        linruntime = f' -l={lintime or self.linearOptions["stopTime"]}'

        if simflags is None:
            simflags = ""
        else:
            simflags = " " + simflags

        if not exe_file.exists():
            raise Exception(f"Error: Application file path not found: {exe_file}")
        else:
            cmd = exe_file.as_posix() + linruntime + override + csvinput + simflags
            cmd = [s for s in cmd.split(' ') if s]
            self._run_cmd(cmd=cmd)

        # code to get the matrix and linear inputs, outputs and states
        linearFile = pathlib.Path(self.tempdir) / "linearized_model.py"

        # support older openmodelica versions before OpenModelica v1.16.2 where linearize() generates "linear_modelname.mo" file
        if not linearFile.exists():
            linearFile = pathlib.Path(f'linear_{self.modelName}.py')

        if not linearFile.exists():
            errormsg = self.sendExpression("getErrorString()")
            raise ModelicaSystemError(f"Linearization failed: {linearFile} not found: {errormsg}")

        # this function is called from the generated python code linearized_model.py at runtime,
        # to improve the performance by directly reading the matrices A, B, C and D from the julia code and avoid building the linearized modelica model
        try:
            # do not add the linearfile directory to path, as multiple execution of linearization will always use the first added path, instead execute the file
            # https://github.com/OpenModelica/OMPython/issues/196
            module = importlib.machinery.SourceFileLoader("linearized_model", linearFile.as_posix()).load_module()
            result = module.linearized_model()
            (n, m, p, x0, u0, A, B, C, D, stateVars, inputVars, outputVars) = result
            self.linearinputs = inputVars
            self.linearoutputs = outputVars
            self.linearstates = stateVars
            return LinearizationResult(n, m, p, A, B, C, D, x0, u0, stateVars,
                                       inputVars, outputVars)
        except ModuleNotFoundError:
            raise Exception("ModuleNotFoundError: No module named 'linearized_model'")

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
