# -*- coding: utf-8 -*-
"""
Definition of main class to run Modelica simulations - ModelicaSystem.
"""

import logging
import os
import pathlib
import textwrap
from typing import Any, cast, Optional

import numpy as np

from OMPython.om_session_abc import (
    OMPathABC,
    OMSessionABC,
    OMSessionException,
)
from OMPython.om_session_omc import (
    OMCSessionLocal,
)
from OMPython.modelica_system_abc import (
    ModelicaSystemABC,
    ModelicaSystemError,
)

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaSystemOMC(ModelicaSystemABC):
    """
    Class to simulate a Modelica model using OpenModelica via OMCSession.
    """

    def __init__(
            self,
            command_line_options: Optional[list[str]] = None,
            work_directory: Optional[str | os.PathLike] = None,
            omhome: Optional[str] = None,
            session: Optional[OMSessionABC] = None,
    ) -> None:
        """Create a ModelicaSystem instance. To define the model use model() or convertFmu2Mo().

        Args:
            command_line_options: List with extra command line options as elements. The list elements are
              provided to omc via setCommandLineOptions(). If set, the default values will be overridden.
              To disable any command line options, use an empty list.
            work_directory: Path to a directory to be used for temporary
              files like the model executable. If left unspecified, a tmp
              directory will be created.
            omhome: path to OMC to be used when creating the OMC session (see OMCSession).
            session: definition of a (local) OMC session to be used. If
              unspecified, a new local session will be created.
        """

        if session is None:
            session = OMCSessionLocal(omhome=omhome)

        super().__init__(
            session=session,
            work_directory=work_directory,
        )

        # set commandLineOptions using default values or the user defined list
        if command_line_options is None:
            # set default command line options to improve the performance of linearization and to avoid recompilation if
            # the simulation executable is reused in linearize() via the runtime flag '-l'
            command_line_options = [
                "--linearizationDumpLanguage=python",
                "--generateSymbolicLinearization",
            ]
        for opt in command_line_options:
            self.set_command_line_options(command_line_option=opt)

    def model(
            self,
            model_name: Optional[str] = None,
            model_file: Optional[str | os.PathLike] = None,
            libraries: Optional[list[str | tuple[str, str]]] = None,
            variable_filter: Optional[str] = None,
            build: bool = True,
    ) -> None:
        """Load and build a Modelica model.

        This method loads the model file and builds it if requested (build == True).

        Args:
            model_file: Path to the model file. Either absolute or relative to
              the current working directory.
            model_name: The name of the model class. If it is contained within
              a package, "PackageName.ModelName" should be used.
            libraries: List of libraries to be loaded before the model itself is
              loaded. Two formats are supported for the list elements:
              lmodel=["Modelica"] for just the library name
              and lmodel=[("Modelica","3.2.3")] for specifying both the name
              and the version.
            variable_filter: A regular expression. Only variables fully
              matching the regexp will be stored in the result file.
              Leaving it unspecified is equivalent to ".*".
            build: Boolean controlling whether the model should be
              built when constructor is called. If False, the constructor
              simply loads the model without compiling.

        Examples:
            mod = ModelicaSystemOMC()
            # and then one of the lines below
            mod.model(name="modelName", file="ModelicaModel.mo", )
            mod.model(name="modelName", file="ModelicaModel.mo", libraries=["Modelica"])
            mod.model(name="modelName", file="ModelicaModel.mo", libraries=[("Modelica","3.2.3"), "PowerSystems"])
        """

        if self._model_name is not None:
            raise ModelicaSystemError("Can not reuse this instance of ModelicaSystem "
                                      f"defined for {repr(self._model_name)}!")

        if model_name is None or not isinstance(model_name, str):
            raise ModelicaSystemError("A model name must be provided!")

        if libraries is None:
            libraries = []

        if not isinstance(libraries, list):
            raise ModelicaSystemError(f"Invalid input type for libraries: {type(libraries)} - list expected!")

        # set variables
        self._model_name = model_name  # Model class name
        self._libraries = libraries  # may be needed if model is derived from other model
        self._variable_filter = variable_filter

        if self._libraries:
            self._loadLibrary(libraries=self._libraries)

        self._file_name = None
        if model_file is not None:
            file_path = pathlib.Path(model_file)
            # special handling for OMCProcessLocal - consider a relative path
            if isinstance(self._session, OMCSessionLocal) and not file_path.is_absolute():
                file_path = pathlib.Path.cwd() / file_path
            if not file_path.is_file():
                raise IOError(f"Model file {file_path} does not exist!")

            self._file_name = self.getWorkDirectory() / file_path.name
            if (isinstance(self._session, OMCSessionLocal)
                    and file_path.as_posix() == self._file_name.as_posix()):
                pass
            elif self._file_name.is_file():
                raise IOError(f"Simulation model file {self._file_name} exist - not overwriting!")
            else:
                content = file_path.read_text(encoding='utf-8')
                self._file_name.write_text(content)

        if self._file_name is not None:
            self._loadFile(fileName=self._file_name)

        if build:
            self.buildModel(variable_filter)

    def set_command_line_options(self, command_line_option: str):
        """
        Set the provided command line option via OMC setCommandLineOptions().
        """
        expr = f'setCommandLineOptions("{command_line_option}")'
        self.sendExpression(expr=expr)

    def _loadFile(self, fileName: OMPathABC):
        # load file
        self.sendExpression(expr=f'loadFile("{fileName.as_posix()}")')

    # for loading file/package, loading model and building model
    def _loadLibrary(self, libraries: list):
        # load Modelica standard libraries or Modelica files if needed
        for element in libraries:
            if element is not None:
                if isinstance(element, str):
                    if element.endswith(".mo"):
                        api_call = "loadFile"
                    else:
                        api_call = "loadModel"
                    self._requestApi(apiName=api_call, entity=element)
                elif isinstance(element, tuple):
                    if not element[1]:
                        expr_load_lib = f"loadModel({element[0]})"
                    else:
                        expr_load_lib = f'loadModel({element[0]}, {{"{element[1]}"}})'
                    self.sendExpression(expr=expr_load_lib)
                else:
                    raise ModelicaSystemError("loadLibrary() failed, Unknown type detected: "
                                              f"{element} is of type {type(element)}, "
                                              "The following patterns are supported:\n"
                                              '1)["Modelica"]\n'
                                              '2)[("Modelica","3.2.3"), "PowerSystems"]\n')

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

        build_model_result = self._requestApi(apiName="buildModel", entity=self._model_name, properties=var_filter)
        logger.debug("OM model build result: %s", build_model_result)

        # check if the executable exists ...
        self.check_model_executable()

        xml_file = self._session.omcpath(build_model_result[0]).parent / build_model_result[1]
        self._xmlparse(xml_file=xml_file)

    def sendExpression(self, expr: str, parsed: bool = True) -> Any:
        """
        Wrapper for OMCSession.sendExpression().
        """
        try:
            retval = self._session.sendExpression(expr=expr, parsed=parsed)
        except OMSessionException as ex:
            raise ModelicaSystemError(f"Error executing {repr(expr)}: {ex}") from ex

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
            expr = f'{apiName}({entity}, {properties})'
        elif entity is not None and properties is None:
            if apiName in ("loadFile", "importFMU"):
                expr = f'{apiName}("{entity}")'
            else:
                expr = f'{apiName}({entity})'
        else:
            expr = f'{apiName}()'

        return self.sendExpression(expr=expr)

    def getContinuousFinal(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, np.float64] | list[np.float64]:
        """
        Get (final) values of continuous signals (at stopTime).

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
            >>> mod.getContinuousFinal()
            {'x': np.float64(0.68), 'der(x)': np.float64(-0.24), 'y': np.float64(-0.24)}
            >>> mod.getContinuousFinal("x")
            [np.float64(0.68)]
            >>> mod.getContinuousFinal(["y","x"])
            [np.float64(-0.24), np.float64(0.68)]
        """
        if not self._simulated:
            raise ModelicaSystemError("Please use getContinuousInitial() before the simulation was started!")

        def get_continuous_solution(name_list: list[str]) -> None:
            for name in name_list:
                if name in self._continuous:
                    value = self.getSolutions(name)
                    self._continuous[name] = np.float64(value[0][-1])
                else:
                    raise KeyError(f"{names} is not continuous")

        if names is None:
            get_continuous_solution(name_list=list(self._continuous.keys()))
            return self._continuous

        if isinstance(names, str):
            get_continuous_solution(name_list=[names])
            return [self._continuous[names]]

        if isinstance(names, list):
            get_continuous_solution(name_list=names)
            values = []
            for name in names:
                values.append(self._continuous[name])
            return values

        raise ModelicaSystemError("Unhandled input for getContinousFinal()")

    def getContinuous(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, np.float64] | list[np.float64]:
        """Get values of continuous signals.

        If called before simulate(), the initial values are returned.
        If called after simulate(), the final values (at stopTime) are returned.
        The return format is always numpy.float64.

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
            >>> mod.getContinuous(["y","x"])
            [np.float64(-0.24), np.float64(0.68)]
        """
        if not self._simulated:
            return self.getContinuousInitial(names=names)

        return self.getContinuousFinal(names=names)

    def getOutputsFinal(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, np.float64] | list[np.float64]:
        """Get (final) values of output signals (at stopTime).

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
            >>> mod.getOutputsFinal()
            {'out1': np.float64(-0.1234), 'out2': np.float64(2.1)}
            >>> mod.getOutputsFinal("out1")
            [np.float64(-0.1234)]
            >>> mod.getOutputsFinal(["out1","out2"])
            [np.float64(-0.1234), np.float64(2.1)]
        """
        if not self._simulated:
            raise ModelicaSystemError("Please use getOuputsInitial() before the simulation was started!")

        def get_outputs_solution(name_list: list[str]) -> None:
            for name in name_list:
                if name in self._outputs:
                    value = self.getSolutions(name)
                    self._outputs[name] = np.float64(value[0][-1])
                else:
                    raise KeyError(f"{names} is not a valid output")

        if names is None:
            get_outputs_solution(name_list=list(self._outputs.keys()))
            return self._outputs

        if isinstance(names, str):
            get_outputs_solution(name_list=[names])
            return [self._outputs[names]]

        if isinstance(names, list):
            get_outputs_solution(name_list=names)
            values = []
            for name in names:
                values.append(self._outputs[name])
            return values

        raise ModelicaSystemError("Unhandled input for getOutputs()")

    def getOutputs(
            self,
            names: Optional[str | list[str]] = None,
    ) -> dict[str, np.float64] | list[np.float64]:
        """Get values of output signals.

        If called before simulate(), the initial values are returned.
        If called after simulate(), the final values (at stopTime) are returned.
        The return format is always numpy.float64.

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
            return self.getOutputsInitial(names=names)

        return self.getOutputsFinal(names=names)

    def plot(
            self,
            plotdata: str,
            resultfile: Optional[str | os.PathLike] = None,
    ) -> None:
        """
        Plot a variable using OMC; this will work for local OMC usage only (OMCProcessLocal). The reason is that the
        plot is created by OMC which needs access to the local display. This is not the case for docker and WSL.
        """

        if not isinstance(self._session, OMCSessionLocal):
            raise ModelicaSystemError("Plot is using the OMC plot functionality; "
                                      "thus, it is only working if OMC is running locally!")

        if resultfile is not None:
            plot_result_file = self._session.omcpath(resultfile)
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
    ) -> tuple[str, ...] | np.ndarray:
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
            result_file = self._session.omcpath(resultfile)

        # check if the result file exits
        if not result_file.is_file():
            raise ModelicaSystemError(f"Result file does not exist {result_file.as_posix()}")

        # get absolute path
        result_file = result_file.absolute()

        result_vars = self.sendExpression(expr=f'readSimulationResultVars("{result_file.as_posix()}")')
        self.sendExpression(expr="closeSimulationResultFile()")
        if varList is None:
            var_list = [str(var) for var in result_vars]
            return tuple(var_list)

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
        res = self.sendExpression(expr=f'readSimulationResult("{result_file.as_posix()}",{{{variables}}})')
        np_res = np.array(res)
        self.sendExpression(expr="closeSimulationResultFile()")
        return np_res

    def convertMo2Fmu(
            self,
            version: str = "2.0",
            fmuType: str = "me_cs",
            fileNamePrefix: Optional[str] = None,
            includeResources: bool = True,
    ) -> OMPathABC:
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

        if fileNamePrefix is None:
            if self._model_name is None:
                fileNamePrefix = "<default>"
            else:
                fileNamePrefix = self._model_name
        include_resources_str = "true" if includeResources else "false"

        properties = (f'version="{version}", fmuType="{fmuType}", '
                      f'fileNamePrefix="{fileNamePrefix}", includeResources={include_resources_str}')
        fmu = self._requestApi(apiName='buildModelFMU', entity=self._model_name, properties=properties)
        fmu_path = self._session.omcpath(fmu)

        # report proper error message
        if not fmu_path.is_file():
            raise ModelicaSystemError(f"Missing FMU file: {fmu_path.as_posix()}")

        return fmu_path

    # to convert FMU to Modelica model
    def convertFmu2Mo(
            self,
            fmu: os.PathLike,
    ) -> OMPathABC:
        """
        In order to load FMU, at first it needs to be translated into Modelica model. This method is used to generate
        Modelica model from the given FMU. It generates "fmuName_me_FMU.mo".
        Currently, it only supports Model Exchange conversion.
        usage
        >>> convertFmu2Mo("c:/BouncingBall.Fmu")
        """

        fmu_path = self._session.omcpath(fmu)

        if not fmu_path.is_file():
            raise ModelicaSystemError(f"Missing FMU file: {fmu_path.as_posix()}")

        filename = self._requestApi(apiName='importFMU', entity=fmu_path.as_posix())
        if not isinstance(filename, str):
            raise ModelicaSystemError(f"Invalid return value for the FMU filename: {filename}")
        filepath = self.getWorkDirectory() / filename

        # report proper error message
        if not filepath.is_file():
            raise ModelicaSystemError(f"Missing file {filepath.as_posix()}")

        self.model(
            model_name=f"{fmu_path.stem}_me_FMU",
            model_file=filepath,
        )

        return filepath

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
        properties = ','.join(f"{key}={val}" for key, val in self._optimization_options.items())
        self.set_command_line_options("-g=Optimica")
        retval = self._requestApi(apiName='optimize', entity=self._model_name, properties=properties)
        retval = cast(dict, retval)
        return retval
