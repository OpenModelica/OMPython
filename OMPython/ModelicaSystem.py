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

import ast
import csv
from dataclasses import dataclass
import importlib
import itertools
import logging
import numbers
import numpy as np
import os
import pandas as pd
import pathlib
import platform
import queue
import re
import subprocess
import tempfile
import textwrap
import threading
from typing import Any, Optional
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

    def arg_get(self, key: str) -> Optional[str | dict]:
        """
        Return the value for the given key
        """
        if key in self._args:
            return self._args[key]

        return None

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
                raise IOError(f"{customBuildDirectory} does not exist")
            tempdir = pathlib.Path(customBuildDirectory).absolute()
        else:
            tempdir = pathlib.Path(tempfile.mkdtemp()).absolute()
            if not tempdir.is_dir():
                raise IOError(f"{tempdir} could not be created")

        logger.info("Define tempdir as %s", tempdir)
        exp = f'cd("{tempdir.as_posix()}")'
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

    def getQuantities(self, names: Optional[str | list[str]] = None) -> list[dict]:
        """
        This method returns list of dictionaries. It displays details of
        quantities such as name, value, changeable, and description.

        Examples:
            >>> mod.getQuantities()
            [
              {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'local',
                'changeable': 'true',
                'description': None,
                'max': None,
                'min': None,
                'name': 'x',
                'start': '1.0',
                'unit': None,
                'variability': 'continuous',
              },
              {
                'name': 'der(x)',
                # ...
              },
              # ...
            ]

            >>> getQuantities("y")
            [{
              'name': 'y', # ...
            }]

            >>> getQuantities(["y","x"])
            [
              {
                'name': 'y', # ...
              },
              {
                'name': 'x', # ...
              }
            ]
        """
        if names is None:
            return self.quantitiesList

        if isinstance(names, str):
            r = [x for x in self.quantitiesList if x["name"] == names]
            if r == []:
                raise KeyError(names)
            return r

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
                return [self.continuouslist[names]]

            if isinstance(names, list):
                return [self.continuouslist[x] for x in names]
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
                    return [self.continuouslist[names]]
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
            return [self.paramlist[names]]
        elif isinstance(names, list):
            return [self.paramlist[x] for x in names]

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
        """
        if names is None:
            return self.inputlist
        elif isinstance(names, str):
            return [self.inputlist[names]]
        elif isinstance(names, list):
            return [self.inputlist[x] for x in names]

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
                return [self.outputlist[names]]
            else:
                return [self.outputlist[x] for x in names]
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
                    return [self.outputlist[names]]
                else:
                    raise KeyError(names)
            elif isinstance(names, list):
                valuelist = []
                for i in names:
                    if i in self.outputlist:
                        value = self.getSolutions(i)
                        self.outputlist[i] = value[0][-1]
                        valuelist.append(value[0][-1])
                    else:
                        raise KeyError(i)
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
            return [self.simulateOptions[names]]
        elif isinstance(names, list):
            return [self.simulateOptions[x] for x in names]

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
            return [self.linearOptions[names]]
        elif isinstance(names, list):
            return [self.linearOptions[x] for x in names]

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
            return [self.optimizeOptions[names]]
        elif isinstance(names, list):
            return [self.optimizeOptions[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getOptimizationOptions()")

    def simulate_cmd(
            self,
            resultfile: pathlib.Path,
            simflags: Optional[str] = None,
            simargs: Optional[dict[str, Optional[str | dict[str, str]]]] = None,
            timeout: Optional[int] = None,
    ) -> ModelicaSystemCmd:
        """
        This method prepares the simulates model according to the simulation options. It returns an instance of
        ModelicaSystemCmd which can be used to run the simulation.

        Due to the tempdir being unique for the ModelicaSystem instance, *NEVER* use this to create several simulations
        with the same instance of ModelicaSystem! Restart each simulation process with a new instance of ModelicaSystem.

        However, if only non-structural parameters are used, it is possible to reuse an existing instance of
        ModelicaSystem to create several version ModelicaSystemCmd to run the model using different settings.

        Parameters
        ----------
        resultfile
        simflags
        simargs
        timeout

        Returns
        -------
            An instance if ModelicaSystemCmd to run the requested simulation.
        """

        om_cmd = ModelicaSystemCmd(runpath=self.tempdir, modelname=self.modelName, timeout=timeout)

        # always define the result file to use
        om_cmd.arg_set(key="r", val=resultfile.as_posix())

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
            # csvfile is based on name used for result file
            csvfile = resultfile.parent / f"{resultfile.stem}.csv"

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

            # write csv file and store the name
            csvfile = self.createCSVData(csvfile=csvfile)

            om_cmd.arg_set(key="csvInput", val=csvfile.as_posix())

        return om_cmd

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

        if resultfile is None:
            # default result file generated by OM
            self.resultfile = self.tempdir / f"{self.modelName}_res.mat"
        elif os.path.exists(resultfile):
            self.resultfile = pathlib.Path(resultfile)
        else:
            self.resultfile = self.tempdir / resultfile

        om_cmd = self.simulate_cmd(resultfile=self.resultfile, simflags=simflags, simargs=simargs, timeout=timeout)

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
            result_file = self.resultfile
        else:
            result_file = pathlib.Path(resultfile)

        # check for result file exits
        if not result_file.is_file():
            raise ModelicaSystemError(f"Result file does not exist {result_file}")

        # get absolute path
        result_file = result_file.absolute()

        resultVars = self.sendExpression(f'readSimulationResultVars("{result_file.as_posix()}")')
        self.sendExpression("closeSimulationResultFile()")
        if varList is None:
            return resultVars

        if isinstance(varList, str):
            if varList not in resultVars and varList != "time":
                raise ModelicaSystemError(f"Requested data {repr(varList)} does not exist")
            res = self.sendExpression(f'readSimulationResult("{result_file.as_posix()}", {{{varList}}})')
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
            res = self.sendExpression(f'readSimulationResult("{result_file.as_posix()}",{{{variables}}})')
            npRes = np.array(res)
            self.sendExpression("closeSimulationResultFile()")
            return npRes

        raise ModelicaSystemError("Unhandled input for getSolutions()")

    @staticmethod
    def _prepare_input_data(
            raw_input: str | list[str] | dict[str, Any],
    ) -> dict[str, str]:
        """
        Convert raw input to a structured dictionary {'key1': 'value1', 'key2': 'value2'}.
        """

        def prepare_str(str_in: str) -> dict[str, str]:
            str_in = str_in.replace(" ", "")
            key_val_list: list[str] = str_in.split("=")
            if len(key_val_list) != 2:
                raise ModelicaSystemError(f"Invalid 'key=value' pair: {str_in}")

            input_data_from_str: dict[str, str] = {key_val_list[0]: key_val_list[1]}

            return input_data_from_str

        input_data: dict[str, str] = {}

        if isinstance(raw_input, str):
            warnings.warn(message="The definition of values to set should use a dictionary, "
                                  "i.e. {'key1': 'val1', 'key2': 'val2', ...}. Please convert all cases which "
                                  "use a string ('key=val') or list ['key1=val1', 'key2=val2', ...]",
                          category=DeprecationWarning,
                          stacklevel=3)
            return prepare_str(raw_input)

        if isinstance(raw_input, list):
            warnings.warn(message="The definition of values to set should use a dictionary, "
                                  "i.e. {'key1': 'val1', 'key2': 'val2', ...}. Please convert all cases which "
                                  "use a string ('key=val') or list ['key1=val1', 'key2=val2', ...]",
                          category=DeprecationWarning,
                          stacklevel=3)

            for item in raw_input:
                input_data |= prepare_str(item)

            return input_data

        if isinstance(raw_input, dict):
            for key, val in raw_input.items():
                # convert all values to strings to align it on one type: dict[str, str]
                # spaces have to be removed as setInput() could take list of tuples as input and spaces would
                str_val = str(val).replace(' ', '')
                if ' ' in key or ' ' in str_val:
                    raise ModelicaSystemError(f"Spaces not allowed in key/value pairs: {repr(key)} = {repr(val)}!")
                input_data[key] = str_val

            return input_data

        raise ModelicaSystemError(f"Invalid type of input: {type(raw_input)}")

    def _set_method_helper(
            self,
            inputdata: dict[str, str],
            classdata: dict[str, Any],
            datatype: str,
            overwritedata: Optional[dict[str, str]] = None,
    ) -> bool:
        """
        Helper function for:
        * setParameter()
        * setContinuous()
        * setSimulationOptions()
        * setLinearizationOption()
        * setOptimizationOption()
        * setInputs()

        Parameters
        ----------
        inputdata
            string or list of string given by user
        classdata
            dict() containing the values of different variables (eg: parameter, continuous, simulation parameters)
        datatype
            type identifier (eg; continuous, parameter, simulation, linearization, optimization)
        overwritedata
            dict() which stores the new override variables list,
        """

        inputdata_status: dict[str, bool] = {}
        for key, val in inputdata.items():
            if key not in classdata:
                raise ModelicaSystemError("Unhandled case in setMethodHelper.apply_single() - "
                                          f"{repr(key)} is not a {repr(datatype)} variable")

            status = False
            if datatype == "parameter" and not self.isParameterChangeable(key):
                logger.debug(f"It is not possible to set the parameter {repr(key)}. It seems to be "
                             "structural, final, protected, evaluated or has a non-constant binding. "
                             "Use sendExpression(...) and rebuild the model using buildModel() API; example: "
                             "sendExpression(\"setParameterValue("
                             f"{self.modelName}, {key}, {val if val is not None else '<?value?>'}"
                             ")\") ")
            else:
                classdata[key] = val
                if overwritedata is not None:
                    overwritedata[key] = val
                status = True

            inputdata_status[key] = status

        return all(inputdata_status.values())

    def isParameterChangeable(
            self,
            name: str,
    ) -> bool:
        q = self.getQuantities(name)
        if q[0]["changeable"] == "false":
            return False
        return True

    def setContinuous(self, cvals: str | list[str] | dict[str, Any]) -> bool:
        """
        This method is used to set continuous values. It can be called:
        with a sequence of continuous name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setContinuous("Name=value")  # depreciated
        >>> setContinuous(["Name1=value1","Name2=value2"])  # depreciated
        >>> setContinuous(cvals={"Name1": "value1", "Name2": "value2"})
        """
        inputdata = self._prepare_input_data(raw_input=cvals)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self.continuouslist,
            datatype="continuous",
            overwritedata=self.overridevariables)

    def setParameters(self, pvals: str | list[str] | dict[str, Any]) -> bool:
        """
        This method is used to set parameter values. It can be called:
        with a sequence of parameter name and assigning corresponding value as arguments as show in the example below:
        usage
        >>> setParameters("Name=value")  # depreciated
        >>> setParameters(["Name1=value1","Name2=value2"])  # depreciated
        >>> setParameters(pvals={"Name1": "value1", "Name2": "value2"})
        """
        inputdata = self._prepare_input_data(raw_input=pvals)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self.paramlist,
            datatype="parameter",
            overwritedata=self.overridevariables)

    def setSimulationOptions(self, simOptions: str | list[str] | dict[str, Any]) -> bool:
        """
        This method is used to set simulation options. It can be called:
        with a sequence of simulation options name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setSimulationOptions("Name=value")  # depreciated
        >>> setSimulationOptions(["Name1=value1","Name2=value2"])  # depreciated
        >>> setSimulationOptions(simOptions={"Name1": "value1", "Name2": "value2"})
        """
        inputdata = self._prepare_input_data(raw_input=simOptions)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self.simulateOptions,
            datatype="simulation-option",
            overwritedata=self.simoptionsoverride)

    def setLinearizationOptions(self, linearizationOptions: str | list[str] | dict[str, Any]) -> bool:
        """
        This method is used to set linearization options. It can be called:
        with a sequence of linearization options name and assigning corresponding value as arguments as show in the example below
        usage
        >>> setLinearizationOptions("Name=value")  # depreciated
        >>> setLinearizationOptions(["Name1=value1","Name2=value2"])  # depreciated
        >>> setLinearizationOptions(linearizationOtions={"Name1": "value1", "Name2": "value2"})
        """
        inputdata = self._prepare_input_data(raw_input=linearizationOptions)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self.linearOptions,
            datatype="Linearization-option",
            overwritedata=None)

    def setOptimizationOptions(self, optimizationOptions: str | list[str] | dict[str, Any]) -> bool:
        """
        This method is used to set optimization options. It can be called:
        with a sequence of optimization options name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setOptimizationOptions("Name=value")  # depreciated
        >>> setOptimizationOptions(["Name1=value1","Name2=value2"])  # depreciated
        >>> setOptimizationOptions(optimizationOptions={"Name1": "value1", "Name2": "value2"})
        """
        inputdata = self._prepare_input_data(raw_input=optimizationOptions)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self.optimizeOptions,
            datatype="optimization-option",
            overwritedata=None)

    def setInputs(self, name: str | list[str] | dict[str, Any]) -> bool:
        """
        This method is used to set input values. It can be called with a sequence of input name and assigning
        corresponding values as arguments as show in the example below. Compared to other set*() methods this is a
        special case as value could be a list of tuples - these are converted to a string in _prepare_input_data()
        and restored here via ast.literal_eval().

        >>> setInputs("Name=value")  # depreciated
        >>> setInputs(["Name1=value1","Name2=value2"])  # depreciated
        >>> setInputs(name={"Name1": "value1", "Name2": "value2"})
        """
        inputdata = self._prepare_input_data(raw_input=name)

        for key, val in inputdata.items():
            if key in self.inputlist:
                if not isinstance(val, str):
                    raise ModelicaSystemError(f"Invalid data in input for {repr(key)}: {repr(val)}")

                val_evaluated = ast.literal_eval(val)

                if isinstance(val_evaluated, (int, float)):
                    self.inputlist[key] = [(float(self.simulateOptions["startTime"]), float(val)),
                                           (float(self.simulateOptions["stopTime"]), float(val))]
                elif isinstance(val_evaluated, list):
                    if not all([isinstance(item, tuple) for item in val_evaluated]):
                        raise ModelicaSystemError("Value for setInput() must be in tuple format; "
                                                  f"got {repr(val_evaluated)}")
                    if val_evaluated != sorted(val_evaluated, key=lambda x: x[0]):
                        raise ModelicaSystemError("Time value should be in increasing order; "
                                                  f"got {repr(val_evaluated)}")

                    for item in val_evaluated:
                        if item[0] < float(self.simulateOptions["startTime"]):
                            raise ModelicaSystemError(f"Time value in {repr(item)} of {repr(val_evaluated)} is less "
                                                      "than the simulation start time")
                        if len(item) != 2:
                            raise ModelicaSystemError(f"Value {repr(item)} of {repr(val_evaluated)} "
                                                      "is in incorrect format!")

                    self.inputlist[key] = val_evaluated
                self.inputFlag = True
            else:
                raise ModelicaSystemError(f"{key} is not an input")

        return True

    def createCSVData(self, csvfile: Optional[pathlib.Path] = None) -> pathlib.Path:
        """
        Create a csv file with inputs for the simulation/optimization of the model. If csvfile is provided as argument,
        this file is used; else a generic file name is created.
        """
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

        if csvfile is None:
            csvfile = self.tempdir / f'{self.modelName}.csv'

        with open(file=csvfile, mode="w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerows(csv_rows)

        return csvfile

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
            raise ModelicaSystemError(
                "Linearization cannot be performed as the model is not build, "
                "use ModelicaSystem() to build the model first"
            )

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
            csvfile = self.createCSVData()
            om_cmd.arg_set(key="csvInput", val=csvfile.as_posix())

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


class ModelicaSystemDoE:
    """
    Class to run DoEs based on a (Open)Modelica model using ModelicaSystem
    """

    DF_COLUMNS_RESULTFILENAME: str = 'resultfilename'
    DF_COLUMNS_RESULTS_AVAILABLE: str = 'results available'

    def __init__(
            self,
            fileName: Optional[str | os.PathLike | pathlib.Path] = None,
            modelName: Optional[str] = None,
            lmodel: Optional[list[str | tuple[str, str]]] = None,
            commandLineOptions: Optional[str] = None,
            variableFilter: Optional[str] = None,
            customBuildDirectory: Optional[str | os.PathLike | pathlib.Path] = None,
            omhome: Optional[str] = None,

            simargs: Optional[dict[str, Optional[str | dict[str, str]]]] = None,
            timeout: Optional[int] = None,

            resultpath: Optional[pathlib.Path] = None,
            parameters: Optional[dict[str, list[str] | list[int] | list[float]]] = None,
    ) -> None:
        """
        Initialisation of ModelicaSystemDoE. The parameters are based on: ModelicaSystem.__init__() and
        ModelicaSystem.simulate(). Additionally, the path to store the result files is needed (= resultpath) as well as
        a list of parameters to vary for the Doe (= parameters). All possible combinations are considered.
        """
        self._lmodel = lmodel
        self._modelName = modelName
        self._fileName = fileName

        self._CommandLineOptions = commandLineOptions
        self._variableFilter = variableFilter
        self._customBuildDirectory = customBuildDirectory
        self._omhome = omhome

        # reference for the model; not used for any simulations but to evaluate parameters, etc.
        self._mod = ModelicaSystem(
            fileName=self._fileName,
            modelName=self._modelName,
            lmodel=self._lmodel,
            commandLineOptions=self._CommandLineOptions,
            variableFilter=self._variableFilter,
            customBuildDirectory=self._customBuildDirectory,
            omhome=self._omhome,
        )

        self._simargs = simargs
        self._timeout = timeout

        if isinstance(resultpath, pathlib.Path):
            self._resultpath = resultpath
        else:
            self._resultpath = pathlib.Path('.')

        if isinstance(parameters, dict):
            self._parameters = parameters
        else:
            self._parameters = {}

        self._sim_df: Optional[pd.DataFrame] = None
        self._sim_task_query: queue.Queue = queue.Queue()

    def prepare(self) -> int:
        """
        Prepare the DoE by evaluating the parameters. Each structural parameter requires a new instance of
        ModelicaSystem while the non-structural parameters can just be set on the executable.

        The return value is the number of simulation defined.
        """

        param_structure = {}
        param_simple = {}
        for param_name in self._parameters.keys():
            changeable = self._mod.isParameterChangeable(name=param_name)
            logger.info(f"Parameter {repr(param_name)} is changeable? {changeable}")

            if changeable:
                param_simple[param_name] = self._parameters[param_name]
            else:
                param_structure[param_name] = self._parameters[param_name]

        param_structure_combinations = list(itertools.product(*param_structure.values()))
        param_simple_combinations = list(itertools.product(*param_simple.values()))

        df_entries: list[pd.DataFrame] = []
        for idx_pc_structure, pc_structure in enumerate(param_structure_combinations):
            mod_structure = ModelicaSystem(
                fileName=self._fileName,
                modelName=self._modelName,
                lmodel=self._lmodel,
                commandLineOptions=self._CommandLineOptions,
                variableFilter=self._variableFilter,
                customBuildDirectory=self._customBuildDirectory,
                omhome=self._omhome,
            )

            sim_args_structure = {}
            for idx_structure, pk_structure in enumerate(param_structure.keys()):
                sim_args_structure[pk_structure] = pc_structure[idx_structure]

                pk_value = pc_structure[idx_structure]
                if isinstance(pk_value, str):
                    expression = f"setParameterValue({self._modelName}, {pk_structure}, $Code(=\"{pk_value}\"))"
                elif isinstance(pk_value, bool):
                    pk_value_bool_str = "true" if pk_value else "false"
                    expression = f"setParameterValue({self._modelName}, {pk_structure}, $Code(={pk_value_bool_str}));"
                else:
                    expression = f"setParameterValue({self._modelName}, {pk_structure}, {pk_value})"
                mod_structure.sendExpression(expression)

            for idx_pc_simple, pc_simple in enumerate(param_simple_combinations):
                sim_args_simple = {}
                for idx_simple, pk_simple in enumerate(param_simple.keys()):
                    sim_args_simple[pk_simple] = str(pc_simple[idx_simple])

                resfilename = f"DOE_{idx_pc_structure:09d}_{idx_pc_simple:09d}.mat"
                logger.info(f"use result file {repr(resfilename)} "
                            f"for structural parameters: {sim_args_structure} "
                            f"and simple parameters: {sim_args_simple}")
                resultfile = self._resultpath / resfilename

                df_data = (
                        {
                            'ID structure': idx_pc_structure,
                            'ID simple': idx_pc_simple,
                            self.DF_COLUMNS_RESULTFILENAME: resfilename,
                            'structural parameters ID': idx_pc_structure,
                        }
                        | sim_args_structure
                        | {
                            'non-structural parameters ID': idx_pc_simple,
                        }
                        | sim_args_simple
                        | {
                            self.DF_COLUMNS_RESULTS_AVAILABLE: False,
                        }
                )

                df_entries.append(pd.DataFrame.from_dict(df_data))

                cmd = mod_structure.simulate_cmd(
                    resultfile=resultfile.absolute().resolve(),
                    simargs={"override": sim_args_simple},
                )

                self._sim_task_query.put(cmd)

        self._sim_df = pd.concat(df_entries, ignore_index=True)

        logger.info(f"Prepared {self._sim_df.shape[0]} simulation definitions for the defined DoE.")

        return self._sim_df.shape[0]

    def get_doe(self) -> Optional[pd.DataFrame]:
        """
        Get the defined Doe as a poandas dataframe.
        """
        return self._sim_df

    def simulate(self, num_workers: int = 3) -> None:
        """
        Simulate the DoE using the defined number of workers.

        Returns True if all simulations were done successfully, else False.
        """

        sim_count_total = self._sim_task_query.qsize()

        def worker(worker_id, task_queue):
            while True:
                sim_data = {}
                try:
                    # Get the next task from the queue
                    cmd: ModelicaSystemCmd = task_queue.get(block=False)
                except queue.Empty:
                    logger.info(f"[Worker {worker_id}] No more simulations to run.")
                    break

                resultfile = cmd.arg_get(key='r')
                resultpath = pathlib.Path(resultfile)

                logger.info(f"[Worker {worker_id}] Performing task: {resultpath.name}")

                try:
                    sim_data['sim'].run()
                except ModelicaSystemError as ex:
                    logger.warning(f"Simulation error for {resultpath.name}: {ex}")

                # Mark the task as done
                task_queue.task_done()

                sim_count_done = sim_count_total - self._sim_task_query.qsize()
                logger.info(f"[Worker {worker_id}] Task completed: {resultpath.name} "
                            f"({sim_count_done}/{sim_count_total} = "
                            f"{sim_count_done / sim_count_total * 100:.2f}% of tasks left)")

        logger.info(f"Start simulations for DoE with {sim_count_total} simulations "
                    f"using {num_workers} workers ...")

        # Create and start worker threads
        threads = []
        for i in range(num_workers):
            thread = threading.Thread(target=worker, args=(i, self._sim_task_query))
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        for idx, row in self._sim_df.to_dict('index').items():
            resultfilename = row[self.DF_COLUMNS_RESULTFILENAME]
            resultfile = self._resultpath / resultfilename

            if resultfile.exists():
                mask = self._sim_df[self.DF_COLUMNS_RESULTFILENAME] == resultfilename
                self._sim_df.loc[mask, self.DF_COLUMNS_RESULTS_AVAILABLE] = True

        sim_done = self._sim_df[self.DF_COLUMNS_RESULTS_AVAILABLE].sum()
        sim_total = self._sim_df.shape[0]
        logger.info(f"All workers finished ({sim_done} of {sim_total} simulations with a result file).")

    def get_solutions(
            self,
            var_list: Optional[list] = None,
    ) -> Optional[tuple[str] | dict[str, pd.DataFrame | str]]:
        """
        Get all solutions of the DoE run. The following return values are possible:

        * None, if there no simulation was run

        * A list of variables if val_list == None

        * The Solutions as dict[str, pd.DataFrame] if a value list (== val_list) is defined.
        """
        if self._sim_df is None:
            return None

        if self._sim_df.shape[0] == 0 or self._sim_df[self.DF_COLUMNS_RESULTS_AVAILABLE].sum() == 0:
            raise ModelicaSystemError("No result files available - all simulations did fail?")

        if var_list is None:
            resultfilename = self._sim_df[self.DF_COLUMNS_RESULTFILENAME].values[0]
            resultfile = self._resultpath / resultfilename
            return self._mod.getSolutions(resultfile=resultfile)

        sol_dict: dict[str, pd.DataFrame | str] = {}
        for row in self._sim_df.to_dict('records'):
            resultfilename = row[self.DF_COLUMNS_RESULTFILENAME]
            resultfile = self._resultpath / resultfilename

            try:
                sol = self._mod.getSolutions(varList=var_list, resultfile=resultfile)
                sol_data = {var: sol[idx] for idx, var in var_list}
                sol_df = pd.DataFrame(sol_data)
                sol_dict[resultfilename] = sol_df
            except ModelicaSystemError as ex:
                logger.warning(f"No solution for {resultfilename}: {ex}")
                sol_dict[resultfilename] = str(ex)

        return sol_dict
