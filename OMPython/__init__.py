# -*- coding: utf-8 -*-
"""
OMPython is a Python interface to OpenModelica.
To get started on a local OMC server, create an OMCSessionLocal object:

```
import OMPython
omc = OMPython.OMCSessionLocal()
omc.sendExpression("getVersion()")
```

"""

from OMPython.model_execution import (
    ModelExecutionCmd,
    ModelExecutionData,
    ModelExecutionException,
)
from OMPython.om_session_abc import (
    OMPathABC,
    OMSessionABC,
    OMSessionException,
)
from OMPython.om_session_omc import (
    OMCPath,
    OMCSessionABC,
    OMCSessionDocker,
    OMCSessionDockerContainer,
    OMCSessionLocal,
    OMCSessionPort,
    OMCSessionWSL,
)
from OMPython.om_session_runner import (
    OMPathRunnerBash,
    OMPathRunnerLocal,
    OMSessionRunner,
)
from OMPython.modelica_system_abc import (
    LinearizationResult,
    ModelicaSystemABC,
    ModelicaSystemError,
)
from OMPython.modelica_system_omc import (
    ModelicaSystemOMC,
)
from OMPython.modelica_system_runner import (
    ModelicaSystemRunner,
)
from OMPython.modelica_doe_abc import (
    ModelicaDoEABC,
)
from OMPython.modelica_doe_omc import (
    doe_get_solutions,

    ModelicaDoEOMC,
)
from OMPython.modelica_doe_runner import (
    ModelicaDoERunner,
)

# global names imported if import 'from OMPython import *' is used
__all__ = [
    'doe_get_solutions',

    'LinearizationResult',

    'ModelExecutionCmd',
    'ModelExecutionData',
    'ModelExecutionException',

    'ModelicaDoEABC',
    'ModelicaDoEOMC',
    'ModelicaDoERunner',
    'ModelicaSystemABC',
    'ModelicaSystemError',
    'ModelicaSystemOMC',
    'ModelicaSystemRunner',

    'OMPathABC',
    'OMSessionABC',
    'OMSessionException',

    'OMCPath',
    'OMCSessionABC',
    'OMCSessionDocker',
    'OMCSessionDockerContainer',
    'OMCSessionLocal',
    'OMCSessionPort',
    'OMCSessionWSL',

    'OMPathRunnerBash',
    'OMPathRunnerLocal',
    'OMSessionRunner',
]
