# OMPython

OMPython is a Python interface that uses CORBA (omniORB) or ZeroMQ to communicate with OpenModelica.

## Dependencies

### Using omniORB (Python 2 only)
- Python 2.7 is required (omniORB restriction). Download Python from http://www.python.org/download/
- omniORB is required
  - Windows: included in the installer of OpenModelica
  - Linux: Install omniORB including Python 2 support (the omniidl command needs to be on the PATH)  
      On Ubuntu, this is done by running `sudo apt-get install omniorb python-omniorb omniidl omniidl-python`
- Installation using `pip` is recommended.

### Using ZeroMQ (Python 2 and 3 supported)
- Python 2.7 or 3.x.x is required. Download Python from http://www.python.org/download/
- PyZMQ is required.
- Installation using `pip` is recommended.

## Installation

### Linux
```bash
$ python -m pip install https://github.com/OpenModelica/OMPython/archive/master.zip
```

### Windows
- Add python to your PATH.
- Start command prompt/terminal and execute commands,
```powershell
> cd %OPENMODELICAHOME%\share\omc\scripts\PythonInterface
> python -m pip install .
```
- This will add OMPython to the Python 3rd party libraries.

## Usage

```python
import OMPython
help(OMPython)
```

## Bug Reports

- See OMPython bugs on the [OpenModelica trac](https://trac.openmodelica.org/OpenModelica/query?component=OMPython) or submit a [new ticket](https://trac.openmodelica.org/OpenModelica/newticket).
- [Pull requests](../../pulls) are welcome.

## Contact

Adeel Asghar, adeel.asghar@liu.se<br />
Arunkumar Palanisamy, arunkumar.palanisamy@liu.se
