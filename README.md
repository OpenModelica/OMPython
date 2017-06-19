# OMPython

OMPython is a Python interface that uses CORBA (omniORB) or ZeroMQ to communicate with OpenModelica.

## Dependencies

### Using omniORB (Python 2 only)
- omniORB is required.
- omniORB is installed including Python 2 support (the omniidl command needs to be on the PATH)  
  On Ubuntu, this is done by running `sudo apt-get install omniorb python-omniorb omniidl omniidl-python`
- Python 2.7 is required (omniORB restriction). Download Python from http://www.python.org/download/
- Installation using `pip` is recommended.

### Using ZeroMQ (Python 2 and 3 supported)
- PyZMQ is required.
- Python 2.7 or 3.x.x is required. Download Python from http://www.python.org/download/
- Installation using `pip` is recommended.

## Installation

### Unix
```bash
$ python -m pip install https://github.com/OpenModelica/OMPython/archive/master.zip
```

### Windows
- Add python to your PATH.
- Start command prompt/terminal and execute commands,
```bash
$ cd %OPENMODELICAHOME%\share\omc\scripts\PythonInterface
$ python -m pip install .
```
- This will add OMPython to the Python 3rd party libraries.

## Usage

```python
import OMPython
help(OMPython)
```

## Contact
Adeel, adeel.asghar@liu.se
Anand, ganan642@student.liu.se
