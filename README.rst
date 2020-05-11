########
OMPython
########

OMPython is a Python interface that uses ZeroMQ or CORBA (omniORB) to communicate with OpenModelica.

Dependencies
============

Using ZeroMQ
------------
- Python 2.7 and 3.x supported
- PyZMQ is required

Using omniORB
-------------
- Currently, only Python 2.7 is supported
- omniORB is required:

  - Windows: included in the OpenModelica installation
  - Linux: Install omniORB including Python 2 support (the omniidl command needs to be on the PATH).
    On Ubuntu, this is done by running ``sudo apt-get install omniorb python-omniorb omniidl omniidl-python``


Installation
============
Installation using ``pip`` is recommended.

Linux
-----
Install the latest OMPython master by running::

  python -m pip install -U https://github.com/OpenModelica/OMPython/archive/master.zip

Windows
-------
Install the version as packaged with your OpenModelica installation by running::

  cd %OPENMODELICAHOME%\share\omc\scripts\PythonInterface
  python -m pip install -U .

Instead, to Install the latest version of the OMPython master branch only, previously cloned into ``<OMPythonPath>``, run::

  cd <OMPythonPath>
  python -m pip install -U .

Usage
=====
Running the following commads should get you started

.. code-block:: python

  import OMPython
  help(OMPython)

or read the `OMPython documentation <https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/ompython.html>`_ online.

Bug Reports
===========

- See OMPython bugs on the `OpenModelica trac <https://trac.openmodelica.org/OpenModelica/query?component=OMPython>`_
  or submit a `new ticket <https://trac.openmodelica.org/OpenModelica/newticket>`_.
- `Pull requests <https://github.com/OpenModelica/OMPython/pulls>`_ are welcome.

Contact
=======

- Adeel Asghar, adeel.asghar@liu.se
- Arunkumar Palanisamy, arunkumar.palanisamy@liu.se
