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
from dataclasses import dataclass
import importlib
import logging
import numbers
import numpy as np
import os
import pathlib
import platform
import re
import subprocess
import tempfile
import textwrap
from typing import Optional, Any
import warnings
import xml.etree.ElementTree as ET

from OMPython.OMCSession import OMCSessionException, OMCSessionZMQ

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaSystemError(Exception):
    """
    Exception used in ModelicaSystem and ModelicaSystemCmd classes.
    """


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


class ModelicaSystemCmd:
    """
    Execute a simulation by running the compiled model.
    """

    def __init__(self, runpath: pathlib.Path, modelname: str, timeout: Optional[int] = None) -> None:
        """
        Initialisation

        Parameters
        ----------
        runpath : pathlib.Path
        modelname : str
        timeout : Optional[int], None
        """
        self._runpath = pathlib.Path(runpath).resolve().absolute()
        self._modelname = modelname
        self._timeout = timeout
        self._args: dict[str, str | None] = {}
        self._arg_override: dict[str, str] = {}

    def arg_set(self, key: str, val: Optional[str | dict] = None) -> None:
        """
        Set one argument for the executable model.

        Parameters
        ----------
        key : str
        val : str, None
        """
        if not isinstance(key, str):
            raise ModelicaSystemError(f"Invalid argument key: {repr(key)} (type: {type(key)})")
        key = key.strip()
        if val is None:
            argval = None
        elif isinstance(val, str):
            argval = val.strip()
        elif isinstance(val, numbers.Number):
            argval = str(val)
        elif key == 'override' and isinstance(val, dict):
            for okey in val:
                if not isinstance(okey, str) or not isinstance(val[okey], (str, numbers.Number)):
                    raise ModelicaSystemError("Invalid argument for 'override': "
                                              f"{repr(okey)} = {repr(val[okey])}")
                self._arg_override[okey] = val[okey]

            argval = ','.join([f"{okey}={str(self._arg_override[okey])}" for okey in self._arg_override])
        else:
            raise ModelicaSystemError(f"Invalid argument value for {repr(key)}: {repr(val)} (type: {type(val)})")

        if key in self._args:
            logger.warning(f"Overwrite model executable argument: {repr(key)} = {repr(argval)} "
                           f"(was: {repr(self._args[key])})")
        self._args[key] = argval

    def args_set(self, args: dict[str, Optional[str | dict[str, str]]]) -> None:
        """
        Define arguments for the model executable.

        Parameters
        ----------
        args : dict[str, Optional[str | dict[str, str]]]
        """
        for arg in args:
            self.arg_set(key=arg, val=args[arg])

    def get_exe(self) -> pathlib.Path:
        """
        Get the path to the executable / complied model.

        Returns
        -------
            pathlib.Path
        """
        if platform.system() == "Windows":
            path_exe = self._runpath / f"{self._modelname}.exe"
        else:
            path_exe = self._runpath / self._modelname

        if not path_exe.exists():
            raise ModelicaSystemError(f"Application file path not found: {path_exe}")

        return path_exe

    def get_cmd(self) -> list:
        """
        Run the requested simulation

        Returns
        -------
            list
        """

        path_exe = self.get_exe()

        cmdl = [path_exe.as_posix()]
        for key in self._args:
            if self._args[key] is None:
                cmdl.append(f"-{key}")
            else:
                cmdl.append(f"-{key}={self._args[key]}")

        return cmdl

    def run(self) -> int:
        """
        Run the requested simulation

        Returns
        -------
            int
        """

        cmdl: list = self.get_cmd()

        logger.debug("Run OM command %s in %s", repr(cmdl), self._runpath.as_posix())

        if platform.system() == "Windows":
            path_dll = ""

            # set the process environment from the generated .bat file in windows which should have all the dependencies
            path_bat = self._runpath / f"{self._modelname}.bat"
            if not path_bat.exists():
                raise ModelicaSystemError("Batch file (*.bat) does not exist " + str(path_bat))

            with open(file=path_bat, mode='r', encoding='utf-8') as fh:
                for line in fh:
                    match = re.match(r"^SET PATH=([^%]*)", line, re.IGNORECASE)
                    if match:
                        path_dll = match.group(1).strip(';')  # Remove any trailing semicolons
            my_env = os.environ.copy()
            my_env["PATH"] = path_dll + os.pathsep + my_env["PATH"]
        else:
            # TODO: how to handle path to resources of external libraries for any system not Windows?
            my_env = None

        try:
            cmdres = subprocess.run(cmdl, capture_output=True, text=True, env=my_env, cwd=self._runpath,
                                    timeout=self._timeout, check=True)
            stdout = cmdres.stdout.strip()
            stderr = cmdres.stderr.strip()
            returncode = cmdres.returncode

            logger.debug("OM output for command %s:\n%s", repr(cmdl), stdout)

            if stderr:
                raise ModelicaSystemError(f"Error running command {repr(cmdl)}: {stderr}")
        except subprocess.TimeoutExpired as ex:
            raise ModelicaSystemError(f"Timeout running command {repr(cmdl)}") from ex
        except subprocess.CalledProcessError as ex:
            raise ModelicaSystemError(f"Error running command {repr(cmdl)}") from ex

        return returncode

    @staticmethod
    def parse_simflags(simflags: str) -> dict[str, Optional[str | dict[str, str]]]:
        """
        Parse a simflag definition; this is depreciated!

        The return data can be used as input for self.args_set().

        Parameters
        ----------
        simflags : str

        Returns
        -------
            dict
        """
        warnings.warn("The argument 'simflags' is depreciated and will be removed in future versions; "
                      "please use 'simargs' instead", DeprecationWarning, stacklevel=2)

        simargs: dict[str, Optional[str | dict[str, str]]] = {}

        args = [s for s in simflags.split(' ') if s]
        for arg in args:
            if arg[0] != '-':
                raise ModelicaSystemError(f"Invalid simulation flag: {arg}")
            arg = arg[1:]
            parts = arg.split('=')
            if len(parts) == 1:
                simargs[parts[0]] = None
            elif parts[0] == 'override':
                override = '='.join(parts[1:])

                override_dict = {}
                for item in override.split(','):
                    kv = item.split('=')
                    if not 0 < len(kv) < 3:
                        raise ModelicaSystemError(f"Invalid value for '-override': {override}")
                    if kv[0]:
                        try:
                            override_dict[kv[0]] = kv[1]
                        except (KeyError, IndexError) as ex:
                            raise ModelicaSystemError(f"Invalid value for '-override': {override}") from ex

                simargs[parts[0]] = override_dict

        return simargs


class ModelicaSystem:
    def __init__(
            self,
            fileName: Optional[str | os.PathLike | pathlib.Path] = None,
            modelName: Optional[str] = None,
            lmodel: Optional[list[str | tuple[str, str]]] = None,
            commandLineOptions: Optional[str] = None,
            variableFilter: Optional[str] = None,
            customBuildDirectory: Optional[str | os.PathLike | pathlib.Path] = None,
            omhome: Optional[str] = None,
            session: Optional[OMCSessionZMQ] = None,
            build: bool = True,
    ) -> None:
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
            omhome: OPENMODELICAHOME value to be used when creating the OMC
              session.
            session: OMC session to be used. If unspecified, a new session
              will be created.
            build: Boolean controlling whether or not the model should be
              built when constructor is called. If False, the constructor
              simply loads the model without compiling.

        Examples:
            mod = ModelicaSystem("ModelicaModel.mo", "modelName")
            mod = ModelicaSystem("ModelicaModel.mo", "modelName", ["Modelica"])
            mod = ModelicaSystem("ModelicaModel.mo", "modelName", [("Modelica","3.2.3"), "PowerSystems"])
        """

        if fileName is None and modelName is None and not lmodel:  # all None
            raise ModelicaSystemError("Cannot create ModelicaSystem object without any arguments")

        if modelName is None:
            raise ModelicaSystemError("A modelname must be provided (argument modelName)!")

        self.quantitiesList: list[dict[str, Any]] = []
        self.paramlist: dict[str, str] = {}  # even numerical values are stored as str
        self.inputlist: dict[str, list | None] = {}
        # outputlist values are str before simulate(), but they can be
        # np.float64 after simulate().
        self.outputlist: dict[str, Any] = {}
        # same for continuouslist
        self.continuouslist: dict[str, Any] = {}
        self.simulateOptions: dict[str, str] = {}
        self.overridevariables: dict[str, str] = {}
        self.simoptionsoverride: dict[str, str] = {}
        self.linearOptions = {'startTime': 0.0, 'stopTime': 1.0, 'stepSize': 0.002, 'tolerance': 1e-8}
        self.optimizeOptions = {'startTime': 0.0, 'stopTime': 1.0, 'numberOfIntervals': 500, 'stepSize': 0.002,
                                'tolerance': 1e-8}
        self.linearinputs: list[str] = []  # linearization input list
        self.linearoutputs: list[str] = []  # linearization output list
        self.linearstates: list[str] = []  # linearization states list

        if session is not None:
            if not isinstance(session, OMCSessionZMQ):
                raise ModelicaSystemError("Invalid session data provided!")
            self.getconn = session
        else:
            self.getconn = OMCSessionZMQ(omhome=omhome)

        # set commandLineOptions if provided by users
        self.setCommandLineOptions(commandLineOptions=commandLineOptions)

        if lmodel is None:
            lmodel = []

        if not isinstance(lmodel, list):
            raise ModelicaSystemError(f"Invalid input type for lmodel: {type(lmodel)} - list expected!")

        self.xmlFile = None
        self.lmodel = lmodel  # may be needed if model is derived from other model
        self.modelName = modelName  # Model class name
        self.fileName = pathlib.Path(fileName).resolve() if fileName is not None else None  # Model file/package name
        self.inputFlag = False  # for model with input quantity
        self.simulationFlag = False  # if the model is simulated?
        self.outputFlag = False
        self.csvFile: Optional[pathlib.Path] = None  # for storing inputs condition
        self.resultfile: Optional[pathlib.Path] = None  # for storing result file
        self.variableFilter = variableFilter

        if self.fileName is not None and not self.fileName.is_file():  # if file does not exist
            raise IOError(f"{self.fileName} does not exist!")

        # set default command Line Options for linearization as
        # linearize() will use the simulation executable and runtime
        # flag -l to perform linearization
        self.setCommandLineOptions("--linearizationDumpLanguage=python")
        self.setCommandLineOptions("--generateSymbolicLinearization")

        self.tempdir = self.setTempDirectory(customBuildDirectory)

        if self.fileName is not None:
            self.loadLibrary(lmodel=self.lmodel)
            self.loadFile(fileName=self.fileName)

        # allow directly loading models from MSL without fileName
        elif fileName is None and modelName is not None:
            self.loadLibrary(lmodel=self.lmodel)

        if build:
            self.buildModel(variableFilter)

    def setCommandLineOptions(self, commandLineOptions: Optional[str] = None):
        # set commandLineOptions if provided by users
        if commandLineOptions is None:
            return
        exp = f'setCommandLineOptions("{commandLineOptions}")'
        self.sendExpression(exp)

    def loadFile(self, fileName: pathlib.Path):
        # load file
        self.sendExpression(f'loadFile("{fileName.as_posix()}")')

    # for loading file/package, loading model and building model
    def loadLibrary(self, lmodel: list):
        # load Modelica standard libraries or Modelica files if needed
        for element in lmodel:
            if element is not None:
                if isinstance(element, str):
                    if element.endswith(".mo"):
                        apiCall = "loadFile"
                    else:
                        apiCall = "loadModel"
                    self.requestApi(apiCall, element)
                elif isinstance(element, tuple):
                    if not element[1]:
                        expr_load_lib = f"loadModel({element[0]})"
                    else:
                        expr_load_lib = f'loadModel({element[0]}, {{"{element[1]}"}})'
                    self.sendExpression(expr_load_lib)
                else:
                    raise ModelicaSystemError("loadLibrary() failed, Unknown type detected: "
                                              f"{element} is of type {type(element)}, "
                                              "The following patterns are supported:\n"
                                              '1)["Modelica"]\n'
                                              '2)[("Modelica","3.2.3"), "PowerSystems"]\n')

    def setTempDirectory(self, customBuildDirectory: Optional[str | os.PathLike | pathlib.Path] = None) -> pathlib.Path:
        # create a unique temp directory for each session and build the model in that directory
        if customBuildDirectory is not None:
            if not os.path.exists(customBuildDirectory):
                raise IOError(customBuildDirectory, " does not exist")
            tempdir = pathlib.Path(customBuildDirectory)
        else:
            tempdir = pathlib.Path(tempfile.mkdtemp())
            if not tempdir.is_dir():
                raise IOError(tempdir, " cannot be created")

        logger.info("Define tempdir as %s", tempdir)
        exp = f'cd("{tempdir.absolute().as_posix()}")'
        self.sendExpression(exp)

        return tempdir

    def getWorkDirectory(self) -> pathlib.Path:
        return self.tempdir

    def buildModel(self, variableFilter: Optional[str] = None):
        if variableFilter is not None:
            self.variableFilter = variableFilter

        if self.variableFilter is not None:
            varFilter = f'variableFilter="{self.variableFilter}"'
        else:
            varFilter = 'variableFilter=".*"'

        buildModelResult = self.requestApi("buildModel", self.modelName, properties=varFilter)
        logger.debug("OM model build result: %s", buildModelResult)

        self.xmlFile = pathlib.Path(buildModelResult[0]).parent / buildModelResult[1]
        self.xmlparse()

    def sendExpression(self, expr: str, parsed: bool = True):
        try:
            retval = self.getconn.sendExpression(expr, parsed)
        except OMCSessionException as ex:
            raise ModelicaSystemError(f"Error executing {repr(expr)}") from ex

        logger.debug(f"Result of executing {repr(expr)}: {textwrap.shorten(repr(retval), width=100)}")

        return retval

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

        return self.sendExpression(exp)

    def xmlparse(self):
        if not self.xmlFile.is_file():
            raise ModelicaSystemError(f"XML file not generated: {self.xmlFile}")

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

        if isinstance(names, str):
            return [x for x in self.quantitiesList if x["name"] == names]

        if isinstance(names, list):
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

            if isinstance(names, str):
                return [self.continuouslist.get(names, "NotExist")]

            if isinstance(names, list):
                return [self.continuouslist.get(x, "NotExist") for x in names]
        else:
            if names is None:
                for i in self.continuouslist:
                    try:
                        value = self.getSolutions(i)
                        self.continuouslist[i] = value[0][-1]
                    except (OMCSessionException, ModelicaSystemError) as ex:
                        raise ModelicaSystemError(f"{i} could not be computed") from ex
                return self.continuouslist

            if isinstance(names, str):
                if names in self.continuouslist:
                    value = self.getSolutions(names)
                    self.continuouslist[names] = value[0][-1]
                    return [self.continuouslist.get(names)]
                else:
                    raise ModelicaSystemError(f"{names} is not continuous")

            if isinstance(names, list):
                valuelist = []
                for i in names:
                    if i in self.continuouslist:
                        value = self.getSolutions(i)
                        self.continuouslist[i] = value[0][-1]
                        valuelist.append(value[0][-1])
                    else:
                        raise ModelicaSystemError(f"{i} is not continuous")
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

    def simulate(self, resultfile: Optional[str] = None, simflags: Optional[str] = None,
                 simargs: Optional[dict[str, Optional[str | dict[str, str]]]] = None,
                 timeout: Optional[int] = None):  # 11
        """
        This method simulates model according to the simulation options.
        usage
        >>> simulate()
        >>> simulate(resultfile="a.mat")
        >>> simulate(simflags="-noEventEmit -noRestart -override=e=0.3,g=10")  # set runtime simulation flags
        >>> simulate(simargs={"noEventEmit": None, "noRestart": None, "override": "e=0.3,g=10"})  # using simargs
        """

        om_cmd = ModelicaSystemCmd(runpath=self.tempdir, modelname=self.modelName, timeout=timeout)

        if resultfile is None:
            # default result file generated by OM
            self.resultfile = self.tempdir / f"{self.modelName}_res.mat"
        elif os.path.exists(resultfile):
            self.resultfile = pathlib.Path(resultfile)
        else:
            self.resultfile = self.tempdir / resultfile
        # always define the resultfile to use
        om_cmd.arg_set(key="r", val=self.resultfile.as_posix())

        # allow runtime simulation flags from user input
        if simflags is not None:
            om_cmd.args_set(args=om_cmd.parse_simflags(simflags=simflags))

        if simargs:
            om_cmd.args_set(args=simargs)

        overrideFile = self.tempdir / f"{self.modelName}_override.txt"
        if self.overridevariables or self.simoptionsoverride:
            tmpdict = self.overridevariables.copy()
            tmpdict.update(self.simoptionsoverride)
            # write to override file
            with open(file=overrideFile, mode="w", encoding="utf-8") as fh:
                for key, value in tmpdict.items():
                    fh.write(f"{key}={value}\n")

            om_cmd.arg_set(key="overrideFile", val=overrideFile.as_posix())

        if self.inputFlag:  # if model has input quantities
            for i in self.inputlist:
                val = self.inputlist[i]
                if val is None:
                    val = [(float(self.simulateOptions["startTime"]), 0.0),
                           (float(self.simulateOptions["stopTime"]), 0.0)]
                    self.inputlist[i] = [(float(self.simulateOptions["startTime"]), 0.0),
                                         (float(self.simulateOptions["stopTime"]), 0.0)]
                if float(self.simulateOptions["startTime"]) != val[0][0]:
                    raise ModelicaSystemError(f"startTime not matched for Input {i}!")
                if float(self.simulateOptions["stopTime"]) != val[-1][0]:
                    raise ModelicaSystemError(f"stopTime not matched for Input {i}!")
            self.csvFile = self.createCSVData()  # create csv file

            om_cmd.arg_set(key="csvInput", val=self.csvFile.as_posix())

        # delete resultfile ...
        if self.resultfile.is_file():
            self.resultfile.unlink()
        # ... run simulation ...
        returncode = om_cmd.run()
        # and check returncode *AND* resultfile
        if returncode != 0 and self.resultfile.is_file():
            logger.warning(f"Return code = {returncode} but result file exists!")

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
            resFile = self.resultfile.as_posix()
        else:
            resFile = resultfile

        # check for result file exits
        if not os.path.exists(resFile):
            raise ModelicaSystemError(f"Result file does not exist {resFile}")
        resultVars = self.sendExpression(f'readSimulationResultVars("{resFile}")')
        self.sendExpression("closeSimulationResultFile()")
        if varList is None:
            return resultVars

        if isinstance(varList, str):
            if varList not in resultVars and varList != "time":
                raise ModelicaSystemError(f"Requested data {repr(varList)} does not exist")
            res = self.sendExpression(f'readSimulationResult("{resFile}", {{{varList}}})')
            npRes = np.array(res)
            self.sendExpression("closeSimulationResultFile()")
            return npRes

        if isinstance(varList, list):
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

    @staticmethod
    def _strip_space(name):
        if isinstance(name, str):
            return name.replace(" ", "")

        if isinstance(name, list):
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
            args1 = self._strip_space(args1)
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
            args1 = self._strip_space(args1)
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
            logger.verbose(f"setParameters() failed : It is not possible to set the following signal {repr(name)}. "
                           "It seems to be structural, final, protected or evaluated or has a non-constant binding, "
                           f"use sendExpression(\"setParameterValue({self.modelName}, {name}, {value})\") "
                           "and rebuild the model using buildModel() API")
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
            name = self._strip_space(name)
            value = name.split("=")
            if value[0] in self.inputlist:
                tmpvalue = eval(value[1])
                if isinstance(tmpvalue, (int, float)):
                    self.inputlist[value[0]] = [(float(self.simulateOptions["startTime"]), float(value[1])),
                                                (float(self.simulateOptions["stopTime"]), float(value[1]))]
                elif isinstance(tmpvalue, list):
                    self.checkValidInputs(tmpvalue)
                    self.inputlist[value[0]] = tmpvalue
                self.inputFlag = True
            else:
                raise ModelicaSystemError(f"{value[0]} is not an input")
        elif isinstance(name, list):
            name = self._strip_space(name)
            for var in name:
                value = var.split("=")
                if value[0] in self.inputlist:
                    tmpvalue = eval(value[1])
                    if isinstance(tmpvalue, (int, float)):
                        self.inputlist[value[0]] = [(float(self.simulateOptions["startTime"]), float(value[1])),
                                                    (float(self.simulateOptions["stopTime"]), float(value[1]))]
                    elif isinstance(tmpvalue, list):
                        self.checkValidInputs(tmpvalue)
                        self.inputlist[value[0]] = tmpvalue
                    self.inputFlag = True
                else:
                    raise ModelicaSystemError(f"{value[0]} is not an input!")

    def checkValidInputs(self, name):
        if name != sorted(name, key=lambda x: x[0]):
            raise ModelicaSystemError('Time value should be in increasing order')
        for l in name:
            if isinstance(l, tuple):
                # if l[0] < float(self.simValuesList[0]):
                if l[0] < float(self.simulateOptions["startTime"]):
                    raise ModelicaSystemError('Input time value is less than simulation startTime')
                if len(l) != 2:
                    raise ModelicaSystemError(f'Value for {l} is in incorrect format!')
            else:
                raise ModelicaSystemError('Error!!! Value must be in tuple format')

    def createCSVData(self) -> pathlib.Path:
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

        csvFile = self.tempdir / f'{self.modelName}.csv'

        with open(file=csvFile, mode="w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerows(csv_rows)

        return csvFile

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
            raise ModelicaSystemError(f"Missing FMU file: {fmu}")

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
            raise ModelicaSystemError(f"Missing file {fileName}")

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

        return optimizeResult

    def linearize(self, lintime: Optional[float] = None, simflags: Optional[str] = None,
                  simargs: Optional[dict[str, Optional[str | dict[str, str]]]] = None,
                  timeout: Optional[int] = None) -> LinearizationResult:
        """Linearize the model according to linearOptions.

        Args:
            lintime: Override linearOptions["stopTime"] value.
            simflags: A string of extra command line flags for the model
              binary. - depreciated in favor of simargs
            simargs: A dict with command line flags and possible options; example: "simargs={'csvInput': 'a.csv'}"
            timeout: Possible timeout for the execution of OM.

        Returns:
            A LinearizationResult object is returned. This allows several
            uses:
            * `(A, B, C, D) = linearize()` to get just the matrices,
            * `result = linearize(); result.A` to get everything and access the
              attributes one by one,
            * `result = linearize(); A = result[0]` mostly just for backwards
              compatibility, because linearize() used to return `[A, B, C, D]`.
        """

        # replacement for depreciated importlib.load_module()
        def load_module_from_path(module_name, file_path):
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module_def = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module_def)

            return module_def

        if self.xmlFile is None:
            raise IOError("Linearization cannot be performed as the model is not build, "
                          "use ModelicaSystem() to build the model first")

        om_cmd = ModelicaSystemCmd(runpath=self.tempdir, modelname=self.modelName, timeout=timeout)

        overrideLinearFile = self.tempdir / f'{self.modelName}_override_linear.txt'

        with open(file=overrideLinearFile, mode="w", encoding="utf-8") as fh:
            for key, value in self.overridevariables.items():
                fh.write(f"{key}={value}\n")
            for key, value in self.linearOptions.items():
                fh.write(f"{key}={value}\n")

        om_cmd.arg_set(key="overrideFile", val=overrideLinearFile.as_posix())

        if self.inputFlag:
            nameVal = self.getInputs()
            for n in nameVal:
                tupleList = nameVal.get(n)
                if tupleList is not None:
                    for l in tupleList:
                        if l[0] < float(self.simulateOptions["startTime"]):
                            raise ModelicaSystemError('Input time value is less than simulation startTime')
            self.csvFile = self.createCSVData()
            om_cmd.arg_set(key="csvInput", val=self.csvFile.as_posix())

        om_cmd.arg_set(key="l", val=str(lintime or self.linearOptions["stopTime"]))

        # allow runtime simulation flags from user input
        if simflags is not None:
            om_cmd.args_set(args=om_cmd.parse_simflags(simflags=simflags))

        if simargs:
            om_cmd.args_set(args=simargs)

        returncode = om_cmd.run()
        if returncode != 0:
            raise ModelicaSystemError(f"Linearize failed with return code: {returncode}")

        self.simulationFlag = True

        # code to get the matrix and linear inputs, outputs and states
        linearFile = self.tempdir / "linearized_model.py"

        # support older openmodelica versions before OpenModelica v1.16.2 where linearize() generates "linear_modelname.mo" file
        if not linearFile.exists():
            linearFile = pathlib.Path(f'linear_{self.modelName}.py')

        if not linearFile.exists():
            raise ModelicaSystemError(f"Linearization failed: {linearFile} not found!")

        # this function is called from the generated python code linearized_model.py at runtime,
        # to improve the performance by directly reading the matrices A, B, C and D from the julia code and avoid building the linearized modelica model
        try:
            # do not add the linearfile directory to path, as multiple execution of linearization will always use the first added path, instead execute the file
            # https://github.com/OpenModelica/OMPython/issues/196
            module = load_module_from_path(module_name="linearized_model", file_path=linearFile.as_posix())

            result = module.linearized_model()
            (n, m, p, x0, u0, A, B, C, D, stateVars, inputVars, outputVars) = result
            self.linearinputs = inputVars
            self.linearoutputs = outputVars
            self.linearstates = stateVars
            return LinearizationResult(n, m, p, A, B, C, D, x0, u0, stateVars,
                                       inputVars, outputVars)
        except ModuleNotFoundError as ex:
            raise ModelicaSystemError("No module named 'linearized_model'") from ex

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
