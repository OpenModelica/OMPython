# -*- coding: utf-8 -*-
"""
Definition of main class to run Modelica simulations - ModelicaSystem.
"""

import logging
import numbers
import os
from typing import Optional, Tuple

from OMPython.modelica_system_abc import (
    ModelicaSystemABC,
    ModelicaSystemError,
)
from OMPython.modelica_doe_abc import (
    ModelicaDoEABC,
)

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaDoERunner(ModelicaDoEABC):
    """
    Class to run DoEs based on a (Open)Modelica model using ModelicaSystemRunner

    The example is the same as defined for ModelicaDoEABC
    """

    def __init__(
            self,
            # ModelicaSystem definition to use
            mod: ModelicaSystemABC,
            # simulation specific input
            # TODO: add more settings (simulation options, input options, ...)
            simargs: Optional[dict[str, Optional[str | dict[str, str] | numbers.Number]]] = None,
            # DoE specific inputs
            resultpath: Optional[str | os.PathLike] = None,
            parameters: Optional[dict[str, list[str] | list[int] | list[float]]] = None,
    ) -> None:
        if not isinstance(mod, ModelicaSystemABC):
            raise ModelicaSystemError(f"Invalid definition for ModelicaSystem*: {type(mod)}!")

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
        if len(param_structure.keys()) > 0:
            raise ModelicaSystemError(f"{self.__class__.__name__} can not handle structure parameters as it uses a "
                                      "pre-compiled binary of model.")

        return {}
