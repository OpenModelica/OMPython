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
    ModelicaSystemCmd,
    ModelicaSystemDoE,
    ModelicaSystemError,
)
from OMPython.OMCSession import (
    OMCPath,
    OMCSession,
    OMCSessionCmd,
    OMCSessionDocker,
    OMCSessionDockerContainer,
    OMCSessionException,
    OMCSessionLocal,
    OMCSessionPort,
    OMCSessionRunData,
    OMCSessionWSL,
    OMCSessionZMQ,
)

# global names imported if import 'from OMPython import *' is used
__all__ = [
    'LinearizationResult',

    'ModelicaSystem',
    'ModelicaSystemCmd',
    'ModelicaSystemDoE',
    'ModelicaSystemError',

    'OMCPath',

    'OMCSession',
    'OMCSessionCmd',
    'OMCSessionDocker',
    'OMCSessionDockerContainer',
    'OMCSessionException',
    'OMCSessionPort',
    'OMCSessionLocal',
    'OMCSessionRunData',
    'OMCSessionWSL',
    'OMCSessionZMQ',
]
