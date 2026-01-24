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
)
from OMPython.OMCSession import (
    OMCPath,
    OMCSession,

    ModelExecutionData,
    ModelExecutionException,

    OMCSessionCmd,
    OMCSessionDocker,
    OMCSessionDockerContainer,
    OMCSessionException,
    OMCSessionLocal,
    OMCSessionPort,
    OMCSessionWSL,
    OMCSessionZMQ,
)

# global names imported if import 'from OMPython import *' is used
__all__ = [
    'LinearizationResult',

    'ModelExecutionData',
    'ModelExecutionException',

    'ModelicaSystem',
    'ModelicaSystemOMC',
    'ModelExecutionCmd',
    'ModelicaSystemDoE',
    'ModelicaDoEOMC',
    'ModelicaSystemError',

    'OMCPath',

    'OMCSession',
    'OMCSessionCmd',
    'OMCSessionDocker',
    'OMCSessionDockerContainer',
    'OMCSessionException',
    'OMCSessionPort',
    'OMCSessionLocal',
    'OMCSessionWSL',
    'OMCSessionZMQ',
]
