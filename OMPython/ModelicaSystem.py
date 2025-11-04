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
from dataclasses import dataclass
import itertools
import logging
import numbers
import numpy as np
import os
import queue
import textwrap
import threading
from typing import Any, cast, Optional
import warnings
import xml.etree.ElementTree as ET

from OMPython.OMCSession import (OMCSessionException, OMCSessionRunData, OMCSessionZMQ,
                                 OMCProcess, OMCProcessLocal, OMCPath)

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
    """A compiled model executable."""

    def __init__(
            self,
            session: OMCSessionZMQ,
            runpath: OMCPath,
            modelname: str,
            timeout: Optional[float] = None,
    ) -> None:
        self._session = session
        self._runpath = runpath
        self._model_name = modelname
        self._timeout = timeout

        # dictionaries of command line arguments for the model executable
        self._args: dict[str, str | None] = {}
        # 'override' argument needs special handling, as it is a dict on its own saved as dict elements following the
        # structure: 'key' => 'key=value'
        self._arg_override: dict[str, str] = {}

    def arg_set(
            self,
            key: str,
            val: Optional[str | dict[str, Any] | numbers.Number] = None,
    ) -> None:
        """
        Set one argument for the executable model.

        Args:
            key: identifier / argument name to be used for the call of the model executable.
            val: value for the given key; None for no value and for key == 'override' a dictionary can be used which
              indicates variables to override
        """

        def override2str(
                okey: str,
                oval: str | bool | numbers.Number,
        ) -> str:
            """
            Convert a value for 'override' to a string taking into account differences between Modelica and Python.
            """
            # check oval for any string representations of numbers (or bool) and convert these to Python representations
            if isinstance(oval, str):
                try:
                    oval_evaluated = ast.literal_eval(oval)
                    if isinstance(oval_evaluated, (numbers.Number, bool)):
                        oval = oval_evaluated
                except (ValueError, SyntaxError):
                    pass

            if isinstance(oval, str):
                oval_str = oval.strip()
            elif isinstance(oval, bool):
                oval_str = 'true' if oval else 'false'
            elif isinstance(oval, numbers.Number):
                oval_str = str(oval)
            else:
                raise ModelicaSystemError(f"Invalid value for override key {okey}: {type(oval)}")

            return f"{okey}={oval_str}"

        if not isinstance(key, str):
            raise ModelicaSystemError(f"Invalid argument key: {repr(key)} (type: {type(key)})")
        key = key.strip()

        if isinstance(val, dict):
            if key != 'override':
                raise ModelicaSystemError("Dictionary input only possible for key 'override'!")

            for okey, oval in val.items():
                if not isinstance(okey, str):
                    raise ModelicaSystemError("Invalid key for argument 'override': "
                                              f"{repr(okey)} (type: {type(okey)})")

                if not isinstance(oval, (str, bool, numbers.Number, type(None))):
                    raise ModelicaSystemError(f"Invalid input for 'override'.{repr(okey)}: "
                                              f"{repr(oval)} (type: {type(oval)})")

                if okey in self._arg_override:
                    if oval is None:
                        logger.info(f"Remove model executable override argument: {repr(self._arg_override[okey])}")
                        del self._arg_override[okey]
                        continue

                    logger.info(f"Update model executable override argument: {repr(okey)} = {repr(oval)} "
                                f"(was: {repr(self._arg_override[okey])})")

                if oval is not None:
                    self._arg_override[okey] = override2str(okey=okey, oval=oval)

            argval = ','.join(sorted(self._arg_override.values()))
        elif val is None:
            argval = None
        elif isinstance(val, str):
            argval = val.strip()
        elif isinstance(val, numbers.Number):
            argval = str(val)
        else:
            raise ModelicaSystemError(f"Invalid argument value for {repr(key)}: {repr(val)} (type: {type(val)})")

        if key in self._args:
            logger.warning(f"Override model executable argument: {repr(key)} = {repr(argval)} "
                           f"(was: {repr(self._args[key])})")
        self._args[key] = argval

    def arg_get(self, key: str) -> Optional[str | dict[str, str | bool | numbers.Number]]:
        """
        Return the value for the given key
        """
        if key in self._args:
            return self._args[key]

        return None

    def args_set(
            self,
            args: dict[str, Optional[str | dict[str, Any] | numbers.Number]],
    ) -> None:
        """
        Define arguments for the model executable.
        """
        for arg in args:
            self.arg_set(key=arg, val=args[arg])

    def get_cmd_args(self) -> list[str]:
        """
        Get a list with the command arguments for the model executable.
        """

        cmdl = []
        for key in sorted(self._args):
            if self._args[key] is None:
                cmdl.append(f"-{key}")
            else:
                cmdl.append(f"-{key}={self._args[key]}")

        return cmdl

    def definition(self) -> OMCSessionRunData:
        """
        Define all needed data to run the model executable. The data is stored in an OMCSessionRunData object.
        """
        # ensure that a result filename is provided
        result_file = self.arg_get('r')
        if not isinstance(result_file, str):
            result_file = (self._runpath / f"{self._model_name}.mat").as_posix()

        omc_run_data = OMCSessionRunData(
            cmd_path=self._runpath.as_posix(),
            cmd_model_name=self._model_name,
            cmd_args=self.get_cmd_args(),
            cmd_result_path=result_file,
            cmd_timeout=self._timeout,
        )

        omc_run_data_updated = self._session.omc_run_data_update(
            omc_run_data=omc_run_data,
        )

        return omc_run_data_updated

    @staticmethod
    def parse_simflags(simflags: str) -> dict[str, Optional[str | dict[str, Any] | numbers.Number]]:
        """
        Parse a simflag definition; this is deprecated!

        The return data can be used as input for self.args_set().
        """
        warnings.warn("The argument 'simflags' is depreciated and will be removed in future versions; "
                      "please use 'simargs' instead", DeprecationWarning, stacklevel=2)

        simargs: dict[str, Optional[str | dict[str, Any] | numbers.Number]] = {}

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
            fileName: Optional[str | os.PathLike] = None,
            modelName: Optional[str] = None,
            lmodel: Optional[list[str | tuple[str, str]]] = None,
            commandLineOptions: Optional[list[str]] = None,
            variableFilter: Optional[str] = None,
            customBuildDirectory: Optional[str | os.PathLike] = None,
            omhome: Optional[str] = None,
            omc_process: Optional[OMCProcess] = None,
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
            commandLineOptions: List with extra command line options as elements. The list elements are
              provided to omc via setCommandLineOptions(). If set, the default values will be overridden.
              To disable any command line options, use an empty list.
            variableFilter: A regular expression. Only variables fully
              matching the regexp will be stored in the result file.
              Leaving it unspecified is equivalent to ".*".
            customBuildDirectory: Path to a directory to be used for temporary
              files like the model executable. If left unspecified, a tmp
              directory will be created.
            omhome: OPENMODELICAHOME value to be used when creating the OMC
              session.
            omc_process: definition of a (local) OMC process to be used. If
              unspecified, a new local session will be created.
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

        self._quantities: list[dict[str, Any]] = []
        self._params: dict[str, str] = {}  # even numerical values are stored as str
        self._inputs: dict[str, list | None] = {}
        # _outputs values are str before simulate(), but they can be
        # np.float64 after simulate().
        self._outputs: dict[str, Any] = {}
        # same for _continuous
        self._continuous: dict[str, Any] = {}
        self._simulate_options: dict[str, str] = {}
        self._override_variables: dict[str, str] = {}
        self._simulate_options_override: dict[str, str] = {}
        self._linearization_options = {'startTime': 0.0, 'stopTime': 1.0, 'stepSize': 0.002, 'tolerance': 1e-8}
        self._optimization_options = self._linearization_options | {'numberOfIntervals': 500}
        self._linearized_inputs: list[str] = []  # linearization input list
        self._linearized_outputs: list[str] = []  # linearization output list
        self._linearized_states: list[str] = []  # linearization states list

        if omc_process is not None:
            self._getconn = OMCSessionZMQ(omc_process=omc_process)
        else:
            self._getconn = OMCSessionZMQ(omhome=omhome)

        # set commandLineOptions using default values or the user defined list
        if commandLineOptions is None:
            # set default command line options to improve the performance of linearization and to avoid recompilation if
            # the simulation executable is reused in linearize() via the runtime flag '-l'
            commandLineOptions = [
                "--linearizationDumpLanguage=python",
                "--generateSymbolicLinearization",
            ]
        for opt in commandLineOptions:
            self.setCommandLineOptions(commandLineOptions=opt)

        if lmodel is None:
            lmodel = []

        if not isinstance(lmodel, list):
            raise ModelicaSystemError(f"Invalid input type for lmodel: {type(lmodel)} - list expected!")

        self._lmodel = lmodel  # may be needed if model is derived from other model
        self._model_name = modelName  # Model class name
        if fileName is not None:
            file_name = self._getconn.omcpath(fileName).resolve()
        else:
            file_name = None
        self._file_name: Optional[OMCPath] = file_name  # Model file/package name
        self._simulated = False  # True if the model has already been simulated
        self._result_file: Optional[OMCPath] = None  # for storing result file
        self._variable_filter = variableFilter

        if self._file_name is not None and not self._file_name.is_file():  # if file does not exist
            raise IOError(f"{self._file_name} does not exist!")

        # set default command Line Options for linearization as
        # linearize() will use the simulation executable and runtime
        # flag -l to perform linearization
        self.setCommandLineOptions("--linearizationDumpLanguage=python")
        self.setCommandLineOptions("--generateSymbolicLinearization")

        self._work_dir: OMCPath = self.setWorkDirectory(customBuildDirectory)

        if self._file_name is not None:
            self._loadLibrary(lmodel=self._lmodel)
            self._loadFile(fileName=self._file_name)

        # allow directly loading models from MSL without fileName
        elif fileName is None and modelName is not None:
            self._loadLibrary(lmodel=self._lmodel)

        if build:
            self.buildModel(variableFilter)

    def session(self) -> OMCSessionZMQ:
        """
        Return the OMC session used for this class.
        """
        return self._getconn

    def setCommandLineOptions(self, commandLineOptions: str):
        """
        Set the provided command line option via OMC setCommandLineOptions().
        """
        exp = f'setCommandLineOptions("{commandLineOptions}")'
        self.sendExpression(exp)

    def _loadFile(self, fileName: OMCPath):
        # load file
        self.sendExpression(f'loadFile("{fileName.as_posix()}")')

    # for loading file/package, loading model and building model
    def _loadLibrary(self, lmodel: list):
        # load Modelica standard libraries or Modelica files if needed
        for element in lmodel:
            if element is not None:
                if isinstance(element, str):
                    if element.endswith(".mo"):
                        apiCall = "loadFile"
                    else:
                        apiCall = "loadModel"
                    self._requestApi(apiName=apiCall, entity=element)
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

    def setWorkDirectory(self, customBuildDirectory: Optional[str | os.PathLike] = None) -> OMCPath:
        """
        Define the work directory for the ModelicaSystem / OpenModelica session. The model is build within this
        directory. If no directory is defined a unique temporary directory is created.
        """
        if customBuildDirectory is not None:
            workdir = self._getconn.omcpath(customBuildDirectory).absolute()
            if not workdir.is_dir():
                raise IOError(f"Provided work directory does not exists: {customBuildDirectory}!")
        else:
            workdir = self._getconn.omcpath_tempdir().absolute()
            if not workdir.is_dir():
                raise IOError(f"{workdir} could not be created")

        logger.info("Define work dir as %s", workdir)
        exp = f'cd("{workdir.as_posix()}")'
        self.sendExpression(exp)

        # set the class variable _work_dir ...
        self._work_dir = workdir
        # ... and also return the defined path
        return workdir

    def getWorkDirectory(self) -> OMCPath:
        """
        Return the defined working directory for this ModelicaSystem / OpenModelica session.
        """
        return self._work_dir

    def buildModel(self, variableFilter: Optional[str] = None):
        filter_def: Optional[str] = None
        if variableFilter is not None:
            filter_def = variableFilter
        elif self._variable_filter is not None:
            filter_def = self._variable_filter

        if filter_def is not None:
            var_filter = f'variableFilter="{filter_def}"'
        else:
            var_filter = 'variableFilter=".*"'

        buildModelResult = self._requestApi(apiName="buildModel", entity=self._model_name, properties=var_filter)
        logger.debug("OM model build result: %s", buildModelResult)

        # check if the executable exists ...
        om_cmd = ModelicaSystemCmd(
            session=self._getconn,
            runpath=self.getWorkDirectory(),
            modelname=self._model_name,
            timeout=5.0,
        )
        # ... by running it - output help for command help
        om_cmd.arg_set(key="help", val="help")
        cmd_definition = om_cmd.definition()
        returncode = self._getconn.run_model_executable(cmd_run_data=cmd_definition)
        if returncode != 0:
            raise ModelicaSystemError("Model executable not working!")

        xml_file = self._getconn.omcpath(buildModelResult[0]).parent / buildModelResult[1]
        self._xmlparse(xml_file=xml_file)

    def sendExpression(self, expr: str, parsed: bool = True) -> Any:
        try:
            retval = self._getconn.sendExpression(expr, parsed)
        except OMCSessionException as ex:
            raise ModelicaSystemError(f"Error executing {repr(expr)}") from ex

        logger.debug(f"Result of executing {repr(expr)}: {textwrap.shorten(repr(retval), width=100)}")

        return retval

    # request to OMC
    def _requestApi(
            self,
            apiName: str,
            entity: Optional[str] = None,
            properties: Optional[str] = None,
    ) -> Any:
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

    def _xmlparse(self, xml_file: OMCPath):
        if not xml_file.is_file():
            raise ModelicaSystemError(f"XML file not generated: {xml_file}")

        xml_content = xml_file.read_text()
        tree = ET.ElementTree(ET.fromstring(xml_content))
        rootCQ = tree.getroot()
        for attr in rootCQ.iter('DefaultExperiment'):
            for key in ("startTime", "stopTime", "stepSize", "tolerance",
                        "solver", "outputFormat"):
                self._simulate_options[key] = str(attr.get(key))

        for sv in rootCQ.iter('ScalarVariable'):
            translations = {
                "alias": "alias",
                "aliasvariable": "aliasVariable",
                "causality": "causality",
                "changeable": "isValueChangeable",
                "description": "description",
                "name": "name",
                "variability": "variability",
            }

            scalar: dict[str, Any] = {}
            for key_dst, key_src in translations.items():
                val = sv.get(key_src)
                scalar[key_dst] = None if val is None else str(val)

            ch = list(sv)
            for att in ch:
                scalar["start"] = att.get('start')
                scalar["min"] = att.get('min')
                scalar["max"] = att.get('max')
                scalar["unit"] = att.get('unit')

            # save parameters in the corresponding class variables
            if scalar["variability"] == "parameter":
                if scalar["name"] in self._override_variables:
                    self._params[scalar["name"]] = self._override_variables[scalar["name"]]
                else:
                    self._params[scalar["name"]] = scalar["start"]
            if scalar["variability"] == "continuous":
                self._continuous[scalar["name"]] = scalar["start"]
            if scalar["causality"] == "input":
                self._inputs[scalar["name"]] = scalar["start"]
            if scalar["causality"] == "output":
                self._outputs[scalar["name"]] = scalar["start"]

            self._quantities.append(scalar)

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
            return self._quantities

        if isinstance(names, str):
            r = [x for x in self._quantities if x["name"] == names]
            if r == []:
                raise KeyError(names)
            return r

        if isinstance(names, list):
            return [x for y in names for x in self._quantities if x["name"] == y]

        raise ModelicaSystemError("Unhandled input for getQuantities()")

    def getContinuous(self, names: Optional[str | list[str]] = None):
        """Get values of continuous signals.

        If called before simulate(), the initial values are returned as
        strings (or None). If called after simulate(), the final values (at
        stopTime) are returned as numpy.float64.

        Args:
            names: Either None (default), a string with the continuous signal
              name, or a list of signal name strings.
        Returns:
            If `names` is None, a dict in the format
            {signal_name: signal_value} is returned.
            If `names` is a string, a single element list [signal_value] is
            returned.
            If `names` is a list, a list with one value for each signal name
            in names is returned: [signal1_value, signal2_value, ...].

        Examples:
            Before simulate():
            >>> mod.getContinuous()
            {'x': '1.0', 'der(x)': None, 'y': '-0.4'}
            >>> mod.getContinuous("y")
            ['-0.4']
            >>> mod.getContinuous(["y","x"])
            ['-0.4', '1.0']

            After simulate():
            >>> mod.getContinuous()
            {'x': np.float64(0.68), 'der(x)': np.float64(-0.24), 'y': np.float64(-0.24)}
            >>> mod.getContinuous("x")
            [np.float64(0.68)]
            >>> mod.getOutputs(["y","x"])
            [np.float64(-0.24), np.float64(0.68)]
        """
        if not self._simulated:
            if names is None:
                return self._continuous
            if isinstance(names, str):
                return [self._continuous[names]]
            if isinstance(names, list):
                return [self._continuous[x] for x in names]

        if names is None:
            for name in self._continuous:
                try:
                    value = self.getSolutions(name)
                    self._continuous[name] = value[0][-1]
                except (OMCSessionException, ModelicaSystemError) as ex:
                    raise ModelicaSystemError(f"{name} could not be computed") from ex
            return self._continuous

        if isinstance(names, str):
            if names in self._continuous:
                value = self.getSolutions(names)
                self._continuous[names] = value[0][-1]
                return [self._continuous[names]]
            raise ModelicaSystemError(f"{names} is not continuous")

        if isinstance(names, list):
            valuelist = []
            for name in names:
                if name in self._continuous:
                    value = self.getSolutions(name)
                    self._continuous[name] = value[0][-1]
                    valuelist.append(value[0][-1])
                else:
                    raise ModelicaSystemError(f"{name} is not continuous")
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
            return self._params
        if isinstance(names, str):
            return [self._params[names]]
        if isinstance(names, list):
            return [self._params[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getParameters()")

    def getInputs(self, names: Optional[str | list[str]] = None) -> dict | list:  # 6
        """Get values of input signals.

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
            return self._inputs
        if isinstance(names, str):
            return [self._inputs[names]]
        if isinstance(names, list):
            return [self._inputs[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getInputs()")

    def getOutputs(self, names: Optional[str | list[str]] = None):  # 7
        """Get values of output signals.

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
        if not self._simulated:
            if names is None:
                return self._outputs
            if isinstance(names, str):
                return [self._outputs[names]]
            return [self._outputs[x] for x in names]

        if names is None:
            for name in self._outputs:
                value = self.getSolutions(name)
                self._outputs[name] = value[0][-1]
            return self._outputs

        if isinstance(names, str):
            if names in self._outputs:
                value = self.getSolutions(names)
                self._outputs[names] = value[0][-1]
                return [self._outputs[names]]
            raise KeyError(names)

        if isinstance(names, list):
            valuelist = []
            for name in names:
                if name in self._outputs:
                    value = self.getSolutions(name)
                    self._outputs[name] = value[0][-1]
                    valuelist.append(value[0][-1])
                else:
                    raise KeyError(name)
            return valuelist

        raise ModelicaSystemError("Unhandled input for getOutputs()")

    def getSimulationOptions(self, names: Optional[str | list[str]] = None) -> dict[str, str] | list[str]:
        """Get simulation options such as stopTime and tolerance.

        Args:
            names: Either None (default), a string with the simulation option
              name, or a list of option name strings.

        Returns:
            If `names` is None, a dict in the format
            {option_name: option_value} is returned.
            If `names` is a string, a single element list [option_value] is
            returned.
            If `names` is a list, a list with one value for each option name
            in names is returned: [option1_value, option2_value, ...].
            Option values are always returned as strings.

        Examples:
            >>> mod.getSimulationOptions()
            {'startTime': '0', 'stopTime': '1.234',
             'stepSize': '0.002', 'tolerance': '1.1e-08', 'solver': 'dassl', 'outputFormat': 'mat'}
            >>> mod.getSimulationOptions("stopTime")
            ['1.234']
            >>> mod.getSimulationOptions(["tolerance", "stopTime"])
            ['1.1e-08', '1.234']
        """
        if names is None:
            return self._simulate_options
        if isinstance(names, str):
            return [self._simulate_options[names]]
        if isinstance(names, list):
            return [self._simulate_options[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getSimulationOptions()")

    def getLinearizationOptions(self, names: Optional[str | list[str]] = None) -> dict | list:
        """Get simulation options used for linearization.

        Args:
            names: Either None (default), a string with the linearization option
              name, or a list of option name strings.

        Returns:
            If `names` is None, a dict in the format
            {option_name: option_value} is returned.
            If `names` is a string, a single element list [option_value] is
            returned.
            If `names` is a list, a list with one value for each option name
            in names is returned: [option1_value, option2_value, ...].
            Some option values are returned as float when first initialized,
            but always as strings after setLinearizationOptions is used to
            change them.

        Examples:
            >>> mod.getLinearizationOptions()
            {'startTime': 0.0, 'stopTime': 1.0, 'stepSize': 0.002, 'tolerance': 1e-08}
            >>> mod.getLinearizationOptions("stopTime")
            [1.0]
            >>> mod.getLinearizationOptions(["tolerance", "stopTime"])
            [1e-08, 1.0]
        """
        if names is None:
            return self._linearization_options
        if isinstance(names, str):
            return [self._linearization_options[names]]
        if isinstance(names, list):
            return [self._linearization_options[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getLinearizationOptions()")

    def getOptimizationOptions(self, names: Optional[str | list[str]] = None) -> dict | list:
        """Get simulation options used for optimization.

        Args:
            names: Either None (default), a string with the optimization option
              name, or a list of option name strings.

        Returns:
            If `names` is None, a dict in the format
            {option_name: option_value} is returned.
            If `names` is a string, a single element list [option_value] is
            returned.
            If `names` is a list, a list with one value for each option name
            in names is returned: [option1_value, option2_value, ...].
            Some option values are returned as float when first initialized,
            but always as strings after setOptimizationOptions is used to
            change them.

        Examples:
            >>> mod.getOptimizationOptions()
            {'startTime': 0.0, 'stopTime': 1.0, 'numberOfIntervals': 500, 'stepSize': 0.002, 'tolerance': 1e-08}
            >>> mod.getOptimizationOptions("stopTime")
            [1.0]
            >>> mod.getOptimizationOptions(["tolerance", "stopTime"])
            [1e-08, 1.0]
        """
        if names is None:
            return self._optimization_options
        if isinstance(names, str):
            return [self._optimization_options[names]]
        if isinstance(names, list):
            return [self._optimization_options[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getOptimizationOptions()")

    def simulate_cmd(
            self,
            result_file: OMCPath,
            simflags: Optional[str] = None,
            simargs: Optional[dict[str, Optional[str | dict[str, Any] | numbers.Number]]] = None,
            timeout: Optional[float] = None,
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
        result_file
        simflags
        simargs
        timeout

        Returns
        -------
            An instance if ModelicaSystemCmd to run the requested simulation.
        """

        om_cmd = ModelicaSystemCmd(
            session=self._getconn,
            runpath=self.getWorkDirectory(),
            modelname=self._model_name,
            timeout=timeout,
        )

        # always define the result file to use
        om_cmd.arg_set(key="r", val=result_file.as_posix())

        # allow runtime simulation flags from user input
        if simflags is not None:
            om_cmd.args_set(args=om_cmd.parse_simflags(simflags=simflags))

        if simargs:
            om_cmd.args_set(args=simargs)

        if self._override_variables or self._simulate_options_override:
            override_file = result_file.parent / f"{result_file.stem}_override.txt"

            override_content = (
                    "\n".join([f"{key}={value}" for key, value in self._override_variables.items()])
                    + "\n".join([f"{key}={value}" for key, value in self._simulate_options_override.items()])
                    + "\n"
            )

            override_file.write_text(override_content)
            om_cmd.arg_set(key="overrideFile", val=override_file.as_posix())

        if self._inputs:  # if model has input quantities
            for key, val in self._inputs.items():
                if val is None:
                    val = [(float(self._simulate_options["startTime"]), 0.0),
                           (float(self._simulate_options["stopTime"]), 0.0)]
                    self._inputs[key] = val
                if float(self._simulate_options["startTime"]) != val[0][0]:
                    raise ModelicaSystemError(f"startTime not matched for Input {key}!")
                if float(self._simulate_options["stopTime"]) != val[-1][0]:
                    raise ModelicaSystemError(f"stopTime not matched for Input {key}!")

            # csvfile is based on name used for result file
            csvfile = result_file.parent / f"{result_file.stem}.csv"
            # write csv file and store the name
            csvfile = self._createCSVData(csvfile=csvfile)

            om_cmd.arg_set(key="csvInput", val=csvfile.as_posix())

        return om_cmd

    def simulate(
            self,
            resultfile: Optional[str] = None,
            simflags: Optional[str] = None,
            simargs: Optional[dict[str, Optional[str | dict[str, Any] | numbers.Number]]] = None,
            timeout: Optional[float] = None,
    ) -> None:
        """Simulate the model according to simulation options.

        See setSimulationOptions().

        Args:
            resultfile: Path to a custom result file
            simflags: String of extra command line flags for the model binary.
              This argument is deprecated, use simargs instead.
            simargs: Dict with simulation runtime flags.
            timeout: Maximum execution time in seconds.

        Examples:
            mod.simulate()
            mod.simulate(resultfile="a.mat")
            # set runtime simulation flags, deprecated
            mod.simulate(simflags="-noEventEmit -noRestart -override=e=0.3,g=10")
            # using simargs
            mod.simulate(simargs={"noEventEmit": None, "noRestart": None, "override": "override": {"e": 0.3, "g": 10}})
        """

        if resultfile is None:
            # default result file generated by OM
            self._result_file = self.getWorkDirectory() / f"{self._model_name}_res.mat"
        elif isinstance(resultfile, OMCPath):
            self._result_file = resultfile
        else:
            self._result_file = self._getconn.omcpath(resultfile)
            if not self._result_file.is_absolute():
                self._result_file = self.getWorkDirectory() / resultfile

        if not isinstance(self._result_file, OMCPath):
            raise ModelicaSystemError(f"Invalid result file path: {self._result_file} - must be an OMCPath object!")

        om_cmd = self.simulate_cmd(
            result_file=self._result_file,
            simflags=simflags,
            simargs=simargs,
            timeout=timeout,
        )

        # delete resultfile ...
        if self._result_file.is_file():
            self._result_file.unlink()
        # ... run simulation ...
        cmd_definition = om_cmd.definition()
        returncode = self._getconn.run_model_executable(cmd_run_data=cmd_definition)
        # and check returncode *AND* resultfile
        if returncode != 0 and self._result_file.is_file():
            # check for an empty (=> 0B) result file which indicates a crash of the model executable
            # see: https://github.com/OpenModelica/OMPython/issues/261
            #      https://github.com/OpenModelica/OpenModelica/issues/13829
            if self._result_file.size() == 0:
                self._result_file.unlink()
                raise ModelicaSystemError("Empty result file - this indicates a crash of the model executable!")

            logger.warning(f"Return code = {returncode} but result file exists!")

        self._simulated = True

    def plot(
            self,
            plotdata: str,
            resultfile: Optional[str | os.PathLike] = None,
    ) -> None:
        """
        Plot a variable using OMC; this will work for local OMC usage only (OMCProcessLocal). The reason is that the
        plot is created by OMC which needs access to the local display. This is not the case for docker and WSL.
        """

        if not isinstance(self._getconn.omc_process, OMCProcessLocal):
            raise ModelicaSystemError("Plot is using the OMC plot functionality; "
                                      "thus, it is only working if OMC is running locally!")

        if resultfile is not None:
            plot_result_file = self._getconn.omcpath(resultfile)
        elif self._result_file is not None:
            plot_result_file = self._result_file
        else:
            raise ModelicaSystemError("No resultfile available - either run simulate() before plotting "
                                      "or provide a result file!")

        if not plot_result_file.is_file():
            raise ModelicaSystemError(f"Provided resultfile {repr(plot_result_file.as_posix())} does not exists!")

        expr = f'plot({plotdata}, fileName="{plot_result_file.as_posix()}")'
        self.sendExpression(expr=expr)

    def getSolutions(
            self,
            varList: Optional[str | list[str]] = None,
            resultfile: Optional[str | os.PathLike] = None,
    ) -> tuple[str] | np.ndarray:
        """Extract simulation results from a result data file.

        Args:
            varList: Names of variables to be extracted. Either unspecified to
              get names of available variables, or a single variable name
              as a string, or a list of variable names.
            resultfile: Path to the result file. If unspecified, the result
              file created by simulate() is used.

        Returns:
            If varList is None, a tuple with names of all variables
            is returned.
            If varList is a string, a 1D numpy array is returned.
            If varList is a list, a 2D numpy array is returned.

        Examples:
            >>> mod.getSolutions()
            ('a', 'der(x)', 'time', 'x')
            >>> mod.getSolutions("x")
            np.array([[1.        , 0.90483742, 0.81873075]])
            >>> mod.getSolutions(["x", "der(x)"])
            np.array([[1.        , 0.90483742 , 0.81873075],
                      [-1.       , -0.90483742, -0.81873075]])
            >>> mod.getSolutions(resultfile="c:/a.mat")
            ('a', 'der(x)', 'time', 'x')
            >>> mod.getSolutions("x", resultfile="c:/a.mat")
            np.array([[1.        , 0.90483742, 0.81873075]])
            >>> mod.getSolutions(["x", "der(x)"], resultfile="c:/a.mat")
            np.array([[1.        , 0.90483742 , 0.81873075],
                      [-1.       , -0.90483742, -0.81873075]])
        """
        if resultfile is None:
            if self._result_file is None:
                raise ModelicaSystemError("No result file found. Run simulate() first.")
            result_file = self._result_file
        else:
            result_file = self._getconn.omcpath(resultfile)

        # check if the result file exits
        if not result_file.is_file():
            raise ModelicaSystemError(f"Result file does not exist {result_file.as_posix()}")

        # get absolute path
        result_file = result_file.absolute()

        result_vars = self.sendExpression(f'readSimulationResultVars("{result_file.as_posix()}")')
        self.sendExpression("closeSimulationResultFile()")
        if varList is None:
            return result_vars

        if isinstance(varList, str):
            var_list_checked = [varList]
        elif isinstance(varList, list):
            var_list_checked = varList
        else:
            raise ModelicaSystemError("Unhandled input for getSolutions()")

        for var in var_list_checked:
            if var == "time":
                continue
            if var not in result_vars:
                raise ModelicaSystemError(f"Requested data {repr(var)} does not exist")
        variables = ",".join(var_list_checked)
        res = self.sendExpression(f'readSimulationResult("{result_file.as_posix()}",{{{variables}}})')
        np_res = np.array(res)
        self.sendExpression("closeSimulationResultFile()")
        return np_res

    @staticmethod
    def _prepare_input_data(
            input_args: Any,
            input_kwargs: dict[str, Any],
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

        for input_arg in input_args:
            if isinstance(input_arg, str):
                warnings.warn(message="The definition of values to set should use a dictionary, "
                                      "i.e. {'key1': 'val1', 'key2': 'val2', ...}. Please convert all cases which "
                                      "use a string ('key=val') or list ['key1=val1', 'key2=val2', ...]",
                              category=DeprecationWarning,
                              stacklevel=3)
                input_data = input_data | prepare_str(input_arg)
            elif isinstance(input_arg, list):
                warnings.warn(message="The definition of values to set should use a dictionary, "
                                      "i.e. {'key1': 'val1', 'key2': 'val2', ...}. Please convert all cases which "
                                      "use a string ('key=val') or list ['key1=val1', 'key2=val2', ...]",
                              category=DeprecationWarning,
                              stacklevel=3)

                for item in input_arg:
                    if not isinstance(item, str):
                        raise ModelicaSystemError(f"Invalid input data type for set*() function: {type(item)}!")
                    input_data = input_data | prepare_str(item)
            elif isinstance(input_arg, dict):
                input_data = input_data | input_arg
            else:
                raise ModelicaSystemError(f"Invalid input data type for set*() function: {type(input_arg)}!")

        if len(input_kwargs):
            for key, val in input_kwargs.items():
                # ensure all values are strings to align it on one type: dict[str, str]
                if not isinstance(val, str):
                    # spaces have to be removed as setInput() could take list of tuples as input and spaces would
                    # result in an error on recreating the input data
                    str_val = str(val).replace(' ', '')
                else:
                    str_val = val
                if ' ' in key or ' ' in str_val:
                    raise ModelicaSystemError(f"Spaces not allowed in key/value pairs: {repr(key)} = {repr(val)}!")
                input_data[key] = str_val

        return input_data

    def _set_method_helper(
            self,
            inputdata: dict[str, str],
            classdata: dict[str, Any],
            datatype: str,
            overridedata: Optional[dict[str, str]] = None,
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
        overridedata
            dict() which stores the new override variables list,
        """

        for key, val in inputdata.items():
            if key not in classdata:
                raise ModelicaSystemError(f"Invalid variable for type {repr(datatype)}: {repr(key)}")

            if datatype == "parameter" and not self.isParameterChangeable(key):
                raise ModelicaSystemError(f"It is not possible to set the parameter {repr(key)}. It seems to be "
                                          "structural, final, protected, evaluated or has a non-constant binding. "
                                          "Use sendExpression(...) and rebuild the model using buildModel() API; "
                                          "command to set the parameter before rebuilding the model: "
                                          "sendExpression(\"setParameterValue("
                                          f"{self._model_name}, {key}, {val if val is not None else '<?value?>'}"
                                          ")\").")

            classdata[key] = val
            if overridedata is not None:
                overridedata[key] = val

        return True

    def isParameterChangeable(
            self,
            name: str,
    ) -> bool:
        q = self.getQuantities(name)
        if q[0]["changeable"] == "false":
            return False
        return True

    def setContinuous(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set continuous values. It can be called:
        with a sequence of continuous name and assigning corresponding values as arguments as show in the example below:
        usage
        >>> setContinuous("Name=value")  # depreciated
        >>> setContinuous(["Name1=value1","Name2=value2"])  # depreciated

        >>> setContinuous(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setContinuous(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._continuous,
            datatype="continuous",
            overridedata=self._override_variables)

    def setParameters(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set parameter values. It can be called:
        with a sequence of parameter name and assigning corresponding value as arguments as show in the example below:
        usage
        >>> setParameters("Name=value")  # depreciated
        >>> setParameters(["Name1=value1","Name2=value2"])  # depreciated

        >>> setParameters(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setParameters(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._params,
            datatype="parameter",
            overridedata=self._override_variables)

    def setSimulationOptions(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set simulation options. It can be called:
        with a sequence of simulation options name and assigning corresponding values as arguments as show in the
        example below:
        usage
        >>> setSimulationOptions("Name=value")  # depreciated
        >>> setSimulationOptions(["Name1=value1","Name2=value2"])  # depreciated

        >>> setSimulationOptions(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setSimulationOptions(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._simulate_options,
            datatype="simulation-option",
            overridedata=self._simulate_options_override)

    def setLinearizationOptions(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set linearization options. It can be called:
        with a sequence of linearization options name and assigning corresponding value as arguments as show in the
        example below
        usage
        >>> setLinearizationOptions("Name=value")  # depreciated
        >>> setLinearizationOptions(["Name1=value1","Name2=value2"])  # depreciated

        >>> setLinearizationOptions(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setLinearizationOptions(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._linearization_options,
            datatype="Linearization-option",
            overridedata=None)

    def setOptimizationOptions(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set optimization options. It can be called:
        with a sequence of optimization options name and assigning corresponding values as arguments as show in the
        example below:
        usage
        >>> setOptimizationOptions("Name=value")  # depreciated
        >>> setOptimizationOptions(["Name1=value1","Name2=value2"])  # depreciated

        >>> setOptimizationOptions(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setOptimizationOptions(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._optimization_options,
            datatype="optimization-option",
            overridedata=None)

    def setInputs(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set input values. It can be called with a sequence of input name and assigning
        corresponding values as arguments as show in the example below. Compared to other set*() methods this is a
        special case as value could be a list of tuples - these are converted to a string in _prepare_input_data()
        and restored here via ast.literal_eval().

        >>> setInputs("Name=value")  # depreciated
        >>> setInputs(["Name1=value1","Name2=value2"])  # depreciated

        >>> setInputs(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setInputs(**param)
        """
        inputdata = self._prepare_input_data(input_args=args, input_kwargs=kwargs)

        for key, val in inputdata.items():
            if key not in self._inputs:
                raise ModelicaSystemError(f"{key} is not an input")

            if not isinstance(val, str):
                raise ModelicaSystemError(f"Invalid data in input for {repr(key)}: {repr(val)}")

            val_evaluated = ast.literal_eval(val)

            if isinstance(val_evaluated, (int, float)):
                self._inputs[key] = [(float(self._simulate_options["startTime"]), float(val)),
                                     (float(self._simulate_options["stopTime"]), float(val))]
            elif isinstance(val_evaluated, list):
                if not all([isinstance(item, tuple) for item in val_evaluated]):
                    raise ModelicaSystemError("Value for setInput() must be in tuple format; "
                                              f"got {repr(val_evaluated)}")
                if val_evaluated != sorted(val_evaluated, key=lambda x: x[0]):
                    raise ModelicaSystemError("Time value should be in increasing order; "
                                              f"got {repr(val_evaluated)}")

                for item in val_evaluated:
                    if item[0] < float(self._simulate_options["startTime"]):
                        raise ModelicaSystemError(f"Time value in {repr(item)} of {repr(val_evaluated)} is less "
                                                  "than the simulation start time")
                    if len(item) != 2:
                        raise ModelicaSystemError(f"Value {repr(item)} of {repr(val_evaluated)} "
                                                  "is in incorrect format!")

                self._inputs[key] = val_evaluated
            else:
                raise ModelicaSystemError(f"Data cannot be evaluated for {repr(key)}: {repr(val)}")

        return True

    def _createCSVData(self, csvfile: Optional[OMCPath] = None) -> OMCPath:
        """
        Create a csv file with inputs for the simulation/optimization of the model. If csvfile is provided as argument,
        this file is used; else a generic file name is created.
        """
        start_time: float = float(self._simulate_options["startTime"])
        stop_time: float = float(self._simulate_options["stopTime"])

        # Replace None inputs with a default constant zero signal
        inputs: dict[str, list[tuple[float, float]]] = {}
        for input_name, input_signal in self._inputs.items():
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
                signal[:, 1],  # values
            )

        # Write CSV file
        input_names = list(interpolated_inputs.keys())
        header = ['time'] + input_names + ['end']

        csv_rows = [header]
        for i, t in enumerate(all_times):
            row = [
                t,  # time
                *(interpolated_inputs[name][i] for name in input_names),  # input values
                0,  # trailing 'end' column
            ]
            csv_rows.append(row)

        if csvfile is None:
            csvfile = self.getWorkDirectory() / f'{self._model_name}.csv'

        # basic definition of a CSV file using csv_rows as input
        csv_content = "\n".join([",".join(map(str, row)) for row in csv_rows]) + "\n"

        csvfile.write_text(csv_content)

        return csvfile

    def convertMo2Fmu(self, version: str = "2.0", fmuType: str = "me_cs",
                      fileNamePrefix: str = "<default>",
                      includeResources: bool = True) -> str:
        """Translate the model into a Functional Mockup Unit.

        Args:
            See https://build.openmodelica.org/Documentation/OpenModelica.Scripting.translateModelFMU.html

        Returns:
            str: Path to the created '*.fmu' file.

        Examples:
            >>> mod.convertMo2Fmu()
            '/tmp/tmpmhfx9umo/CauerLowPassAnalog.fmu'
            >>> mod.convertMo2Fmu(version="2.0", fmuType="me|cs|me_cs", fileNamePrefix="<default>",
                                  includeResources=True)
            '/tmp/tmpmhfx9umo/CauerLowPassAnalog.fmu'
        """

        if fileNamePrefix == "<default>":
            fileNamePrefix = self._model_name
        if includeResources:
            includeResourcesStr = "true"
        else:
            includeResourcesStr = "false"
        properties = (f'version="{version}", fmuType="{fmuType}", '
                      f'fileNamePrefix="{fileNamePrefix}", includeResources={includeResourcesStr}')
        fmu = self._requestApi(apiName='buildModelFMU', entity=self._model_name, properties=properties)

        # report proper error message
        if not os.path.exists(fmu):
            raise ModelicaSystemError(f"Missing FMU file: {fmu}")

        return fmu

    # to convert FMU to Modelica model
    def convertFmu2Mo(self, fmuName):  # 20
        """
        In order to load FMU, at first it needs to be translated into Modelica model. This method is used to generate
        Modelica model from the given FMU. It generates "fmuName_me_FMU.mo".
        Currently, it only supports Model Exchange conversion.
        usage
        >>> convertFmu2Mo("c:/BouncingBall.Fmu")
        """

        fileName = self._requestApi(apiName='importFMU', entity=fmuName)

        # report proper error message
        if not os.path.exists(fileName):
            raise ModelicaSystemError(f"Missing file {fileName}")

        return fileName

    def optimize(self) -> dict[str, Any]:
        """Perform model-based optimization.

        Optimization options set by setOptimizationOptions() are used.

        Returns:
            A dict with various values is returned. One of these values is the
            path to the result file.

        Examples:
            >>> mod.optimize()
            {'messages': 'LOG_SUCCESS | info | The initialization finished successfully without homotopy method. ...'
             'resultFile': '/tmp/tmp68guvjhs/BangBang2021_res.mat',
             'simulationOptions': 'startTime = 0.0, stopTime = 1.0, numberOfIntervals = '
                                  "1000, tolerance = 1e-8, method = 'optimization', "
                                  "fileNamePrefix = 'BangBang2021', options = '', "
                                  "outputFormat = 'mat', variableFilter = '.*', cflags = "
                                  "'', simflags = '-s=\\'optimization\\' "
                                  "-optimizerNP=\\'1\\''",
             'timeBackend': 0.008684897,
             'timeCompile': 0.7546678929999999,
             'timeFrontend': 0.045438053000000006,
             'timeSimCode': 0.0018537170000000002,
             'timeSimulation': 0.266354356,
             'timeTemplates': 0.002007785,
             'timeTotal': 1.079097854}
        """
        cName = self._model_name
        properties = ','.join(f"{key}={val}" for key, val in self._optimization_options.items())
        self.setCommandLineOptions("-g=Optimica")
        optimizeResult = self._requestApi(apiName='optimize', entity=cName, properties=properties)

        return optimizeResult

    def linearize(
            self,
            lintime: Optional[float] = None,
            simflags: Optional[str] = None,
            simargs: Optional[dict[str, Optional[str | dict[str, Any] | numbers.Number]]] = None,
            timeout: Optional[float] = None,
    ) -> LinearizationResult:
        """Linearize the model according to linearization options.

        See setLinearizationOptions.

        Args:
            lintime: Override "stopTime" value.
            simflags: String of extra command line flags for the model binary.
              This argument is deprecated, use simargs instead.
            simargs: A dict with command line flags and possible options; example: "simargs={'csvInput': 'a.csv'}"
            timeout: Maximum execution time in seconds.

        Returns:
            A LinearizationResult object is returned. This allows several
            uses:
            * `(A, B, C, D) = linearize()` to get just the matrices,
            * `result = linearize(); result.A` to get everything and access the
              attributes one by one,
            * `result = linearize(); A = result[0]` mostly just for backwards
              compatibility, because linearize() used to return `[A, B, C, D]`.
        """
        if len(self._quantities) == 0:
            # if self._quantities has no content, the xml file was not parsed; see self._xmlparse()
            raise ModelicaSystemError(
                "Linearization cannot be performed as the model is not build, "
                "use ModelicaSystem() to build the model first"
            )

        om_cmd = ModelicaSystemCmd(
            session=self._getconn,
            runpath=self.getWorkDirectory(),
            modelname=self._model_name,
            timeout=timeout,
        )

        override_content = (
                "\n".join([f"{key}={value}" for key, value in self._override_variables.items()])
                + "\n".join([f"{key}={value}" for key, value in self._linearization_options.items()])
                + "\n"
        )
        override_file = self.getWorkDirectory() / f'{self._model_name}_override_linear.txt'
        override_file.write_text(override_content)

        om_cmd.arg_set(key="overrideFile", val=override_file.as_posix())

        if self._inputs:
            for key, data in self._inputs.items():
                if data is not None:
                    for value in data:
                        if value[0] < float(self._simulate_options["startTime"]):
                            raise ModelicaSystemError('Input time value is less than simulation startTime')
            csvfile = self._createCSVData()
            om_cmd.arg_set(key="csvInput", val=csvfile.as_posix())

        om_cmd.arg_set(key="l", val=str(lintime or self._linearization_options["stopTime"]))

        # allow runtime simulation flags from user input
        if simflags is not None:
            om_cmd.args_set(args=om_cmd.parse_simflags(simflags=simflags))

        if simargs:
            om_cmd.args_set(args=simargs)

        # the file create by the model executable which contains the matrix and linear inputs, outputs and states
        linear_file = self.getWorkDirectory() / "linearized_model.py"
        linear_file.unlink(missing_ok=True)

        cmd_definition = om_cmd.definition()
        returncode = self._getconn.run_model_executable(cmd_run_data=cmd_definition)
        if returncode != 0:
            raise ModelicaSystemError(f"Linearize failed with return code: {returncode}")
        if not linear_file.is_file():
            raise ModelicaSystemError(f"Linearization failed: {linear_file} not found!")

        self._simulated = True

        # extract data from the python file with the linearized model using the ast module - this allows to get the
        # needed information without executing the created code
        linear_data = {}
        linear_file_content = linear_file.read_text()
        try:
            # ignore possible typing errors below (mypy) - these are caught by the try .. except .. block
            linear_file_ast = ast.parse(linear_file_content)
            for body_part in linear_file_ast.body[0].body:  # type: ignore
                if not isinstance(body_part, ast.Assign):
                    continue

                target = body_part.targets[0].id  # type: ignore
                value = ast.literal_eval(body_part.value)

                linear_data[target] = value
        except (AttributeError, IndexError, ValueError, SyntaxError, TypeError) as ex:
            raise ModelicaSystemError(f"Error parsing linearization file {linear_file}!") from ex

        # remove the file
        linear_file.unlink()

        self._linearized_inputs = linear_data["inputVars"]
        self._linearized_outputs = linear_data["outputVars"]
        self._linearized_states = linear_data["stateVars"]

        return LinearizationResult(
            n=linear_data["n"],
            m=linear_data["m"],
            p=linear_data["p"],
            x0=linear_data["x0"],
            u0=linear_data["u0"],
            A=linear_data["A"],
            B=linear_data["B"],
            C=linear_data["C"],
            D=linear_data["D"],
            stateVars=linear_data["stateVars"],
            inputVars=linear_data["inputVars"],
            outputVars=linear_data["outputVars"],
        )

    def getLinearInputs(self) -> list[str]:
        """Get names of input variables of the linearized model."""
        return self._linearized_inputs

    def getLinearOutputs(self) -> list[str]:
        """Get names of output variables of the linearized model."""
        return self._linearized_outputs

    def getLinearStates(self) -> list[str]:
        """Get names of state variables of the linearized model."""
        return self._linearized_states


class ModelicaSystemDoE:
    """
    Class to run DoEs based on a (Open)Modelica model using ModelicaSystem

    Example
    -------
    ```
    import OMPython
    import pathlib


    def run_doe():
        mypath = pathlib.Path('.')

        model = mypath / "M.mo"
        model.write_text(
            "    model M\n"
            "      parameter Integer p=1;\n"
            "      parameter Integer q=1;\n"
            "      parameter Real a = -1;\n"
            "      parameter Real b = -1;\n"
            "      Real x[p];\n"
            "      Real y[q];\n"
            "    equation\n"
            "      der(x) = a * fill(1.0, p);\n"
            "      der(y) = b * fill(1.0, q);\n"
            "    end M;\n"
        )

        param = {
            # structural
            'p': [1, 2],
            'q': [3, 4],
            # simple
            'a': [5, 6],
            'b': [7, 8],
        }

        resdir = mypath / 'DoE'
        resdir.mkdir(exist_ok=True)

        doe_mod = OMPython.ModelicaSystemDoE(
            fileName=model.as_posix(),
            modelName="M",
            parameters=param,
            resultpath=resdir,
            simargs={"override": {'stopTime': 1.0}},
        )
        doe_mod.prepare()
        doe_dict = doe_mod.get_doe()
        doe_mod.simulate()
        doe_sol = doe_mod.get_solutions()

        # ... work with doe_df and doe_sol ...


    if __name__ == "__main__":
        run_doe()
    ```

    """

    # Dictionary keys used in simulation dict (see _sim_dict or get_doe()). These dict keys contain a space and, thus,
    # cannot be used as OM variable identifiers. They are defined here as reference for any evaluation of the data.
    DICT_ID_STRUCTURE: str = 'ID structure'
    DICT_ID_NON_STRUCTURE: str = 'ID non-structure'
    DICT_RESULT_AVAILABLE: str = 'result available'

    def __init__(
            self,
            fileName: Optional[str | os.PathLike] = None,
            modelName: Optional[str] = None,
            lmodel: Optional[list[str | tuple[str, str]]] = None,
            commandLineOptions: Optional[list[str]] = None,
            variableFilter: Optional[str] = None,
            customBuildDirectory: Optional[str | os.PathLike] = None,
            omhome: Optional[str] = None,

            simargs: Optional[dict[str, Optional[str | dict[str, str] | numbers.Number]]] = None,
            timeout: Optional[int] = None,

            resultpath: Optional[str | os.PathLike] = None,
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

        if resultpath is not None:
            self._resultpath = self.session().omcpath(resultpath)
        else:
            self._resultpath = self.session().omcpath_tempdir()

        if not self._resultpath.is_dir():
            raise ModelicaSystemError(f"Resultpath {self._resultpath.as_posix()} does not exists!")

        if isinstance(parameters, dict):
            self._parameters = parameters
        else:
            self._parameters = {}

        self._sim_dict: Optional[dict[str, dict[str, Any]]] = None
        self._sim_task_query: queue.Queue = queue.Queue()

    def session(self) -> OMCSessionZMQ:
        """
        Return the OMC session used for this class.
        """
        return self._mod.session()

    def prepare(self) -> int:
        """
        Prepare the DoE by evaluating the parameters. Each structural parameter requires a new instance of
        ModelicaSystem while the non-structural parameters can just be set on the executable.

        The return value is the number of simulation defined.
        """

        param_structure = {}
        param_non_structure = {}
        for param_name in self._parameters.keys():
            changeable = self._mod.isParameterChangeable(name=param_name)
            logger.info(f"Parameter {repr(param_name)} is changeable? {changeable}")

            if changeable:
                param_non_structure[param_name] = self._parameters[param_name]
            else:
                param_structure[param_name] = self._parameters[param_name]

        param_structure_combinations = list(itertools.product(*param_structure.values()))
        param_simple_combinations = list(itertools.product(*param_non_structure.values()))

        self._sim_dict = {}
        for idx_pc_structure, pc_structure in enumerate(param_structure_combinations):
            mod_structure = ModelicaSystem(
                fileName=self._fileName,
                modelName=self._modelName,
                lmodel=self._lmodel,
                commandLineOptions=self._CommandLineOptions,
                variableFilter=self._variableFilter,
                customBuildDirectory=self._customBuildDirectory,
                omhome=self._omhome,
                build=False,
            )

            sim_param_structure = {}
            for idx_structure, pk_structure in enumerate(param_structure.keys()):
                sim_param_structure[pk_structure] = pc_structure[idx_structure]

                pk_value = pc_structure[idx_structure]
                if isinstance(pk_value, str):
                    pk_value_str = pk_value.replace('"', '\\"')
                    expression = f"setParameterValue({self._modelName}, {pk_structure}, \"{pk_value_str}\")"
                elif isinstance(pk_value, bool):
                    pk_value_bool_str = "true" if pk_value else "false"
                    expression = f"setParameterValue({self._modelName}, {pk_structure}, {pk_value_bool_str});"
                else:
                    expression = f"setParameterValue({self._modelName}, {pk_structure}, {pk_value})"
                res = mod_structure.sendExpression(expression)
                if not res:
                    raise ModelicaSystemError(f"Cannot set structural parameter {self._modelName}.{pk_structure} "
                                              f"to {pk_value} using {repr(expression)}")

            mod_structure.buildModel(variableFilter=self._variableFilter)

            for idx_pc_simple, pc_simple in enumerate(param_simple_combinations):
                sim_param_simple = {}
                for idx_simple, pk_simple in enumerate(param_non_structure.keys()):
                    sim_param_simple[pk_simple] = cast(Any, pc_simple[idx_simple])

                resfilename = f"DOE_{idx_pc_structure:09d}_{idx_pc_simple:09d}.mat"
                logger.info(f"use result file {repr(resfilename)} "
                            f"for structural parameters: {sim_param_structure} "
                            f"and simple parameters: {sim_param_simple}")
                resultfile = self._resultpath / resfilename

                df_data = (
                        {
                            self.DICT_ID_STRUCTURE: idx_pc_structure,
                        }
                        | sim_param_structure
                        | {
                            self.DICT_ID_NON_STRUCTURE: idx_pc_simple,
                        }
                        | sim_param_simple
                        | {
                            self.DICT_RESULT_AVAILABLE: False,
                        }
                )

                self._sim_dict[resfilename] = df_data

                mscmd = mod_structure.simulate_cmd(
                    result_file=resultfile,
                    timeout=self._timeout,
                )
                if self._simargs is not None:
                    mscmd.args_set(args=self._simargs)
                mscmd.args_set(args={"override": sim_param_simple})

                self._sim_task_query.put(mscmd)

        logger.info(f"Prepared {self._sim_task_query.qsize()} simulation definitions for the defined DoE.")

        return self._sim_task_query.qsize()

    def get_doe(self) -> Optional[dict[str, dict[str, Any]]]:
        """
        Get the defined DoE as a dict, where each key is the result filename and the value is a dict of simulation
        settings including structural and non-structural parameters.

        The following code snippet can be used to convert the data to a pandas dataframe:

        ```
        import pandas as pd

        doe_dict = doe_mod.get_doe()
        doe_df = pd.DataFrame.from_dict(data=doe_dict, orient='index')
        ```

        """
        return self._sim_dict

    def simulate(
            self,
            num_workers: int = 3,
    ) -> bool:
        """
        Simulate the DoE using the defined number of workers.

        Returns True if all simulations were done successfully, else False.
        """

        sim_query_total = self._sim_task_query.qsize()
        if not isinstance(self._sim_dict, dict) or len(self._sim_dict) == 0:
            raise ModelicaSystemError("Missing Doe Summary!")
        sim_dict_total = len(self._sim_dict)

        def worker(worker_id, task_queue):
            while True:
                try:
                    # Get the next task from the queue
                    mscmd = task_queue.get(block=False)
                except queue.Empty:
                    logger.info(f"[Worker {worker_id}] No more simulations to run.")
                    break

                if mscmd is None:
                    raise ModelicaSystemError("Missing simulation definition!")

                resultfile = mscmd.arg_get(key='r')
                resultpath = self.session().omcpath(resultfile)

                logger.info(f"[Worker {worker_id}] Performing task: {resultpath.name}")

                try:
                    mscmd.run()
                except ModelicaSystemError as ex:
                    logger.warning(f"Simulation error for {resultpath.name}: {ex}")

                # Mark the task as done
                task_queue.task_done()

                sim_query_done = sim_query_total - self._sim_task_query.qsize()
                logger.info(f"[Worker {worker_id}] Task completed: {resultpath.name} "
                            f"({sim_query_total - sim_query_done}/{sim_query_total} = "
                            f"{(sim_query_total - sim_query_done) / sim_query_total * 100:.2f}% of tasks left)")

        logger.info(f"Start simulations for DoE with {sim_query_total} simulations "
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

        sim_dict_done = 0
        for resultfilename in self._sim_dict:
            resultfile = self._resultpath / resultfilename

            # include check for an empty (=> 0B) result file which indicates a crash of the model executable
            # see: https://github.com/OpenModelica/OMPython/issues/261
            # https://github.com/OpenModelica/OpenModelica/issues/13829
            if resultfile.is_file() and resultfile.size() > 0:
                self._sim_dict[resultfilename][self.DICT_RESULT_AVAILABLE] = True
                sim_dict_done += 1

        logger.info(f"All workers finished ({sim_dict_done} of {sim_dict_total} simulations with a result file).")

        return sim_dict_total == sim_dict_done

    def get_solutions(
            self,
            var_list: Optional[list] = None,
    ) -> Optional[tuple[str] | dict[str, dict[str, np.ndarray]]]:
        """
        Get all solutions of the DoE run. The following return values are possible:

        * A list of variables if val_list == None

        * The Solutions as dict[str, pd.DataFrame] if a value list (== val_list) is defined.

        The following code snippet can be used to convert the solution data for each run to a pandas dataframe:

        ```
        import pandas as pd

        doe_sol = doe_mod.get_solutions()
        for key in doe_sol:
            data = doe_sol[key]['data']
            if data:
                doe_sol[key]['df'] = pd.DataFrame.from_dict(data=data)
            else:
                doe_sol[key]['df'] = None
        ```

        """
        if not isinstance(self._sim_dict, dict):
            return None

        if len(self._sim_dict) == 0:
            raise ModelicaSystemError("No result files available - all simulations did fail?")

        sol_dict: dict[str, dict[str, Any]] = {}
        for resultfilename in self._sim_dict:
            resultfile = self._resultpath / resultfilename

            sol_dict[resultfilename] = {}

            if not self._sim_dict[resultfilename][self.DICT_RESULT_AVAILABLE]:
                sol_dict[resultfilename]['msg'] = 'No result file available!'
                sol_dict[resultfilename]['data'] = {}
                continue

            if var_list is None:
                var_list_row = list(self._mod.getSolutions(resultfile=resultfile.as_posix()))
            else:
                var_list_row = var_list

            try:
                sol = self._mod.getSolutions(varList=var_list_row, resultfile=resultfile.as_posix())
                sol_data = {var: sol[idx] for idx, var in enumerate(var_list_row)}
                sol_dict[resultfilename]['msg'] = 'Simulation available'
                sol_dict[resultfilename]['data'] = sol_data
            except ModelicaSystemError as ex:
                msg = f"Error reading solution for {resultfilename}: {ex}"
                logger.warning(msg)
                sol_dict[resultfilename]['msg'] = msg
                sol_dict[resultfilename]['data'] = {}

        return sol_dict
