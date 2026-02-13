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

from OMPython.ModelicaSystem import (
    LinearizationResult,
    ModelicaSystem,
    ModelicaSystemOMC,
    ModelExecutionCmd,
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

    OMSessionRunner,
    OMSessionABC,

    ModelExecutionData,
    ModelExecutionException,

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

    'ModelExecutionData',
    'ModelExecutionException',

    'ModelicaSystem',
    'ModelicaSystemOMC',
    'ModelicaSystemCmd',
    'ModelExecutionCmd',
    'ModelicaSystemDoE',
    'ModelicaDoEOMC',
    'ModelicaSystemError',

    'ModelicaSystemRunner',
    'ModelicaDoERunner',

    'OMPathABC',
    'OMCPath',

    'OMSessionRunner',

    'doe_get_solutions',

    'OMCSessionABC',
    'OMCSessionCmd',
    'OMCSessionDocker',
    'OMCSessionDockerContainer',
    'OMSessionABC',

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
