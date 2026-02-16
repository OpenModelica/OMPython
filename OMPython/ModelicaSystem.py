# -*- coding: utf-8 -*-
"""
Definition of main class to run Modelica simulations - ModelicaSystem.
"""

import logging
import numbers
import os
import pathlib
from typing import Any, Optional
import warnings

import numpy as np

from OMPython.model_execution import (
    ModelExecutionCmd,
    ModelExecutionException,
)
from OMPython.om_session_abc import (
    OMPathABC,
)
from OMPython.om_session_omc import (
    OMCSessionLocal,
)
from OMPython.modelica_system_abc import (
    LinearizationResult,
    ModelicaSystemError,
)
from OMPython.modelica_system_omc import (
    ModelicaSystemOMC,
)
from OMPython.modelica_doe_omc import (
    ModelicaDoEOMC,
)

from OMPython.compatibility_v400 import (
    depreciated_class,
)

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


@depreciated_class(msg="Please use class ModelicaSystemOMC instead!")
class ModelicaSystem(ModelicaSystemOMC):
    """
    Compatibility class.
    """

    def __init__(
            self,
            fileName: Optional[str | os.PathLike | pathlib.Path] = None,
            modelName: Optional[str] = None,
            lmodel: Optional[list[str | tuple[str, str]]] = None,
            commandLineOptions: Optional[list[str]] = None,
            variableFilter: Optional[str] = None,
            customBuildDirectory: Optional[str | os.PathLike] = None,
            omhome: Optional[str] = None,
            omc_process: Optional[OMCSessionLocal] = None,
            build: bool = True,
    ) -> None:
        super().__init__(
            command_line_options=commandLineOptions,
            work_directory=customBuildDirectory,
            omhome=omhome,
            session=omc_process,
        )
        self.model(
            model_name=modelName,
            model_file=fileName,
            libraries=lmodel,
            variable_filter=variableFilter,
            build=build,
        )
        self._getconn = self._session

    def setCommandLineOptions(self, commandLineOptions: str):
        super().set_command_line_options(command_line_option=commandLineOptions)

    def simulate_cmd(  # type: ignore[override]
            self,
            result_file: OMPathABC,
            simflags: Optional[str] = None,
            simargs: Optional[dict[str, Optional[str | dict[str, Any] | numbers.Number]]] = None,
    ) -> ModelExecutionCmd:
        """
        Compatibility layer for OMPython v4.0.0 - keep simflags available and use ModelicaSystemCmd!
        """

        if simargs is None:
            simargs = {}

        if simflags is not None:
            simargs_extra = parse_simflags(simflags=simflags)
            simargs = simargs | simargs_extra

        return super().simulate_cmd(
            result_file=result_file,
            simargs=simargs,
        )

    def simulate(  # type: ignore[override]
            self,
            resultfile: Optional[str | os.PathLike] = None,
            simflags: Optional[str] = None,
            simargs: Optional[dict[str, Optional[str | dict[str, Any] | numbers.Number]]] = None,
    ) -> None:
        """
        Compatibility layer for OMPython v4.0.0 - keep simflags available and use ModelicaSystemCmd!
        """

        if simargs is None:
            simargs = {}

        if simflags is not None:
            simargs_extra = parse_simflags(simflags=simflags)
            simargs = simargs | simargs_extra

        return super().simulate(
            resultfile=resultfile,
            simargs=simargs,
        )

    def linearize(  # type: ignore[override]
            self,
            lintime: Optional[float] = None,
            simflags: Optional[str] = None,
            simargs: Optional[dict[str, Optional[str | dict[str, Any] | numbers.Number]]] = None,
    ) -> LinearizationResult:
        """
        Compatibility layer for OMPython v4.0.0 - keep simflags available and use ModelicaSystemCmd!
        """
        if simargs is None:
            simargs = {}

        if simflags is not None:
            simargs_extra = parse_simflags(simflags=simflags)
            simargs = simargs | simargs_extra

        return super().linearize(
            lintime=lintime,
            simargs=simargs,
        )

    @staticmethod
    def _set_compatibility_helper(
            pkey: str,
            args: Any,
            kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        input_args = []
        if len(args) == 1:
            input_args.append(args[0])
        elif pkey in kwargs:
            input_args.append(kwargs[pkey])

        # the code below is based on _prepare_input_data2()

        def prepare_str(str_in: str) -> dict[str, str]:
            str_in = str_in.replace(" ", "")
            key_val_list: list[str] = str_in.split("=")
            if len(key_val_list) != 2:
                raise ModelicaSystemError(f"Invalid 'key=value' pair: {str_in}")
            if len(key_val_list[0]) == 0:
                raise ModelicaSystemError(f"Empty key: {str_in}")

            input_data_from_str: dict[str, str] = {str(key_val_list[0]): str(key_val_list[1])}

            return input_data_from_str

        input_data: dict[str, str] = {}

        if input_args is None:
            return input_data

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
                input_arg_str: dict[str, str] = {}
                for key, val in input_arg.items():
                    if not isinstance(key, str) or len(key) == 0:
                        raise ModelicaSystemError(f"Invalid key for set*() functions: {repr(key)}")
                    input_arg_str[key] = str(val).replace(' ', '')
                input_data = input_data | input_arg_str
            else:
                raise ModelicaSystemError(f"Invalid input data type for set*() function: {type(input_arg)}!")

        return input_data

    def setContinuous(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        Compatibility wrapper for setContinuous() from OMPython v4.0.0

        Original definition:

        ```
        def setContinuous(
                self,
                cvals: str | list[str] | dict[str, Any],
        ) -> bool:
        ```
        """
        param = self._set_compatibility_helper(pkey='cvals', args=args, kwargs=kwargs)
        return super().setContinuous(**param)

    def setParameters(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        Compatibility wrapper for setParameters() from OMPython v4.0.0

        Original definition:

        ```
        def setParameters(
                self,
                pvals: str | list[str] | dict[str, Any],
        ) -> bool:
        ```
        """
        param = self._set_compatibility_helper(pkey='pvals', args=args, kwargs=kwargs)
        return super().setParameters(**param)

    def setOptimizationOptions(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        Compatibility wrapper for setOptimizationOptions() from OMPython v4.0.0

        Original definition:

        ```
        def setOptimizationOptions(
                self,
                optimizationOptions: str | list[str] | dict[str, Any],
        ) -> bool:
        ```
        """
        param = self._set_compatibility_helper(pkey='optimizationOptions', args=args, kwargs=kwargs)
        return super().setOptimizationOptions(**param)

    def setInputs(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        Compatibility wrapper for setInputs() from OMPython v4.0.0

        Original definition:

        ```
        def setInputs(
                self,
                name: str | list[str] | dict[str, Any],
        ) -> bool:
        ```
        """
        param = self._set_compatibility_helper(pkey='name', args=args, kwargs=kwargs)
        return super().setInputs(**param)

    def setSimulationOptions(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        Compatibility wrapper for setSimulationOptions() from OMPython v4.0.0

        Original definition:

        ```
        def setSimulationOptions(
                self,
                simOptions: str | list[str] | dict[str, Any],
        ) -> bool:
        ```
        """
        param = self._set_compatibility_helper(pkey='simOptions', args=args, kwargs=kwargs)
        return super().setSimulationOptions(**param)

    def setLinearizationOptions(
            self,
            *args: Any,
            **kwargs: dict[str, Any],
    ) -> bool:
        """
        Compatibility wrapper for setLinearizationOptions() from OMPython v4.0.0

        Original definition:

        ```
        def setLinearizationOptions(
                self,
                linearizationOptions: str | list[str] | dict[str, Any],
        ) -> bool:
        ```
        """
        param = self._set_compatibility_helper(pkey='linearizationOptions', args=args, kwargs=kwargs)
        return super().setLinearizationOptions(**param)

    def getContinuous(
            self,
            names: Optional[str | list[str]] = None,
    ):
        """
        Compatibility wrapper for getContinuous() from OMPython v4.0.0

        If no model simulation was run (self._simulated == False), the return value should be converted to str.
        """
        retval = super().getContinuous(names=names)
        if self._simulated:
            return retval

        if isinstance(retval, dict):
            retval2: dict = {}
            for key, val in retval.items():
                if np.isnan(val):
                    retval2[key] = None
                else:
                    retval2[key] = str(val)
            return retval2
        if isinstance(retval, list):
            retval3: list[str | None] = []
            for val in retval:
                if np.isnan(val):
                    retval3.append(None)
                else:
                    retval3.append(str(val))
            return retval3

        raise ModelicaSystemError("Invalid data!")

    def getOutputs(
            self,
            names: Optional[str | list[str]] = None,
    ):
        """
        Compatibility wrapper for getOutputs() from OMPython v4.0.0

        If no model simulation was run (self._simulated == False), the return value should be converted to str.
        """
        retval = super().getOutputs(names=names)
        if self._simulated:
            return retval

        if isinstance(retval, dict):
            retval2: dict = {}
            for key, val in retval.items():
                if np.isnan(val):
                    retval2[key] = None
                else:
                    retval2[key] = str(val)
            return retval2
        if isinstance(retval, list):
            retval3: list[str | None] = []
            for val in retval:
                if np.isnan(val):
                    retval3.append(None)
                else:
                    retval3.append(str(val))
            return retval3

        raise ModelicaSystemError("Invalid data!")


@depreciated_class(msg="Please use class ModelicaDoEOMC instead!")
class ModelicaSystemDoE(ModelicaDoEOMC):
    """
    Compatibility class.
    """


@depreciated_class(msg="Please use class ModelExecutionCmd instead!")
class ModelicaSystemCmd(ModelExecutionCmd):
    """
    Compatibility class; not much content.

    Missing definitions:
    * get_exe() - see self.definition.cmd_model_executable
    * get_cmd() - use self.get_cmd_args() or self.definition().get_cmd()
    * run() - use self.definition().run()
    """


def parse_simflags(simflags: str) -> dict[str, Optional[str | dict[str, Any] | numbers.Number]]:
    """
    Parse a simflag definition; this is deprecated!

    The return data can be used as input for self.args_set().
    """
    warnings.warn(
        message="The argument 'simflags' is depreciated and will be removed in future versions; "
                "please use 'simargs' instead",
        category=DeprecationWarning,
        stacklevel=2,
    )

    simargs: dict[str, Optional[str | dict[str, Any] | numbers.Number]] = {}

    args = [s for s in simflags.split(' ') if s]
    for arg in args:
        if arg[0] != '-':
            raise ModelExecutionException(f"Invalid simulation flag: {arg}")
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
                    raise ModelExecutionException(f"Invalid value for '-override': {override}")
                if kv[0]:
                    try:
                        override_dict[kv[0]] = kv[1]
                    except (KeyError, IndexError) as ex:
                        raise ModelExecutionException(f"Invalid value for '-override': {override}") from ex

            simargs[parts[0]] = override_dict

    return simargs
