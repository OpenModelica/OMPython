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

from OMPython.OMCSession import OMCSessionException, OMCSessionZMQ, OMCProcessLocal

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

    def __init__(self, runpath: pathlib.Path, modelname: str, timeout: Optional[float] = None) -> None:
        self._runpath = pathlib.Path(runpath).resolve().absolute()
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

    def get_exe(self) -> pathlib.Path:
        """Get the path to the compiled model executable."""
        if platform.system() == "Windows":
            path_exe = self._runpath / f"{self._model_name}.exe"
        else:
            path_exe = self._runpath / self._model_name

        if not path_exe.exists():
            raise ModelicaSystemError(f"Application file path not found: {path_exe}")

        return path_exe

    def get_cmd(self) -> list:
        """Get a list with the path to the executable and all command line args.

        This can later be used as an argument for subprocess.run().
        """

        path_exe = self.get_exe()

        cmdl = [path_exe.as_posix()]
        for key in sorted(self._args):
            if self._args[key] is None:
                cmdl.append(f"-{key}")
            else:
                cmdl.append(f"-{key}={self._args[key]}")

        return cmdl

    def run(self) -> int:
        """Run the requested simulation.

        Returns
        -------
            Subprocess return code (0 on success).
        """

        cmdl: list = self.get_cmd()

        logger.debug("Run OM command %s in %s", repr(cmdl), self._runpath.as_posix())

        if platform.system() == "Windows":
            path_dll = ""

            # set the process environment from the generated .bat file in windows which should have all the dependencies
            path_bat = self._runpath / f"{self._model_name}.bat"
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
            fileName: Optional[str | os.PathLike | pathlib.Path] = None,
            modelName: Optional[str] = None,
            lmodel: Optional[list[str | tuple[str, str]]] = None,
            commandLineOptions: Optional[list[str]] = None,
            variableFilter: Optional[str] = None,
            customBuildDirectory: Optional[str | os.PathLike] = None,
            omhome: Optional[str] = None,
            omc_process: Optional[OMCProcessLocal] = None,
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
            if not isinstance(omc_process, OMCProcessLocal):
                raise ModelicaSystemError("Invalid (local) omc process definition provided!")
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
        self._file_name = pathlib.Path(fileName).resolve() if fileName is not None else None  # Model file/package name
        self._simulated = False  # True if the model has already been simulated
        self._result_file: Optional[pathlib.Path] = None  # for storing result file
        self._variable_filter = variableFilter

        if self._file_name is not None and not self._file_name.is_file():  # if file does not exist
            raise IOError(f"{self._file_name} does not exist!")

        self._work_dir: pathlib.Path = self.setWorkDirectory(customBuildDirectory)

        if self._file_name is not None:
            self._loadLibrary(lmodel=self._lmodel)
            self._loadFile(fileName=self._file_name)

        # allow directly loading models from MSL without fileName
        elif fileName is None and modelName is not None:
            self._loadLibrary(lmodel=self._lmodel)

        if build:
            self.buildModel(variableFilter)

    def setCommandLineOptions(self, commandLineOptions: str):
        """
        Set the provided command line option via OMC setCommandLineOptions().
        """
        exp = f'setCommandLineOptions("{commandLineOptions}")'
        self.sendExpression(exp)

    def _loadFile(self, fileName: pathlib.Path):
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

    def setWorkDirectory(self, customBuildDirectory: Optional[str | os.PathLike] = None) -> pathlib.Path:
        """
        Define the work directory for the ModelicaSystem / OpenModelica session. The model is build within this
        directory. If no directory is defined a unique temporary directory is created.
        """
        if customBuildDirectory is not None:
            workdir = pathlib.Path(customBuildDirectory).absolute()
            if not workdir.is_dir():
                raise IOError(f"Provided work directory does not exists: {customBuildDirectory}!")
        else:
            workdir = pathlib.Path(tempfile.mkdtemp()).absolute()
            if not workdir.is_dir():
                raise IOError(f"{workdir} could not be created")

        logger.info("Define work dir as %s", workdir)
        exp = f'cd("{workdir.as_posix()}")'
        self.sendExpression(exp)

        # set the class variable _work_dir ...
        self._work_dir = workdir
        # ... and also return the defined path
        return workdir

    def getWorkDirectory(self) -> pathlib.Path:
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

        xml_file = pathlib.Path(buildModelResult[0]).parent / buildModelResult[1]
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

    def _xmlparse(self, xml_file: pathlib.Path):
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
        else:
            if names is None:
                for i in self._continuous:
                    try:
                        value = self.getSolutions(i)
                        self._continuous[i] = value[0][-1]
                    except (OMCSessionException, ModelicaSystemError) as ex:
                        raise ModelicaSystemError(f"{i} could not be computed") from ex
                return self._continuous

            if isinstance(names, str):
                if names in self._continuous:
                    value = self.getSolutions(names)
                    self._continuous[names] = value[0][-1]
                    return [self._continuous[names]]
                else:
                    raise ModelicaSystemError(f"{names} is not continuous")

            if isinstance(names, list):
                valuelist = []
                for i in names:
                    if i in self._continuous:
                        value = self.getSolutions(i)
                        self._continuous[i] = value[0][-1]
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
            return self._params
        elif isinstance(names, str):
            return [self._params[names]]
        elif isinstance(names, list):
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
        elif isinstance(names, str):
            return [self._inputs[names]]
        elif isinstance(names, list):
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
            elif isinstance(names, str):
                return [self._outputs[names]]
            else:
                return [self._outputs[x] for x in names]
        else:
            if names is None:
                for i in self._outputs:
                    value = self.getSolutions(i)
                    self._outputs[i] = value[0][-1]
                return self._outputs
            elif isinstance(names, str):
                if names in self._outputs:
                    value = self.getSolutions(names)
                    self._outputs[names] = value[0][-1]
                    return [self._outputs[names]]
                else:
                    raise KeyError(names)
            elif isinstance(names, list):
                valuelist = []
                for i in names:
                    if i in self._outputs:
                        value = self.getSolutions(i)
                        self._outputs[i] = value[0][-1]
                        valuelist.append(value[0][-1])
                    else:
                        raise KeyError(i)
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
            {'startTime': '0', 'stopTime': '1.234', 'stepSize': '0.002', 'tolerance': '1.1e-08', 'solver': 'dassl', 'outputFormat': 'mat'}
            >>> mod.getSimulationOptions("stopTime")
            ['1.234']
            >>> mod.getSimulationOptions(["tolerance", "stopTime"])
            ['1.1e-08', '1.234']
        """
        if names is None:
            return self._simulate_options
        elif isinstance(names, str):
            return [self._simulate_options[names]]
        elif isinstance(names, list):
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
        elif isinstance(names, str):
            return [self._linearization_options[names]]
        elif isinstance(names, list):
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
        elif isinstance(names, str):
            return [self._optimization_options[names]]
        elif isinstance(names, list):
            return [self._optimization_options[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getOptimizationOptions()")

    def simulate_cmd(
            self,
            result_file: pathlib.Path,
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
            for key in self._inputs:
                val = self._inputs[key]
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
            mod.simulate(simflags="-noEventEmit -noRestart -override=e=0.3,g=10")  # set runtime simulation flags, deprecated
            mod.simulate(simargs={"noEventEmit": None, "noRestart": None, "override": "override": {"e": 0.3, "g": 10}})  # using simargs
        """

        if resultfile is None:
            # default result file generated by OM
            self._result_file = self.getWorkDirectory() / f"{self._model_name}_res.mat"
        elif os.path.exists(resultfile):
            self._result_file = pathlib.Path(resultfile)
        else:
            self._result_file = self.getWorkDirectory() / resultfile

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
        returncode = om_cmd.run()
        # and check returncode *AND* resultfile
        if returncode != 0 and self._result_file.is_file():
            # check for an empty (=> 0B) result file which indicates a crash of the model executable
            # see: https://github.com/OpenModelica/OMPython/issues/261
            #      https://github.com/OpenModelica/OpenModelica/issues/13829
            if self._result_file.stat().st_size == 0:
                self._result_file.unlink()
                raise ModelicaSystemError("Empty result file - this indicates a crash of the model executable!")

            logger.warning(f"Return code = {returncode} but result file exists!")

        self._simulated = True

    def getSolutions(self, varList: Optional[str | list[str]] = None, resultfile: Optional[str] = None) -> tuple[str] | np.ndarray:
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
            result_file = pathlib.Path(resultfile)

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
                raise ModelicaSystemError("Unhandled case in setMethodHelper.apply_single() - "
                                          f"{repr(key)} is not a {repr(datatype)} variable")

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
            cvals: str | list[str] | dict[str, Any],
    ) -> bool:
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
            classdata=self._continuous,
            datatype="continuous",
            overridedata=self._override_variables)

    def setParameters(
            self,
            pvals: str | list[str] | dict[str, Any],
    ) -> bool:
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
            classdata=self._params,
            datatype="parameter",
            overridedata=self._override_variables)

    def setSimulationOptions(
            self,
            simOptions: str | list[str] | dict[str, Any],
    ) -> bool:
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
            classdata=self._simulate_options,
            datatype="simulation-option",
            overridedata=self._simulate_options_override)

    def setLinearizationOptions(
            self,
            linearizationOptions: str | list[str] | dict[str, Any],
    ) -> bool:
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
            classdata=self._linearization_options,
            datatype="Linearization-option",
            overridedata=None)

    def setOptimizationOptions(
            self,
            optimizationOptions: str | list[str] | dict[str, Any],
    ) -> bool:
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
            classdata=self._optimization_options,
            datatype="optimization-option",
            overridedata=None)

    def setInputs(
            self,
            name: str | list[str] | dict[str, Any],
    ) -> bool:
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

    def _createCSVData(self, csvfile: Optional[pathlib.Path] = None) -> pathlib.Path:
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
            >>> mod.convertMo2Fmu(version="2.0", fmuType="me|cs|me_cs", fileNamePrefix="<default>", includeResources=True)
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
        In order to load FMU, at first it needs to be translated into Modelica model. This method is used to generate Modelica model from the given FMU. It generates "fmuName_me_FMU.mo".
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
            runpath=self.getWorkDirectory(),
            modelname=self._model_name,
            timeout=timeout,
        )

        overrideLinearFile = self.getWorkDirectory() / f'{self._model_name}_override_linear.txt'

        with open(file=overrideLinearFile, mode="w", encoding="utf-8") as fh:
            for key1, value1 in self._override_variables.items():
                fh.write(f"{key1}={value1}\n")
            for key2, value2 in self._linearization_options.items():
                fh.write(f"{key2}={value2}\n")

        om_cmd.arg_set(key="overrideFile", val=overrideLinearFile.as_posix())

        if self._inputs:
            for key in self._inputs:
                data = self._inputs[key]
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

        returncode = om_cmd.run()
        if returncode != 0:
            raise ModelicaSystemError(f"Linearize failed with return code: {returncode}")
        if not linear_file.exists():
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
