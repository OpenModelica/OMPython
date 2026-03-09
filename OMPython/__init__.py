# -*- coding: utf-8 -*-
"""
OMPython is a Python interface to OpenModelica.
To get started on a local OMC server, create an OMCSessionLocal object:

```
import OMPython
omc = OMPython.OMCSessionLocal()
omc.sendExpression("command")
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

from OMPython.ModelicaSystem import (
    LinearizationResult,
    ModelicaSystem,
    ModelicaSystemOMC,
    ModelicaSystemDoE,
    ModelicaDoEOMC,
    ModelicaSystemError,
    ModelicaSystemRunner,
    ModelicaDoERunner,

    doe_get_solutions,

    ModelicaSystemCmd,
)
from OMPython.OMCSession import (
    OMCSessionCmd,
    OMCSessionZMQ,
    OMCSessionException,

    OMCProcessLocal,
    OMCProcessPort,
    OMCProcessDocker,
    OMCProcessDockerContainer,
)

# global names imported if import 'from OMPython import *' is used
__all__ = [
    'LinearizationResult',

    'ModelExecutionCmd',
    'ModelExecutionData',
    'ModelExecutionException',

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

    'ModelicaSystem',
    'ModelicaSystemOMC',
    'ModelicaSystemCmd',
    'ModelicaSystemDoE',
    'ModelicaDoEOMC',
    'ModelicaSystemError',

    'ModelicaSystemRunner',
    'ModelicaDoERunner',

    'doe_get_solutions',

    'OMCSessionABC',
    'OMCSessionCmd',

    'OMCSessionException',

    'OMCSessionZMQ',

    'OMCProcessLocal',
    'OMCProcessPort',
    'OMCProcessDocker',
    'OMCProcessDockerContainer',
]
