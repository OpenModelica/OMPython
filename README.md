# OMPython

OMPython is a Python interface that uses ZeroMQ to
communicate with OpenModelica.

[![FMITest](https://github.com/OpenModelica/OMPython/actions/workflows/FMITest.yml/badge.svg)](https://github.com/OpenModelica/OMPython/actions/workflows/FMITest.yml)
[![Test](https://github.com/OpenModelica/OMPython/actions/workflows/Test.yml/badge.svg)](https://github.com/OpenModelica/OMPython/actions/workflows/Test.yml)

## Dependencies

-   Python 3.x supported
-   PyZMQ is required

## Installation

Installation using `pip` is recommended.

### Via pip

```bash
pip install OMPython
```

### Via source

Clone the repository and run:

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

  - Submit bugs through the [OpenModelica GitHub issues](https://github.com/OpenModelica/OMPython/issues/new).
  - [Pull requests](https://github.com/OpenModelica/OMPython/pulls) are welcome.

## Contact

  - Adeel Asghar, <adeel.asghar@liu.se>
  - Arunkumar Palanisamy, <arunkumar.palanisamy@liu.se>
