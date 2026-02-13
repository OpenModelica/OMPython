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
    OMPathABC,
    OMCPath,

    OMSessionABC,
    OMSessionRunner,

    OMCSessionABC,
    OMCSessionCmd,
    OMCSessionDocker,
    OMCSessionDockerContainer,
    OMCSessionException,
    OMCSessionLocal,
    OMCSessionPort,

    OMPathRunnerBash,
    OMPathRunnerLocal,

    OMCSessionWSL,
    OMCSessionZMQ,

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

    'ModelicaSystem',
    'ModelicaSystemOMC',
    'ModelicaSystemCmd',
    'ModelicaSystemDoE',
    'ModelicaDoEOMC',
    'ModelicaSystemError',

    'ModelicaSystemRunner',
    'ModelicaDoERunner',

    'OMPathABC',
    'OMCPath',

    'OMSessionABC',
    'OMSessionRunner',

    'doe_get_solutions',

    'OMCSessionABC',
    'OMCSessionCmd',
    'OMCSessionDocker',
    'OMCSessionDockerContainer',
    'OMCSessionException',
    'OMCSessionPort',
    'OMCSessionLocal',

    'OMPathRunnerBash',
    'OMPathRunnerLocal',

    'OMCSessionWSL',
    'OMCSessionZMQ',

    'OMCProcessLocal',
    'OMCProcessPort',
    'OMCProcessDocker',
    'OMCProcessDockerContainer',
]
