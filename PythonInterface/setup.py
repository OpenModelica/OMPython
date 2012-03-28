from distutils.core import setup

setup(name='OMPython',
      version='1.0',
      description='OpenModelica-Python API Interface',
      author='Anand Kalaiarasi Ganeson',
      author_email='ganan642@student.liu.se',
      maintainer='Adeel Asghar',
      maintainer_email='adeel.asghar@liu.se',
      url='http://openmodelica.org/',
      packages=['OMPython', 'OMPython.OMParser'],
     )
     
setup(name='OMPythonIDL',
      version='1.0',
      description='OpenModelica-Python API Stubs',
      author='Anand Kalaiarasi Ganeson',
      author_email='ganan642@student.liu.se',
      maintainer='Adeel Asghar',
      maintainer_email='adeel.asghar@liu.se',
      url='http://openmodelica.org/',
      packages=['OMPythonIDL', 'OMPythonIDL._OMCIDL', 'OMPythonIDL._OMCIDL__POA'],
     )
     
