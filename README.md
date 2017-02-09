# OMPython

OMPython is a Python interface that uses CORBA (omniORB) to communicate with OpenModelica.

## Dependencies

- omniORB is required to be installed including Python support (the omniidl command needs to be on the PATH)  
  On Ubuntu, this is done by running `sudo apt-get install omniorb python-omniorb omniidl omniidl-python` 
- Python 2.7 is required (omniORB restriction). Download python from http://www.python.org/download/
- pip is recommended

## Installation

Fast way (using pip):
- `pip install git+git://github.com/OpenModelica/OMPython.git`

Manual installation:
- Add python to your PATH.
- Start command prompt/terminal and execute command `python setup.py install`. This will add OMPython to the python 3rd party libraries.

## Usage

```python
import OMPython
help(OMPython)
```

## Contact
Adeel, adeel.asghar@liu.se
Anand, ganan642@student.liu.se
