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
    """

    def __init__(
            self,
            work_directory: Optional[str | os.PathLike] = None,
            session: Optional[OMSessionABC] = None,
    ) -> None:
        if session is None:
            session = OMSessionRunner()

        if not isinstance(session, OMSessionRunner):
            raise ModelicaSystemError("Only working if OMCsessionDummy is used!")

        super().__init__(
            work_directory=work_directory,
            session=session,
        )

    def setup(
            self,
            model_name: Optional[str] = None,
            variable_filter: Optional[str] = None,
    ) -> None:
        """
        Needed definitions to set up the runner class. This class expects the model (defined by model_name) to exists
        within the working directory. At least two files are needed:

        * model executable (as '<model_name>' or '<model_name>.exe'; in case of Windows additional '<model_name>.bat'
          is expected to evaluate the path to needed dlls
        * the model initialization file (as '<model_name>_init.xml')
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
