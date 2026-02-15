# -*- coding: utf-8 -*-
"""
Definition of main class to run Modelica simulations - ModelicaSystem.
"""

import logging
import os
import pathlib
import platform
from typing import Any, Optional

import numpy as np

from OMPython.model_execution import (
    ModelExecutionCmd,
    ModelExecutionException,
)
from OMPython.om_session_omc import (
    OMCSessionLocal,
)
from OMPython.modelica_system_abc import (
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

    def _set_compatibility_helper(
            self,
            pkey: str,
            args: Any,
            kwargs: dict[str, Any],
    ) -> Any:
        param = None
        if len(args) == 1:
            param = args[0]
        if param is None and pkey in kwargs:
            param = kwargs[pkey]

        return param

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
        if param is None:
            raise ModelicaSystemError("Invalid input for setContinuous() (v4.0.0 compatibility mode).")

        return super().setContinuous(param)

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
        if param is None:
            raise ModelicaSystemError("Invalid input for setParameters() (v4.0.0 compatibility mode).")

        return super().setParameters(param)

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
        if param is None:
            raise ModelicaSystemError("Invalid input for setOptimizationOptions() (v4.0.0 compatibility mode).")

        return super().setOptimizationOptions(param)

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
        if param is None:
            raise ModelicaSystemError("Invalid input for setInputs() (v4.0.0 compatibility mode).")

        return super().setInputs(param)

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
        if param is None:
            raise ModelicaSystemError("Invalid input for setSimulationOptions() (v4.0.0 compatibility mode).")

        return super().setSimulationOptions(param)

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
        if param is None:
            raise ModelicaSystemError("Invalid input for setLinearizationOptions() (v4.0.0 compatibility mode).")

        return super().setLinearizationOptions(param)

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
    Compatibility class; in the new version it is renamed as ModelExecutionCmd.
    """

    def __init__(
            self,
            runpath: pathlib.Path,
            modelname: str,
            timeout: float = 10.0,
    ) -> None:
        super().__init__(
            runpath=runpath,
            timeout=timeout,
            cmd_prefix=[],
            model_name=modelname,
        )

    def get_exe(self) -> pathlib.Path:
        """Get the path to the compiled model executable."""

        path_run = pathlib.Path(self._runpath)
        if platform.system() == "Windows":
            path_exe = path_run / f"{self._model_name}.exe"
        else:
            path_exe = path_run / self._model_name

        if not path_exe.exists():
            raise ModelicaSystemError(f"Application file path not found: {path_exe}")

        return path_exe

    def get_cmd(self) -> list:
        """
        Get a list with the path to the executable and all command line args.

        This can later be used as an argument for subprocess.run().
        """

        cmdl = [self.get_exe().as_posix()] + self.get_cmd_args()

        return cmdl

    def run(self) -> int:
        cmd_definition = self.definition()
        try:
            returncode = cmd_definition.run()
        except ModelExecutionException as exc:
            raise ModelicaSystemError(f"Cannot execute model: {exc}") from exc
        return returncode
