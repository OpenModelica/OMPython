# OMPython [![License: OSMC-PL-RT](https://img.shields.io/badge/license-OSMC--PL--RT-lightgrey.svg)](LICENSE)

OMPython is a Python interface that uses ZeroMQ to communicate with OpenModelica.

[![Test](https://github.com/OpenModelica/OMPython/actions/workflows/Test.yml/badge.svg)](https://github.com/OpenModelica/OMPython/actions/workflows/Test.yml)
[![PyPI Version](https://img.shields.io/pypi/v/OMPython.svg)](https://pypi.org/project/OMPython/)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/ompython.svg)](https://anaconda.org/conda-forge/ompython)

## Dependencies

  - Python >= 3.10; Python >= 3.12 for `OMPath` functionality (handle file system access via OMC using a `pathlib.Path` compatible abstraction layer)
  - Additional packages: numpy, psutil, pyparsing and pyzmq

## Selecting the OpenModelica installation

`OMCSessionLocal` and `ModelicaSystemOMC` look for OpenModelica in this order:

1. the `omhome` argument: `OMPython.OMCSessionLocal(omhome="C:/Program Files/OpenModelica1.27.0-64bit")`
2. the `version` argument: `OMPython.OMCSessionLocal(version="1.27.0")`, or `version="1.27"` for the newest
   installed 1.27.x
3. the environment variable `OPENMODELICAHOME`
4. the newest version found in the environment variables `OPENMODELICAHOME_<version>`
5. `omc` on the `PATH`

The Windows installer of OpenModelica allows several versions to be installed side by side and sets
`OPENMODELICAHOME_<version>` for each of them, with every character of the version that is not a letter or a
digit replaced by an underscore: `OPENMODELICAHOME_1_27_0` for version 1.27.0. `OPENMODELICAHOME` points to the
version selected as the default one.

## Installation

Installation using `pip` is recommended.

### Via pip

```bash
pip install OMPython
```

### Via conda

OMPython is also available as a conda package via [conda-forge](https://conda-forge.org/)

```bash
conda install -c conda-forge ompython
```
See the [ompython-feedstock](https://github.com/conda-forge/ompython-feedstock) for details.

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
import OMPython
omc = OMPython.OMCSessionLocal()
omc.sendExpression("getVersion()")
```

or read the [OMPython documentation](https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/ompython.html)
online.

## Bug Reports

- Submit bugs through the [OpenModelica GitHub issues](https://github.com/OpenModelica/OMPython/issues/new).
- [Pull requests](https://github.com/OpenModelica/OMPython/pulls) are welcome.


## Development

It is recommended to set up [`pre-commit`](https://pre-commit.com/) to automatically run linters:

```bash
# cd to the root of the repository
pre-commit install
```

## License

This project is licensed under the OSMC Public Runtime License. See [LICENSE](LICENSE) for details.

## Contact

- Adeel Asghar, <adeel.asghar@liu.se>
- Arunkumar Palanisamy, <arunkumar.palanisamy@liu.se>
