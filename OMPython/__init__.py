# -*- coding: utf-8 -*-
"""
OMPython is a Python interface to OpenModelica.
To get started, create an OMCSessionZMQ object:
from OMPython import OMCSessionZMQ
omc = OMCSessionZMQ()
omc.sendExpression("command")
"""

from OMPython.OMBase import (
    ModelicaSystemBase,
    ModelicaSystemError,
)
from OMPython.ModelicaSystem import (
    LinearizationResult,
    ModelicaSystem,
    ModelicaSystemCmd,
    ModelicaSystemDoE,
)
from OMPython.OMRunner import (
    ModelicaSystemRunner,
)
from OMPython.OMCSession import (
    OMCSession,
    OMCSessionCmd,
    OMCSessionException,
    OMCSessionRunData,
    OMCSessionZMQ,
    OMCSessionPort,
    OMCSessionLocal,
    OMCSessionDocker,
    OMCSessionDockerContainer,
    OMCSessionWSL,
)

# global names imported if import 'from OMPython import *' is used
__all__ = [
    'LinearizationResult',
    'ModelicaSystem',
    'ModelicaSystemBase',
    'ModelicaSystemCmd',
    'ModelicaSystemDoE',
    'ModelicaSystemError',
    'ModelicaSystemRunner',

    'OMCSession',
    'OMCSessionCmd',
    'OMCSessionException',
    'OMCSessionRunData',
    'OMCSessionZMQ',
    'OMCSessionPort',
    'OMCSessionLocal',
    'OMCSessionDocker',
    'OMCSessionDockerContainer',
    'OMCSessionWSL',
]
