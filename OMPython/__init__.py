# -*- coding: utf-8 -*-
"""
OMPython is a Python interface to OpenModelica.
To get started, create an OMCSessionZMQ object:
from OMPython import OMCSessionZMQ
omc = OMCSessionZMQ()
omc.sendExpression("command")
"""

import shutil
import abc
import csv
import getpass
import logging
import json
import os
import platform
import psutil
import re
import signal
import subprocess
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
import numpy as np
import pyparsing
import importlib
import zmq
import pathlib
import warnings


# TODO: replace this with the new parser
from OMPython import OMTypedParser, OMParser

__license__ = """
 This file is part of OpenModelica.

 Copyright (c) 1998-CurrentYear, Open Source Modelica Consortium (OSMC),
 c/o Linköpings universitet, Department of Computer and Information Science,
 SE-58183 Linköping, Sweden.

 All rights reserved.

 THIS PROGRAM IS PROVIDED UNDER THE TERMS OF THE BSD NEW LICENSE OR THE
 GPL VERSION 3 LICENSE OR THE OSMC PUBLIC LICENSE (OSMC-PL) VERSION 1.2.
 ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS PROGRAM CONSTITUTES
 RECIPIENT'S ACCEPTANCE OF THE OSMC PUBLIC LICENSE OR THE GPL VERSION 3,
 ACCORDING TO RECIPIENTS CHOICE.

 The OpenModelica software and the OSMC (Open Source Modelica Consortium)
 Public License (OSMC-PL) are obtained from OSMC, either from the above
 address, from the URLs: http://www.openmodelica.org or
 http://www.ida.liu.se/projects/OpenModelica, and in the OpenModelica
 distribution. GNU version 3 is obtained from:
 http://www.gnu.org/copyleft/gpl.html. The New BSD License is obtained from:
 http://www.opensource.org/licenses/BSD-3-Clause.

 This program is distributed WITHOUT ANY WARRANTY; without even the implied
 warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE, EXCEPT AS
 EXPRESSLY SET FORTH IN THE BY RECIPIENT SELECTED SUBSIDIARY LICENSE
 CONDITIONS OF OSMC-PL.
"""

# Logger Defined
logger = logging.getLogger('OMPython')
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
logger_console_handler = logging.StreamHandler()
logger_console_handler.setLevel(logging.INFO)

# create formatter and add it to the handlers
logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger_console_handler.setFormatter(logger_formatter)

# add the handlers to the logger
logger.addHandler(logger_console_handler)
logger.setLevel(logging.WARNING)
