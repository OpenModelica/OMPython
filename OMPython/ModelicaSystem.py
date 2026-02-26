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

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


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

    def setContinuous(  # type: ignore[override]
            self,
            cvals: str | list[str] | dict[str, Any],
    ) -> bool:
        if isinstance(cvals, dict):
            return super().setContinuous(**cvals)
        raise ModelicaSystemError("Only dict input supported for setContinuous()")

    def setParameters(  # type: ignore[override]
            self,
            pvals: str | list[str] | dict[str, Any],
    ) -> bool:
        if isinstance(pvals, dict):
            return super().setParameters(**pvals)
        raise ModelicaSystemError("Only dict input supported for setParameters()")

    def setOptimizationOptions(  # type: ignore[override]
            self,
            optimizationOptions: str | list[str] | dict[str, Any],
    ) -> bool:
        if isinstance(optimizationOptions, dict):
            return super().setOptimizationOptions(**optimizationOptions)
        raise ModelicaSystemError("Only dict input supported for setOptimizationOptions()")

    def setInputs(  # type: ignore[override]
            self,
            name: str | list[str] | dict[str, Any],
    ) -> bool:
        if isinstance(name, dict):
            return super().setInputs(**name)
        raise ModelicaSystemError("Only dict input supported for setInputs()")

    def setSimulationOptions(  # type: ignore[override]
            self,
            simOptions: str | list[str] | dict[str, Any],
    ) -> bool:
        if isinstance(simOptions, dict):
            return super().setSimulationOptions(**simOptions)
        raise ModelicaSystemError("Only dict input supported for setSimulationOptions()")

    def setLinearizationOptions(  # type: ignore[override]
            self,
            linearizationOptions: str | list[str] | dict[str, Any],
    ) -> bool:
        if isinstance(linearizationOptions, dict):
            return super().setLinearizationOptions(**linearizationOptions)
        raise ModelicaSystemError("Only dict input supported for setLinearizationOptions()")

    def getContinuous(
            self,
            names: Optional[str | list[str]] = None,
    ):
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

        raise ModelExecutionException("Invalid data!")

    def getOutputs(
            self,
            names: Optional[str | list[str]] = None,
    ):
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

        raise ModelExecutionException("Invalid data!")


class ModelicaSystemDoE(ModelicaDoEOMC):
    """
    Compatibility class.
    """


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
        """Get a list with the path to the executable and all command line args.

        This can later be used as an argument for subprocess.run().
        """

        cmdl = [self.get_exe().as_posix()] + self.get_cmd_args()

        return cmdl

    def run(self):
        cmd_definition = self.definition()
        return cmd_definition.run()
