# -*- coding: utf-8 -*-
"""
OMPython is a Python interface to OpenModelica.
To get started, create an OMCSessionZMQ object:
from OMPython import OMCSessionZMQ
omc = OMCSessionZMQ()
omc.sendExpression("command")
"""

from OMPython.ModelicaSystem import (
    LinearizationResult,
    ModelicaSystem,
    ModelicaSystemCmd,
    ModelicaSystemDoE,
    ModelicaSystemError,
)
from OMPython.OMCSession import (
    OMCSessionCmd,
    OMCSessionException,
    OMCSessionRunData,
    OMCSessionZMQ,
    OMCProcessPort,
    OMCProcessLocal,
    OMCProcessDocker,
    OMCProcessDockerContainer,
    OMCProcessWSL,
)

# global names imported if import 'from OMPython import *' is used
__all__ = [
    'LinearizationResult',
    'ModelicaSystem',
    'ModelicaSystemCmd',
    'ModelicaSystemDoE',
    'ModelicaSystemError',

    'OMCSessionCmd',
    'OMCSessionException',
    'OMCSessionRunData',
    'OMCSessionZMQ',
    'OMCProcessPort',
    'OMCProcessLocal',
    'OMCProcessDocker',
    'OMCProcessDockerContainer',
    'OMCProcessWSL',
]
