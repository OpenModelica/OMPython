# -*- coding: utf-8 -*-
"""
Definition of main class to run Modelica simulations - ModelicaSystem.
"""

import abc
import ast
from dataclasses import dataclass
import logging
import numbers
import os
import re
from typing import Any, Optional
import xml.etree.ElementTree as ET

import numpy as np

from OMPython.model_execution import (
    ModelExecutionCmd,
    ModelExecutionException,
)
from OMPython.om_session_abc import (
    OMPathABC,
    OMSessionABC,
)

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaSystemError(Exception):
    """
    Exception used in ModelicaSystem classes.
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


class ModelicaSystemABC(metaclass=abc.ABCMeta):
    """
    Base class to simulate a Modelica models.
    """

    def __init__(
            self,
            session: OMSessionABC,
            work_directory: Optional[str | os.PathLike] = None,
    ) -> None:
        """Create a ModelicaSystem instance. To define the model use model() or convertFmu2Mo().

        Args:
            work_directory: Path to a directory to be used for temporary
              files like the model executable. If left unspecified, a tmp
              directory will be created.
            session: definition of a (local) OMC session to be used. If
              unspecified, a new local session will be created.
        """

        self._quantities: list[dict[str, Any]] = []
        self._params: dict[str, str] = {}  # even numerical values are stored as str
        self._inputs: dict[str, list[tuple[float, float]]] = {}
        self._outputs: dict[str, np.float64] = {}  # numpy.float64 as it allows to define None values
        self._continuous: dict[str, np.float64] = {}  # numpy.float64 as it allows to define None values
        self._simulate_options: dict[str, str] = {}
        self._override_variables: dict[str, str] = {}
        self._simulate_options_override: dict[str, str] = {}
        self._linearization_options: dict[str, str] = {
            'startTime': str(0.0),
            'stopTime': str(1.0),
            'stepSize': str(0.002),
            'tolerance': str(1e-8),
        }
        self._optimization_options = self._linearization_options | {
            'numberOfIntervals': str(500),
        }
        self._linearized_inputs: list[str] = []  # linearization input list
        self._linearized_outputs: list[str] = []  # linearization output list
        self._linearized_states: list[str] = []  # linearization states list

        self._simulated = False  # True if the model has already been simulated
        self._result_file: Optional[OMPathABC] = None  # for storing result file

        self._model_name: Optional[str] = None
        self._libraries: Optional[list[str | tuple[str, str]]] = None
        self._file_name: Optional[OMPathABC] = None
        self._variable_filter: Optional[str] = None

        self._session = session
        # get OpenModelica version
        version_str = self._session.get_version()
        self._version = self._parse_om_version(version=version_str)

        self._work_dir: OMPathABC = self.setWorkDirectory(work_directory)

    def get_session(self) -> OMSessionABC:
        """
        Return the OMC session used for this class.
        """
        return self._session

    def get_model_name(self) -> str:
        """
        Return the defined model name.
        """
        if not isinstance(self._model_name, str):
            raise ModelicaSystemError("No model name defined!")

        return self._model_name

    def setWorkDirectory(self, work_directory: Optional[str | os.PathLike] = None) -> OMPathABC:
        """
        Define the work directory for the ModelicaSystem / OpenModelica session. The model is build within this
        directory. If no directory is defined a unique temporary directory is created.
        """
        if work_directory is not None:
            workdir = self._session.omcpath(work_directory).absolute()
            if not workdir.is_dir():
                raise IOError(f"Provided work directory does not exists: {work_directory}!")
        else:
            workdir = self._session.omcpath_tempdir().absolute()
            if not workdir.is_dir():
                raise IOError(f"{workdir} could not be created")

        logger.info("Define work dir as %s", workdir)
        self._session.set_workdir(workdir=workdir)

        # set the class variable _work_dir ...
        self._work_dir = workdir
        # ... and also return the defined path
        return workdir

    def getWorkDirectory(self) -> OMPathABC:
        """
        Return the defined working directory for this ModelicaSystem / OpenModelica session.
        """
        return self._work_dir

    def check_model_executable(self):
        """
        Check if the model executable is working
        """
        # check if the executable exists ...
        om_cmd = ModelExecutionCmd(
            runpath=self.getWorkDirectory(),
            cmd_local=self._session.model_execution_local,
            cmd_windows=self._session.model_execution_windows,
            cmd_prefix=self._session.model_execution_prefix(cwd=self.getWorkDirectory()),
            model_name=self._model_name,
        )
        # ... by running it - output help for command help
        om_cmd.arg_set(key="help", val="help")
        cmd_definition = om_cmd.definition()
        try:
            returncode = cmd_definition.run()
        except ModelExecutionException as exc:
            raise ModelicaSystemError(f"Cannot execute model: {exc}") from exc
        if returncode != 0:
            raise ModelicaSystemError("Model executable not working!")

    def _xmlparse(self, xml_file: OMPathABC):
        if not xml_file.is_file():
            raise ModelicaSystemError(f"XML file not generated: {xml_file}")

        xml_content = xml_file.read_text()
        tree = ET.ElementTree(ET.fromstring(xml_content))
        root = tree.getroot()
        if root is None:
            raise ModelicaSystemError(f"Cannot read XML file: {xml_file}")
        for attr in root.iter('DefaultExperiment'):
            for key in ("startTime", "stopTime", "stepSize", "tolerance",
                        "solver", "outputFormat"):
                self._simulate_options[key] = str(attr.get(key))

        for sv in root.iter('ScalarVariable'):
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
                self._continuous[scalar["name"]] = np.float64(scalar["start"])
            if scalar["causality"] == "input":
                self._inputs[scalar["name"]] = scalar["start"]
            if scalar["causality"] == "output":
                self._outputs[scalar["name"]] = np.float64(scalar["start"])

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

    def getContinuousInitial(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, np.float64] | list[np.float64]:
        """
        Get (initial) values of continuous signals.

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
            >>> mod.getContinuousInitial()
            {'x': '1.0', 'der(x)': None, 'y': '-0.4'}
            >>> mod.getContinuousInitial("y")
            ['-0.4']
            >>> mod.getContinuousInitial(["y","x"])
            ['-0.4', '1.0']
        """
        if names is None:
            return self._continuous
        if isinstance(names, str):
            return [self._continuous[names]]
        if isinstance(names, list):
            return [self._continuous[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getContinousInitial()")

    def getParameters(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, str] | list[str]:
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

    def getInputs(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, list[tuple[float, float]]] | list[list[tuple[float, float]]]:
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

    def getOutputsInitial(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, np.float64] | list[np.float64]:
        """
        Get (initial) values of output signals.

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
            >>> mod.getOutputsInitial()
            {'out1': '-0.4', 'out2': '1.2'}
            >>> mod.getOutputsInitial("out1")
            ['-0.4']
            >>> mod.getOutputsInitial(["out1","out2"])
            ['-0.4', '1.2']
        """
        if names is None:
            return self._outputs
        if isinstance(names, str):
            return [self._outputs[names]]
        if isinstance(names, list):
            return [self._outputs[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getOutputsInitial()")

    def getSimulationOptions(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, str] | list[str]:
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

    def getLinearizationOptions(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, str] | list[str]:
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

            The option values are always returned as strings.

        Examples:
            >>> mod.getLinearizationOptions()
            {'startTime': '0.0', 'stopTime': '1.0', 'stepSize': '0.002', 'tolerance': '1e-08'}
            >>> mod.getLinearizationOptions("stopTime")
            ['1.0']
            >>> mod.getLinearizationOptions(["tolerance", "stopTime"])
            ['1e-08', '1.0']
        """
        if names is None:
            return self._linearization_options
        if isinstance(names, str):
            return [self._linearization_options[names]]
        if isinstance(names, list):
            return [self._linearization_options[x] for x in names]

        raise ModelicaSystemError("Unhandled input for getLinearizationOptions()")

    def getOptimizationOptions(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, str] | list[str]:
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

            The option values are always returned as string.

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

    @staticmethod
    def _parse_om_version(version: str) -> tuple[int, int, int]:
        """
        Evaluate an OMC version string and return a tuple of (epoch, major, minor).
        """
        match = re.search(pattern=r"v?(\d+)\.(\d+)\.(\d+)", string=version)
        if not match:
            raise ValueError(f"Version not found in: {version}")
        major, minor, patch = map(int, match.groups())

        return major, minor, patch

    def _process_override_data(
            self,
            om_cmd: ModelExecutionCmd,
            override_file: OMPathABC,
            override_var: dict[str, str],
            override_sim: dict[str, str],
    ) -> None:
        """
        Define the override parameters. As the definition of simulation specific override parameter changes with OM
        1.26.0, version specific code is needed. Please keep in mind, that this will fail if OMC is not used to run the
        model executable.
        """
        if len(override_var) == 0 and len(override_sim) == 0:
            return

        override_content = ""
        if override_var:
            override_content += "\n".join([f"{key}={value}" for key, value in override_var.items()]) + "\n"

        # simulation options are not read from override file from version >= 1.26.0,
        # pass them to simulation executable directly as individual arguments
        # see https://github.com/OpenModelica/OpenModelica/pull/14813
        if override_sim:
            if self._version >= (1, 26, 0):
                for key, opt_value in override_sim.items():
                    om_cmd.arg_set(key=key, val=str(opt_value))
            else:
                override_content += "\n".join([f"{key}={value}" for key, value in override_sim.items()]) + "\n"

        if override_content:
            override_file.write_text(override_content)
            om_cmd.arg_set(key="overrideFile", val=override_file.as_posix())

    def simulate_cmd(
            self,
            result_file: OMPathABC,
            simargs: Optional[dict[str, Optional[str | dict[str, Any] | numbers.Number]]] = None,
    ) -> ModelExecutionCmd:
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
        simargs

        Returns
        -------
            An instance if ModelicaSystemCmd to run the requested simulation.
        """

        om_cmd = ModelExecutionCmd(
            runpath=self.getWorkDirectory(),
            cmd_local=self._session.model_execution_local,
            cmd_windows=self._session.model_execution_windows,
            cmd_prefix=self._session.model_execution_prefix(cwd=self.getWorkDirectory()),
            model_name=self._model_name,
        )

        # always define the result file to use
        om_cmd.arg_set(key="r", val=result_file.as_posix())

        if simargs:
            om_cmd.args_set(args=simargs)

        self._process_override_data(
            om_cmd=om_cmd,
            override_file=result_file.parent / f"{result_file.stem}_override.txt",
            override_var=self._override_variables,
            override_sim=self._simulate_options_override,
        )

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
            resultfile: Optional[str | os.PathLike] = None,
            simargs: Optional[dict[str, Optional[str | dict[str, Any] | numbers.Number]]] = None,
    ) -> None:
        """Simulate the model according to simulation options.

        See setSimulationOptions().

        Args:
            resultfile: Path to a custom result file
            simargs: Dict with simulation runtime flags.

        Examples:
            mod.simulate()
            mod.simulate(resultfile="a.mat")
            mod.simulate(simargs={"noEventEmit": None, "noRestart": None, "override": "override": {"e": 0.3, "g": 10}})
        """

        if resultfile is None:
            # default result file generated by OM
            self._result_file = self.getWorkDirectory() / f"{self._model_name}_res.mat"
        elif isinstance(resultfile, OMPathABC):
            self._result_file = resultfile
        else:
            self._result_file = self._session.omcpath(resultfile)
            if not self._result_file.is_absolute():
                self._result_file = self.getWorkDirectory() / resultfile

        if not isinstance(self._result_file, OMPathABC):
            raise ModelicaSystemError(f"Invalid result file path: {self._result_file} - must be an OMCPath object!")

        om_cmd = self.simulate_cmd(
            result_file=self._result_file,
            simargs=simargs,
        )

        # delete resultfile ...
        if self._result_file.is_file():
            self._result_file.unlink()
        # ... run simulation ...
        cmd_definition = om_cmd.definition()
        try:
            returncode = cmd_definition.run()
        except ModelExecutionException as exc:
            raise ModelicaSystemError(f"Cannot execute model: {exc}") from exc
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

    @staticmethod
    def _prepare_input_data(
            input_kwargs: dict[str, Any],
    ) -> dict[str, str]:
        """
        Convert raw input to a structured dictionary {'key1': 'value1', 'key2': 'value2'}.
        """
        input_data: dict[str, str] = {}

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
                                          "sendExpression(expr=\"setParameterValue("
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
        """
        Return if the parameter defined by name is changeable (= non-structural; can be modified without the need to
        recompile the model).
        """
        q = self.getQuantities(name)
        if q[0]["changeable"] == "false":
            return False
        return True

    def setContinuous(
            self,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set continuous values.

        usage:
        >>> setContinuous(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setContinuous(**param)
        """
        inputdata = self._prepare_input_data(input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._continuous,
            datatype="continuous",
            overridedata=self._override_variables)

    def setParameters(
            self,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set parameter values

        usage:
        >>> setParameters(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setParameters(**param)
        """
        inputdata = self._prepare_input_data(input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._params,
            datatype="parameter",
            overridedata=self._override_variables)

    def setSimulationOptions(
            self,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set simulation options.

        usage:
        >>> setSimulationOptions(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setSimulationOptions(**param)
        """
        inputdata = self._prepare_input_data(input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._simulate_options,
            datatype="simulation-option",
            overridedata=self._simulate_options_override)

    def setLinearizationOptions(
            self,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set linearization options.

        usage:
        >>> setLinearizationOptions(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setLinearizationOptions(**param)
        """
        inputdata = self._prepare_input_data(input_kwargs=kwargs)

        return self._set_method_helper(
            inputdata=inputdata,
            classdata=self._linearization_options,
            datatype="Linearization-option",
            overridedata=None)

    def setOptimizationOptions(
            self,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        This method is used to set optimization options.

        usage:
        >>> setOptimizationOptions(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setOptimizationOptions(**param)
        """
        inputdata = self._prepare_input_data(input_kwargs=kwargs)

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
        This method is used to set input values.

        Compared to other set*() methods this is a special case as value could be a list of tuples - these are
        converted to a string in _prepare_input_data() and restored here via ast.literal_eval().

        usage:
        >>> setInputs(Name1="value1", Name2="value2")
        >>> param = {"Name1": "value1", "Name2": "value2"}
        >>> setInputs(**param)
        """
        inputdata = self._prepare_input_data(input_kwargs=kwargs)

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
                if not all(isinstance(item, tuple) for item in val_evaluated):
                    raise ModelicaSystemError("Value for setInput() must be in tuple format; "
                                              f"got {repr(val_evaluated)}")

                val_evaluated_checked: list[tuple[float, float]] = []
                for item in val_evaluated:
                    if len(item) != 2:
                        raise ModelicaSystemError(f"Value {repr(item)} of {repr(val_evaluated)} "
                                                  "is in incorrect format!")

                    try:
                        val_evaluated_checked.append((float(item[0]), float(item[1])))
                    except (ValueError, TypeError) as exc:
                        raise ModelicaSystemError("All elements of the input for setInput() should be convertible to "
                                                  "type Tuple[float, float] - "
                                                  f"found [{repr(item[0])}, {repr(item[1])}] with types "
                                                  f"[{type(item[0])}, {type(item[1])}]!") from exc

                    if item[0] < float(self._simulate_options["startTime"]):
                        raise ModelicaSystemError(f"Time value in {repr(item)} of {repr(val_evaluated)} is less "
                                                  "than the simulation start time")

                if val_evaluated_checked != sorted(val_evaluated_checked, key=lambda x: x[0]):
                    raise ModelicaSystemError("Time value should be in increasing order; "
                                              f"got {repr(val_evaluated_checked)}")

                self._inputs[key] = val_evaluated_checked
            else:
                raise ModelicaSystemError(f"Data cannot be evaluated for {repr(key)}: {repr(val)}")

        return True

    def _createCSVData(self, csvfile: Optional[OMPathABC] = None) -> OMPathABC:
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
                x=all_times,
                xp=signal[:, 0],  # times
                fp=signal[:, 1],  # values
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

    def linearize(
            self,
            lintime: Optional[float] = None,
            simargs: Optional[dict[str, Optional[str | dict[str, Any] | numbers.Number]]] = None,
    ) -> LinearizationResult:
        """Linearize the model according to linearization options.

        See setLinearizationOptions.

        Args:
            lintime: Override "stopTime" value.
            simargs: A dict with command line flags and possible options; example: "simargs={'csvInput': 'a.csv'}"

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
                "use ModelicaSystemOMC() to build the model first"
            )

        om_cmd = ModelExecutionCmd(
            runpath=self.getWorkDirectory(),
            cmd_local=self._session.model_execution_local,
            cmd_windows=self._session.model_execution_windows,
            cmd_prefix=self._session.model_execution_prefix(cwd=self.getWorkDirectory()),
            model_name=self._model_name,
        )

        self._process_override_data(
            om_cmd=om_cmd,
            override_file=self.getWorkDirectory() / f'{self._model_name}_override_linear.txt',
            override_var=self._override_variables,
            override_sim=self._linearization_options,
        )

        if self._inputs:
            for data in self._inputs.values():
                if data is not None:
                    for value in data:
                        if value[0] < float(self._simulate_options["startTime"]):
                            raise ModelicaSystemError('Input time value is less than simulation startTime')
            csvfile = self._createCSVData()
            om_cmd.arg_set(key="csvInput", val=csvfile.as_posix())

        if lintime is None:
            lintime = float(self._linearization_options["stopTime"])
        if (float(self._linearization_options["startTime"]) > lintime
                or float(self._linearization_options["stopTime"]) < lintime):
            raise ModelicaSystemError(f"Invalid linearisation time: {lintime=}; "
                                      f"expected value: {self._linearization_options['startTime']} "
                                      f"<= lintime <= {self._linearization_options['stopTime']}")
        om_cmd.arg_set(key="l", val=str(lintime))

        if simargs:
            om_cmd.args_set(args=simargs)

        # the file create by the model executable which contains the matrix and linear inputs, outputs and states
        linear_file = self.getWorkDirectory() / "linearized_model.py"
        linear_file.unlink(missing_ok=True)

        cmd_definition = om_cmd.definition()
        try:
            returncode = cmd_definition.run()
        except ModelExecutionException as exc:
            raise ModelicaSystemError(f"Cannot execute model: {exc}") from exc
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
                value_ast = ast.literal_eval(body_part.value)

                linear_data[target] = value_ast
        except (AttributeError, IndexError, ValueError, SyntaxError, TypeError) as ex:
            raise ModelicaSystemError(f"Error parsing linearization file {linear_file}: {ex}") from ex

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
