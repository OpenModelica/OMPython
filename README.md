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

```bash
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


## Development

It is recommended to set up [`pre-commit`](https://pre-commit.com/) to
automatically run linters:
```sh
# cd to the root of the repository
pre-commit install
```

## Conda Package

Follow the steps to make a conda package,

 - Update the version number in `recipe/meta.yaml` file.
 - Update the `sha256` in `recipe/meta.yaml` according to the version number.
   - You can get the `sha256` from https://pypi.org/project/OMPython/#files
 - Download and install conda if you don't have one.
 - Run command `conda install -c conda-forge conda-build` that will install `conda-build` tool into your conda environment.
 - Build conda recipe `conda build recipe`.
 - Do a local install and test.
    - Install locally to test. Run `conda create -n test-ompython -c local -c conda-forge ompython`
    - Activate the install. Run `conda activate test-ompython`
    - Now test installed ompython `python -c "import OMPython; print(OMPython.__version__)"`

## Contact

  - Adeel Asghar, <adeel.asghar@liu.se>
  - Arunkumar Palanisamy, <arunkumar.palanisamy@liu.se>
