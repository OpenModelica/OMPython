try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='OMPython',
      version='2.0',
      description='OpenModelica-Python API Interface',
      author='Anand Kalaiarasi Ganeson',
      author_email='ganan642@student.liu.se',
      maintainer='Adeel Asghar',
      maintainer_email='adeel.asghar@liu.se',
      url='http://openmodelica.org/',
      packages=['OMPython', 'OMPython.OMParser','OMPythonIDL', 'OMPythonIDL._OMCIDL', 'OMPythonIDL._OMCIDL__POA'],
      install_requires=[
        # 'omniORB', # Required, but not part of pypi
        'pyparsing'
      ]
)


