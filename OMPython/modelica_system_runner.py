# -*- coding: utf-8 -*-
"""
Definition of main class to run Modelica simulations - ModelicaSystem.
"""

import logging
import os
from typing import Optional

from OMPython.om_session_abc import (
    OMSessionABC,
)
from OMPython.om_session_runner import (
    OMSessionRunner,
)
from OMPython.modelica_system_abc import (
    ModelicaSystemABC,
    ModelicaSystemError,
)

# define logger using the current module name as ID
logger = logging.getLogger(__name__)


class ModelicaSystemRunner(ModelicaSystemABC):
    """
    Class to simulate a Modelica model using a pre-compiled model binary.

    Executes a pre-compiled Modelica executable and reads its initialization XML
    file without requiring an active OpenModelica Compiler (OMC) server connection.
    """

    def __init__(
            self,
            work_directory: Optional[str | os.PathLike] = None,
            session: Optional[OMSessionABC] = None,
    ) -> None:
        """Initialize ModelicaSystemRunner.

        Args:
            work_directory: Directory containing the compiled model executable and
                initialization XML file. If unspecified, a temporary directory is created.
            session: An instance of OMSessionRunner. If unspecified, a new
                OMSessionRunner is created.

        Raises:
            ModelicaSystemError: If the provided session is not an OMSessionRunner.
        """
        if session is None:
            session = OMSessionRunner()

        if not isinstance(session, OMSessionRunner):
            raise ModelicaSystemError("Only working if OMCsessionRunner is used!")

        super().__init__(
            work_directory=work_directory,
            session=session,
        )

    def setup(
            self,
            model_name: Optional[str] = None,
            variable_filter: Optional[str] = None,
    ) -> None:
        """Set up the runner for a pre-compiled model.

        Expects the model files to exist within the working directory:
        * Model executable ('<model_name>' or '<model_name>.exe'; on Windows,
          optionally '<model_name>.bat')
        * Model initialization file ('<model_name>_init.xml')

        Args:
            model_name: The name of the model to execute.
            variable_filter: Optional regex pattern for filtering result variables.

        Raises:
            ModelicaSystemError: If the instance already has a model configured,
                if model_name is missing, or if the model binary/XML is invalid.
        """

        if self._model_name is not None:
            raise ModelicaSystemError("Can not reuse this instance of ModelicaSystem "
                                      f"defined for {repr(self._model_name)}!")

        if model_name is None or not isinstance(model_name, str):
            raise ModelicaSystemError("A model name must be provided!")

        # set variables
        self._model_name = model_name  # Model class name
        self._variable_filter = variable_filter

        # test if the model can be executed
        self.check_model_executable()

        # read XML file
        xml_file = self._session.omcpath(self.getWorkDirectory()) / f"{self._model_name}_init.xml"
        self._xmlparse(xml_file=xml_file)
