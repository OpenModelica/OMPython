try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from subprocess import call
import sys
import os
# Python 3.3 offers shutil.which()
from distutils import spawn

if not os.path.exists(os.path.join(os.path.dirname(__file__), 'OMPythonIDL', '__init__.py')):
  try:
    omhome = os.path.split(os.path.split(os.path.realpath(spawn.find_executable("omc")))[0])[0]
  except:
    omhome = None
  omhome = omhome or os.environ.get('OPENMODELICAHOME')

  if omhome is None:
    raise Exception("Failed to find OPENMODELICAHOME (searched for environment variable as well as the omc executable)")
  idl = os.path.join(omhome,"share","omc","omc_communication.idl")
  if not os.path.exists(idl):
    raise Exception("Path not found: %s" % idl)

  if 0<>call(["omniidl","-bpython","-Wbglobal=_OMCIDL","-Wbpackage=OMPythonIDL",idl]):
    raise Exception("omniidl command failed")

setup(name='OMPython',
      version='2.0.2',
      description='OpenModelica-Python API Interface',
      author='Anand Kalaiarasi Ganeson',
      author_email='ganan642@student.liu.se',
      maintainer='Adeel Asghar',
      maintainer_email='adeel.asghar@liu.se',
      license="BSD, OSMC-PL 1.2, GPL (user's choice)",
      url='http://openmodelica.org/',
      packages=['OMPython', 'OMPython.OMParser', 'OMPythonIDL', 'OMPythonIDL._OMCIDL', 'OMPythonIDL._OMCIDL__POA'],
      install_requires=[
        # 'omniORB', # Required, but not part of pypi
        'pyparsing'
      ]
)
