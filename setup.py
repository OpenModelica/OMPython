try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from subprocess import call
import os
# Python 3.3 offers shutil.which()
from distutils import spawn


def warningOrError(errorOnFailure, msg):
    if errorOnFailure:
        raise Exception(msg)
    else:
        print(msg)


def generateIDL():
    errorOnFailure = not os.path.exists(os.path.join(os.path.dirname(__file__), 'OMPythonIDL', '__init__.py'))
    try:
        omhome = os.path.split(os.path.split(os.path.realpath(spawn.find_executable("omc")))[0])[0]
    except BaseException:
        omhome = None
    omhome = omhome or os.environ.get('OPENMODELICAHOME')

    if omhome is None:
        warningOrError(errorOnFailure, "Failed to find OPENMODELICAHOME (searched for environment variable as well as the omc executable)")
        return
    idl = os.path.join(omhome, "share", "omc", "omc_communication.idl")
    if not os.path.exists(idl):
        warningOrError(errorOnFailure, "Path not found: %s" % idl)
        return

    if 0 != call(["omniidl", "-bpython", "-Wbglobal=_OMCIDL", "-Wbpackage=OMPythonIDL", idl]):
        warningOrError(errorOnFailure, "omniidl command failed")
        return
    print("Generated OMPythonIDL files")


try:
    # if we don't have omniidl or omniORB then don't try to generate OMPythonIDL files.
    try:
      import omniidl
    except ImportError:
      import omniORB
    hasomniidl = True
    generateIDL()
except ImportError:
    hasomniidl = False

OMPython_packages = ['OMPython', 'OMPython.OMParser']
if hasomniidl:
    OMPython_packages.extend(['OMPythonIDL', 'OMPythonIDL._OMCIDL', 'OMPythonIDL._OMCIDL__POA'])

setup(name='OMPython',
      version='3.3.0',
      description='OpenModelica-Python API Interface',
      author='Anand Kalaiarasi Ganeson',
      author_email='ganan642@student.liu.se',
      maintainer='Adeel Asghar',
      maintainer_email='adeel.asghar@liu.se',
      license="BSD, OSMC-PL 1.2, GPL (user's choice)",
      url='http://openmodelica.org/',
      packages=OMPython_packages,
      install_requires=[
          # 'omniORB', # Required, but not part of pypi
          'future',
          'pyparsing',
          'numpy',
          'psutil',
          'pyzmq'
      ]
      )
