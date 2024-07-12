# OMPython

OMPython is a Python interface that uses ZeroMQ or CORBA (omniORB) to
communicate with OpenModelica.

[![FMITest](https://github.com/OpenModelica/OMPython/actions/workflows/FMITest.yml/badge.svg)](https://github.com/OpenModelica/OMPython/actions/workflows/FMITest.yml)
[![Test](https://github.com/OpenModelica/OMPython/actions/workflows/Test.yml/badge.svg)](https://github.com/OpenModelica/OMPython/actions/workflows/Test.yml)

## Dependencies

### Using ZeroMQ

-   Python 2.7 and 3.x supported
-   PyZMQ is required

### Using omniORB

-   Currently, only Python 2.7 is supported
-   omniORB is required:
    -   Windows: included in the OpenModelica installation
    -   Linux: Install omniORB including Python 2 support (the omniidl
        command needs to be on the PATH). On Ubuntu, this is done by
        running
        `sudo apt-get install omniorb python-omniorb omniidl omniidl-python`

## Installation

Installation using `pip` is recommended.

### Linux

Install the latest OMPython master by running:

```bash
python -m pip install -U https://github.com/OpenModelica/OMPython/archive/master.zip
```

### Windows

Install the version packed with your OpenModelica installation by running:

```cmd
cd %OPENMODELICAHOME%\share\omc\scripts\PythonInterface
python -m pip install -U .
```

### Local installation

To Install the latest version of the OMPython master branch
only, previously cloned into `<OMPythonPath>`, run:

```
cd <OMPythonPath>
python -m pip install -U .
```

## Usage

Running the following commands should get you started

```python
import OMPython
help(OMPython)
```

```python
from OMPython import OMCSessionZMQ
omc = OMCSessionZMQ()
omc.sendExpression("getVersion()")
```

or read the [OMPython documentation](https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/ompython.html)
online.

## Bug Reports

  - See OMPython bugs on the [OpenModelica
    trac](https://trac.openmodelica.org/OpenModelica/query?component=OMPython)
    or submit a [new
    ticket](https://trac.openmodelica.org/OpenModelica/newticket).
  - [Pull requests](https://github.com/OpenModelica/OMPython/pulls) are
    welcome.

## Contact

  - Adeel Asghar, <adeel.asghar@liu.se>
  - Arunkumar Palanisamy, <arunkumar.palanisamy@liu.se>
