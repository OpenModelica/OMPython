from setuptools import setup

OMPython_packages = ['OMPython', 'OMPython.OMParser']

setup(name='OMPython',
      version='3.6.0',
      description='OpenModelica-Python API Interface',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      author='Anand Kalaiarasi Ganeson',
      author_email='ganan642@student.liu.se',
      maintainer='Adeel Asghar',
      maintainer_email='adeel.asghar@liu.se',
      license="BSD, OSMC-PL 1.2, GPL (user's choice)",
      url='http://openmodelica.org/',
      packages=OMPython_packages,
      install_requires=[
          'future',
          'numpy',
          'psutil',
          'pyparsing',
          'pyzmq'
      ],
      python_requires='>=3.8',
      )
