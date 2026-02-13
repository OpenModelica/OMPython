# -*- coding: utf-8 -*-
"""
Definition of main class to run Modelica simulations - ModelicaSystem.
"""

import logging
import numbers
import os
from typing import Any, Optional, Tuple

import numpy as np

from OMPython.om_session_abc import (
    OMPathABC,
)
from OMPython.modelica_system_abc import (
    ModelicaSystemError,
)
from OMPython.modelica_system_omc import (
    ModelicaSystemOMC,
)
from OMPython.modelica_doe_abc import (
    ModelicaDoEABC,
)

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaDoEOMC(ModelicaDoEABC):
    """
    Class to run DoEs based on a (Open)Modelica model using ModelicaSystemOMC

    The example is the same as defined for ModelicaDoEABC
    """

    def __init__(
            self,
            # ModelicaSystem definition to use
            mod: ModelicaSystemOMC,
            # simulation specific input
            # TODO: add more settings (simulation options, input options, ...)
            simargs: Optional[dict[str, Optional[str | dict[str, str] | numbers.Number]]] = None,
            # DoE specific inputs
            resultpath: Optional[str | os.PathLike] = None,
            parameters: Optional[dict[str, list[str] | list[int] | list[float]]] = None,
    ) -> None:

        if not isinstance(mod, ModelicaSystemOMC):
            raise ModelicaSystemError(f"Invalid definition for mod: {type(mod)} - expect ModelicaSystemOMC!")

        super().__init__(
            mod=mod,
            simargs=simargs,
            resultpath=resultpath,
            parameters=parameters,
        )

    def _prepare_structure_parameters(
            self,
            idx_pc_structure: int,
            pc_structure: Tuple,
            param_structure: dict[str, list[str] | list[int] | list[float]],
    ) -> dict[str, str | int | float]:
        build_dir = self._resultpath / f"DOE_{idx_pc_structure:09d}"
        build_dir.mkdir()
        self._mod.setWorkDirectory(work_directory=build_dir)

        # need to repeat this check to make the linters happy
        if not isinstance(self._mod, ModelicaSystemOMC):
            raise ModelicaSystemError(f"Invalid definition for mod: {type(self._mod)} - expect ModelicaSystemOMC!")

        sim_param_structure = {}
        for idx_structure, pk_structure in enumerate(param_structure.keys()):
            sim_param_structure[pk_structure] = pc_structure[idx_structure]

            pk_value = pc_structure[idx_structure]
            if isinstance(pk_value, str):
                pk_value_str = self.get_session().escape_str(pk_value)
                expr = f"setParameterValue({self._model_name}, {pk_structure}, \"{pk_value_str}\")"
            elif isinstance(pk_value, bool):
                pk_value_bool_str = "true" if pk_value else "false"
                expr = f"setParameterValue({self._model_name}, {pk_structure}, {pk_value_bool_str});"
            else:
                expr = f"setParameterValue({self._model_name}, {pk_structure}, {pk_value})"
            res = self._mod.sendExpression(expr=expr)
            if not res:
                raise ModelicaSystemError(f"Cannot set structural parameter {self._model_name}.{pk_structure} "
                                          f"to {pk_value} using {repr(expr)}")

        self._mod.buildModel()

        return sim_param_structure

    def get_doe_solutions(
            self,
            var_list: Optional[list] = None,
    ) -> Optional[tuple[str] | dict[str, dict[str, np.ndarray]]]:
        """
        Wrapper for doe_get_solutions()
        """
        if not isinstance(self._mod, ModelicaSystemOMC):
            raise ModelicaSystemError(f"Invalid definition for mod: {type(self._mod)} - expect ModelicaSystemOMC!")

        return doe_get_solutions(
            msomc=self._mod,
            resultpath=self._resultpath,
            doe_def=self.get_doe_definition(),
            var_list=var_list,
        )


def doe_get_solutions(
        msomc: ModelicaSystemOMC,
        resultpath: OMPathABC,
        doe_def: Optional[dict] = None,
        var_list: Optional[list] = None,
) -> Optional[tuple[str] | dict[str, dict[str, np.ndarray]]]:
    """
    Get all solutions of the DoE run. The following return values are possible:

    * A list of variables if val_list == None

    * The Solutions as dict[str, pd.DataFrame] if a value list (== val_list) is defined.

    The following code snippet can be used to convert the solution data for each run to a pandas dataframe:

    ```
    import pandas as pd

    doe_sol = doe_mod.get_doe_solutions()
    for key in doe_sol:
        data = doe_sol[key]['data']
        if data:
            doe_sol[key]['df'] = pd.DataFrame.from_dict(data=data)
        else:
            doe_sol[key]['df'] = None
    ```

    """
    if not isinstance(doe_def, dict):
        return None

    if len(doe_def) == 0:
        raise ModelicaSystemError("No result files available - all simulations did fail?")

    sol_dict: dict[str, dict[str, Any]] = {}
    for resultfilename in doe_def:
        resultfile = resultpath / resultfilename

        sol_dict[resultfilename] = {}

        if not doe_def[resultfilename][ModelicaDoEABC.DICT_RESULT_AVAILABLE]:
            msg = f"No result file available for {resultfilename}"
            logger.warning(msg)
            sol_dict[resultfilename]['msg'] = msg
            sol_dict[resultfilename]['data'] = {}
            continue

        if var_list is None:
            var_list_row = list(msomc.getSolutions(resultfile=resultfile))
        else:
            var_list_row = var_list

        try:
            sol = msomc.getSolutions(varList=var_list_row, resultfile=resultfile)
            sol_data = {var: sol[idx] for idx, var in enumerate(var_list_row)}
            sol_dict[resultfilename]['msg'] = 'Simulation available'
            sol_dict[resultfilename]['data'] = sol_data
        except ModelicaSystemError as ex:
            msg = f"Error reading solution for {resultfilename}: {ex}"
            logger.warning(msg)
            sol_dict[resultfilename]['msg'] = msg
            sol_dict[resultfilename]['data'] = {}

    return sol_dict
