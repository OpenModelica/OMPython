# -*- coding: utf-8 -*-
"""
OMPython is a Python interface to OpenModelica.
To get started, create an OMCSession object:
from OMPython import OMCSession
OMPython = OMCSession()
OMPython.sendExpression(command)

Note: Conversion from OMPython 1.0 to OMPython 2.0 is very simple
1.0:
import OMPython
OMPython.execute(command)
2.0:
from OMPython import OMCSession
OMPython = OMCSession()
OMPython.execute(command)

The difference between execute and sendExpression is the type of the
returned expression. sendExpression maps Modelica types to Python types,
while execute tries to map also output that is not valid Modelica.
That format is harder to use.
"""

__license__ = """
 This file is part of OpenModelica.

 Copyright (c) 1998-CurrentYear, Open Source Modelica Consortium (OSMC),
 c/o Linköpings universitet, Department of Computer and Information Science,
 SE-58183 Linköping, Sweden.

 All rights reserved.

 THIS PROGRAM IS PROVIDED UNDER THE TERMS OF THE BSD NEW LICENSE OR THE
 GPL VERSION 3 LICENSE OR THE OSMC PUBLIC LICENSE (OSMC-PL) VERSION 1.2.
 ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS PROGRAM CONSTITUTES
 RECIPIENT'S ACCEPTANCE OF THE OSMC PUBLIC LICENSE OR THE GPL VERSION 3,
 ACCORDING TO RECIPIENTS CHOICE.

 The OpenModelica software and the OSMC (Open Source Modelica Consortium)
 Public License (OSMC-PL) are obtained from OSMC, either from the above
 address, from the URLs: http://www.openmodelica.org or
 http://www.ida.liu.se/projects/OpenModelica, and in the OpenModelica
 distribution. GNU version 3 is obtained from:
 http://www.gnu.org/copyleft/gpl.html. The New BSD License is obtained from:
 http://www.opensource.org/licenses/BSD-3-Clause.

 This program is distributed WITHOUT ANY WARRANTY; without even the implied
 warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE, EXCEPT AS
 EXPRESSLY SET FORTH IN THE BY RECIPIENT SELECTED SUBSIDIARY LICENSE
 CONDITIONS OF OSMC-PL.

 Version: 1.1
"""

import os
import sys
import time
import logging
import uuid
import getpass
import subprocess
import tempfile
import pyparsing
from distutils import spawn

# The following import are added by Sudeep
import numpy as np
import csv

from copy import deepcopy
import xml.etree.ElementTree as ET

if sys.platform == 'darwin':
    # On Mac let's assume omc is installed here and there might be a broken omniORB installed in a bad place
    sys.path.append('/opt/local/lib/python2.7/site-packages/')
    sys.path.append('/opt/openmodelica/lib/python2.7/site-packages/')

# TODO: replace this with the new parser
from OMPython import OMTypedParser, OMParser

# Logger Defined
logger = logging.getLogger('OMCSession')
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
logger_console_handler = logging.StreamHandler()
logger_console_handler.setLevel(logging.INFO)

# create formatter and add it to the handlers
logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger_console_handler.setFormatter(logger_formatter)

# add the handlers to the logger
logger.addHandler(logger_console_handler)

class OMCSession(object):

    def _start_server(self):
        self._server = subprocess.Popen(self._omc_command, shell=True, stdout=self._omc_log_file,
                                        stderr=self._omc_log_file)
        return self._server

    def _set_omc_corba_command(self, omc_path='omc'):
        self._omc_command = "{0} +d=interactiveCorba +c={1}".format(omc_path, self._random_string)
        return self._omc_command

    def _start_omc(self):
        self._server = None
        self._omc_command = None
        try:
            self.omhome = os.environ.get('OPENMODELICAHOME')
            if self.omhome is None:
              self.omhome = os.path.split(os.path.split(os.path.realpath(spawn.find_executable("omc")))[0])[0]
            elif os.path.exists('/opt/local/bin/omc'):
              self.omhome = '/opt/local'
            # add OPENMODELICAHOME\lib\python to PYTHONPATH so python can load omniORB imports
            sys.path.append(os.path.join(self.omhome, 'lib', 'python'))
            self._set_omc_corba_command(os.path.join(self.omhome, 'bin', 'omc'))
            self._start_server()
        except:
          logger.error("The OpenModelica compiler is missing in the System path (%s), please install it" % os.path.join(self.omhome, 'bin', 'omc'))
          raise

    def _connect_to_omc(self):
        self._omc = None
        # import the skeletons for the global module
        from omniORB import CORBA
        from OMPythonIDL import _OMCIDL
        # Locating and using the IOR
        if sys.platform == 'win32':
            self._ior_file = "openmodelica.objid." + self._random_string
        else:
            self._ior_file = "openmodelica." + self._currentUser + ".objid." + self._random_string
        self._ior_file = os.path.join(self._temp_dir, self._ior_file)
        self._omc_corba_uri = "file:///" + self._ior_file
        # See if the omc server is running
        if os.path.isfile(self._ior_file):
            logger.info("OMC Server is up and running at {0}".format(self._omc_corba_uri))
        else:
            attempts = 0
            while True:
                if not os.path.isfile(self._ior_file):
                    time.sleep(0.25)
                    attempts += 1
                    if attempts == 10:
                        name = self._omc_log_file.name
                        self._omc_log_file.close()
                        logger.error("OMC Server is down. Please start it! Log-file says:\n%s" % open(name).read())
                        raise Exception
                    else:
                        continue
                else:
                    logger.info("OMC Server is up and running at {0}".format(self._omc_corba_uri))
                    break

        #initialize the ORB with maximum size for the ORB set
        sys.argv.append("-ORBgiopMaxMsgSize")
        sys.argv.append("2147483647")
        self._orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        # Read the IOR file
        with open(self._ior_file, 'r') as f_p:
            self._ior = f_p.readline()

        # Find the root POA
        self._poa = self._orb.resolve_initial_references("RootPOA")
        # Convert the IOR into an object reference
        self._obj_reference = self._orb.string_to_object(self._ior)
        # Narrow the reference to the OmcCommunication object
        self._omc = self._obj_reference._narrow(_OMCIDL.OmcCommunication)
        # Check if we are using the right object
        if self._omc is None:
            logger.error("Object reference is not valid")
            raise Exception

    def __init__(self, readonly=False):
        self.readonly = readonly
        self.omc_cache = {}

        # FIXME: this code is not well written... need to be refactored
        self._temp_dir = tempfile.gettempdir()

        # generate a random string for this session
        self._random_string = uuid.uuid4().hex

        if sys.platform == 'win32':
          self._omc_log_file = open(os.path.join(self._temp_dir, "openmodelica.objid." + self._random_string+".log"), 'w')
        else:
          self._currentUser = getpass.getuser()
          if not self._currentUser:
              self._currentUser = "nobody"
          # this file must be closed in the destructor
          self._omc_log_file = open(os.path.join(self._temp_dir, "openmodelica." + self._currentUser + ".objid." + self._random_string+".log"), 'w')

        # start up omc executable, which is waiting for the CORBA connection
        self._start_omc()

        # connect to the running omc instance using CORBA
        self._connect_to_omc()

    def __del__(self):
        if self._omc is not None:
          self._omc.sendExpression("quit()")
        self._omc_log_file.close()
        # kill self._server process if it is still running/exists
        if self._server.returncode is None:
            self._server.kill()

    # FIXME: we should have one function which interacts with OMC. Either execute OR sendExpression.
    # Execute uses OMParser.check_for_values and sendExpression uses OMTypedParser.parseString.
    # We should have one parser. Then we can get rid of one of these functions.
    def execute(self, command):
        if self._omc is not None:
          result = self._omc.sendExpression(command)
          if command == "quit()":
            self._omc = None
            return result
          else:
            answer = OMParser.check_for_values(result)
            return answer
        else:
          return "No connection with OMC. Create an instance of OMCSession."

    # FIXME: we should have one function which interacts with OMC. Either execute OR sendExpression.
    # Execute uses OMParser.check_for_values and sendExpression uses OMTypedParser.parseString.
    # We should have one parser. Then we can get rid of one of these functions.
    def sendExpression(self, command, parsed=True):
        """
        Sends an expression to the OpenModelica. The return type is parsed as if the
        expression was part of the typed OpenModelica API (see ModelicaBuiltin.mo).
        * Integer and Real are returned as Python numbers
        * Strings, enumerations, and typenames are returned as Python strings
        * Arrays, tuples, and MetaModelica lists are returned as tuples
        * Records are returned as dicts (the name of the record is lost)
        * Booleans are returned as True or False
        * NONE() is returned as None
        * SOME(value) is returned as value
        """
        if self._omc is not None:
          result = self._omc.sendExpression(str(command))
          if command == "quit()":
            self._omc = None
            return result
          else:
            if (parsed==True):
               answer = OMTypedParser.parseString(result)
               return answer
            else:
               return result     
        else:
          return "No connection with OMC. Create an instance of OMCSession."

    def ask(self, question, opt=None, parsed=True):
        p = (question, opt, parsed)

        if self.readonly and question != 'getErrorString':
            # can use cache if readonly
            if p in self.omc_cache:
                return self.omc_cache[p]

        if opt:
            expression = '{0}({1})'.format(question, opt)
        else:
            expression = question

        logger.debug('OMC ask: {0}  - parsed: {1}'.format(expression, parsed))

        try:
            if parsed:
                res = self.execute(expression)
            else:
                res = self._omc.sendExpression(expression)
        except Exception as e:
            logger.error("OMC failed: {0}, {1}, parsed={2}".format(question, opt, parsed))
            raise e

        # save response
        self.omc_cache[p] = res

        return res

    # TODO: Open Modelica Compiler API functions. Would be nice to generate these.
    def loadFile(self, filename):
        return self.ask('loadFile', '"{0}"'.format(filename))

    def loadModel(self, className):
        return self.ask('loadModel', className)

    def isModel(self, className):
        return self.ask('isModel', className)

    def isPackage(self, className):
        return self.ask('isPackage', className)

    def isPrimitive(self, className):
        return self.ask('isPrimitive', className)

    def isConnector(self, className):
        return self.ask('isConnector', className)

    def isRecord(self, className):
        return self.ask('isRecord', className)

    def isBlock(self, className):
        return self.ask('isBlock', className)

    def isType(self, className):
        return self.ask('isType', className)

    def isFunction(self, className):
        return self.ask('isFunction', className)

    def isClass(self, className):
        return self.ask('isClass', className)

    def isParameter(self, className):
        return self.ask('isParameter', className)

    def isConstant(self, className):
        return self.ask('isConstant', className)

    def isProtected(self, className):
        return self.ask('isProtected', className)

    def getPackages(self):
        return self.ask('getPackages')

    def getPackages(self, className):
        return self.ask('getPackages', className)

    def getClassRestriction(self, className):
        return self.ask('getClassRestriction', className)

    def getDerivedClassModifierNames(self, className):
        return self.ask('getDerivedClassModifierNames', className)

    def getDerivedClassModifierValue(self, className, modifierName):
        return self.ask('getDerivedClassModifierValue', '{0}, {1}'.format(className, modifierName))

    def typeNameStrings(self, className):
        return self.ask('typeNameStrings', className)

    def getComponents(self, className):
        return self.ask('getComponents', className)

    def getClassComment(self, className):
        try:
            return self.ask('getClassComment', className)
        except pyparsing.ParseException as ex:
            logger.warning("Method 'getClassComment' failed for {0}".format(className))
            logger.warning('OMTypedParser error: {0}'.format(ex.message))
            return 'No description available'

    def getNthComponent(self, className, comp_id):
        """ returns with (type, name, description) """
        return self.ask('getNthComponent', '{0}, {1}'.format(className, comp_id))

    def getNthComponentAnnotation(self, className, comp_id):
        return self.ask('getNthComponentAnnotation', '{0}, {1}'.format(className, comp_id))

    def getImportCount(self, className):
        return self.ask('getImportCount', className)

    def getNthImport(self, className, importNumber):
        # [Path, id, kind]
        return self.ask('getNthImport', '{0}, {1}'.format(className, importNumber))

    def getInheritanceCount(self, className):
        return self.ask('getInheritanceCount', className)

    def getNthInheritedClass(self, className, inheritanceDepth):
        return self.ask('getNthInheritedClass', '{0}, {1}'.format(className, inheritanceDepth))

    def getParameterNames(self, className):
        try:
            return self.ask('getParameterNames', className)
        except KeyError as ex:
            logger.warning('OMPython error: {0}'.format(ex.message))
            # FIXME: OMC returns with a different structure for empty parameter set
            return []

    def getParameterValue(self, className, parameterName):
        try:
            return self.ask('getParameterValue', '{0}, {1}'.format(className, parameterName))
        except pyparsing.ParseException as ex:
            logger.warning('OMTypedParser error: {0}'.format(ex.message))
            return ""

    def getComponentModifierNames(self, className, componentName):
        return self.ask('getComponentModifierNames', '{0}, {1}'.format(className, componentName))

    def getComponentModifierValue(self, className, componentName):
        try:
            # FIXME: OMPython exception UnboundLocalError exception for 'Modelica.Fluid.Machines.ControlledPump'
            return self.ask('getComponentModifierValue', '{0}, {1}'.format(className, componentName))
        except pyparsing.ParseException as ex:
            logger.warning('OMTypedParser error: {0}'.format(ex.message))
            result = self.ask('getComponentModifierValue', '{0}, {1}'.format(className, componentName), parsed=False)
            try:
                answer = OMParser.check_for_values(result)
                OMParser.result = {}
                return answer[2:]
            except (TypeError, UnboundLocalError) as ex:
                logger.warning('OMParser error: {0}'.format(ex.message))
                return result

    def getExtendsModifierNames(self, className, componentName):
        return self.ask('getExtendsModifierNames', '{0}, {1}'.format(className, componentName))

    def getExtendsModifierValue(self, className, extendsName, modifierName):
        try:
            # FIXME: OMPython exception UnboundLocalError exception for 'Modelica.Fluid.Machines.ControlledPump'
            return self.ask('getExtendsModifierValue', '{0}, {1}, {2}'.format(className, extendsName, modifierName))
        except pyparsing.ParseException as ex:
            logger.warning('OMTypedParser error: {0}'.format(ex.message))
            result = self.ask('getExtendsModifierValue', '{0}, {1}, {2}'.format(className, extendsName, modifierName), parsed=False)
            try:
                answer = OMParser.check_for_values(result)
                OMParser.result = {}
                return answer[2:]
            except (TypeError, UnboundLocalError) as ex:
                logger.warning('OMParser error: {0}'.format(ex.message))
                return result

    def getNthComponentModification(self, className, comp_id):
        # FIXME: OMPython exception Results KeyError exception

        # get {$Code(....)} field
        # \{\$Code\((\S*\s*)*\)\}
        value = self.ask('getNthComponentModification', '{0}, {1}'.format(className, comp_id), parsed=False)
        value = value.replace("{$Code(", "")
        return value[:-3]
        #return self.re_Code.findall(value)

    # function getClassNames
    #   input TypeName class_ = $Code(AllLoadedClasses);
    #   input Boolean recursive = false;
    #   input Boolean qualified = false;
    #   input Boolean sort = false;
    #   input Boolean builtin = false "List also builtin classes if true";
    #   input Boolean showProtected = false "List also protected classes if true";
    #   output TypeName classNames[:];
    # end getClassNames;
    def getClassNames(self, className=None, recursive=False, qualified=False, sort=False, builtin=False,
                      showProtected=False):
        if className:
            value = self.ask('getClassNames',
                             '{0}, recursive={1}, qualified={2}, sort={3}, builtin={4}, showProtected={5}'.format(
                                 className, str(recursive).lower(), str(qualified).lower(), str(sort).lower(),
                                 str(builtin).lower(), str(showProtected).lower()))
        else:
            value = self.ask('getClassNames',
                             'recursive={1}, qualified={2}, sort={3}, builtin={4}, showProtected={5}'.format(
                                 str(recursive).lower(), str(qualified).lower(), str(sort).lower(),
                                 str(builtin).lower(), str(showProtected).lower()))
        return value

		
#author = Sudeep Bajracharya
#sudba156@student.liu.se
#LIU(Department of Computer Science)
class Quantity:
    def __init__(self, name, start, changable, variability, description, causality):
        self.name = name
        self.start = start
        self.changable = changable
        self.description = description
        self.variability = variability
        self.causality = causality
		
#author = Sudeep Bajracharya
#sudba156@student.liu.se
#LIU(Department of Computer Science)
class ModelicaSystem(object):
    def __init__(self, fileName = None, modelName = None, lmodel = None):
        if fileName is None and modelName is None and lmodel is None: # all None 
            self.getconn = OMCSession()
            return
			
        if fileName is None:
            return "File does not exist"			
        self.tree = None
        self.quantitiesList = [] #detail list of all Modelica quantity variables inc. name, changable, description, etc
        self.qNamesList = [] #for all quantities name list
        self.cNamesList = [] #for continuous quantities name list 
        self.cValuesList = [] #for continuous quantities value list
        self.iNamesList = [] #for input quantities name list
        self.inputsVal = [] #for input quantities value list
        self.oNamesList = [] #for output quantities name list
        self.pNamesList = [] #for output quantities value list
        self.pValuesList = [] #for parameter quantities name list
        self.oValuesList = [] #for parameter quantities value list
        self.simNamesList = ['startTime', 'stopTime', 'stepSize', 'tolerance', 'solver'] #simulation options list
        self.simValuesList = [] #for simulation values list
        self.optimizeOptionsNamesList = ['startTime', 'stopTime', 'numberOfIntervals', 'stepSize', 'tolerance', 'simflags']
        self.optimizeOptionsValuesList = ['0.0', '1.0', '500', '0.002','1e-8',' ']
        self.linearizeOptionsNamesList = ['startTime', 'stopTime', 'numberOfIntervals', 'stepSize', 'tolerance', 'simflags']
        self.linearizeOptionsValuesList = ['0.0', '1.0', '500', '0.002','1e-8',' ']
        self.getconn = OMCSession()
        self.xmlFile = None
        self.lmodel = lmodel #may be needed if model is derived from other model
        self.modelName = modelName #Model class name
        self.fileName = fileName #Model file/package name
        #self.simFlag = False
        self.inputFlag = False #for model with input quantity
        self.csvFile = '' #for storing inputs condition
        if not os.path.exists(self.fileName): #if file does not eixt
            print "Error: File does not exist!!!"
            return
			
        (head, tail) = os.path.split(self.fileName)#to store directory/path and file)
        self.currDir = os.getcwd()
        self.modelDir = head
        self.fileName_ = tail

        if not self.modelDir:
            file_ = os.path.exists(self.fileName_)
            if(file_):#execution from path where file is located 
                self.loadingModel(self.fileName_, self.modelName, self.lmodel)
            else:
                print "Error: File does not exist!!!"

        else:
            os.chdir(self.modelDir)
            file_ = os.path.exists(self.fileName_)
            self.model = self.fileName_[:-3]
            if(self.fileName_):#execution from different path
                os.chdir(self.currDir)
                self.loadingModel(self.fileName, self.modelName, self.lmodel)
            else:
                print "Error: File does not exist!!!"

    def __del__(self):
        if self.getconn is not None:
            self.requestApi('quit')

    #for loading file/package, loading model and building model        
    def loadingModel(self, fName, mName, lmodel):
        #load file
        loadfileError = ''
        loadfileResult = self.requestApi("loadFile", fName)
        loadfileError = self.requestApi("getErrorString")
        if loadfileError:
            specError = 'Parser error: Unexpected token near: optimization (IDENT)'
            if specError in loadfileError:
                self.requestApi("setCommandLineOptions", '"+g=Optimica"')
                self.requestApi("loadFile", fName)
            else:
                print 'loadFile Error: ', loadfileError
                return
        
        #load Modelica standard libraries if needed
        if lmodel is not None:
            loadmodelError = ''
            loadModelResult = self.requestApi("loadModel", lmodel)		
            loadmodelError = self.requestApi('getErrorString')
            if loadmodelError:
                print loadmodelError
                return
        
        # build model 
        buildModelError = ''
        self.getconn.sendExpression("setCommandLineOptions(\"+d=initialization\")")
        buildModelResult = self.requestApi("buildModel", mName)
        buildModelError = self.requestApi("getErrorString")
        if 'Expected end of text' not in buildModelError:
            print buildModelError
            return
    
        self.xmlFile = buildModelResult[1]
        self.tree = ET.parse(self.xmlFile)
        self.root = self.tree.getroot()
        self.createQuantitiesList() #initialize quantitiesList
        self.getQuantitiesNames() #initialize qNamesList
        self.getContinuousNames() #initialize cNamesList
        self.getParameterNames() #initialize pNamesList
        #self.inputs = self.getInputNames()
        self.getInputNames() #initialize iNamesList
        self.setInputSize() #defing input value list size
        self.getOutputNames() #initialize oNamesList
        self.getContinuousValues() #initialize cValuesList
        self.getParameterValues() #initialize pValuesList
        self.getInputValues() #initialize input value list
        self.getOutputValues() #initialize oValuesList
        self.getSimulationValue() #initialize simulation value list


    #request to OM
    def requestApi(self, apiName, entity=None, properties=None ):
        if (entity is not None and properties is not None):
            exp = '{}({}, {})'.format(apiName, entity, properties)
        elif entity is not None and properties is None:
            if apiName == "loadFile" or apiName == "importFMU":
                exp = '{}("{}")'.format(apiName, entity)
            else:
                exp = '{}({})'.format(apiName, entity)
        else:
            exp = '{}()'.format(apiName)
        try:
            res = self.getconn.sendExpression(exp)
        except Exception as e:
            res = str(e)
        return res
    
    #create detail quantities list
    def createQuantitiesList(self):
        rootCQ = self.root
        if not self.quantitiesList:
            for sv in rootCQ.iter('ScalarVariable'):
                name = sv.get('name')
                changable = sv.get('isValueChangeable')
                description = sv.get('description')
                variability = sv.get('variability')
                causality = sv.get('causality')
                ch = sv.getchildren()
                start = None
                for att in ch:
                    start = att.get('start')
                self.quantitiesList.append(Quantity(name, start, changable, variability, description, causality))
        return self.quantitiesList
    
    #to get list of all quantities names
    def getQuantitiesNames(self):
        if not self.qNamesList:
            for q in self.quantitiesList:
                self.qNamesList.append(q.name)
        return self.qNamesList
    
    #check if names exist
    def checkAvailability(self, names, chkList, inputFlag = None):
        try:
            if isinstance(names, list):
                nonExistingList = []
                for n in names:
                    if n not in chkList:
                        nonExistingList.append(n)
                if nonExistingList:
                    print 'Error!!! ', nonExistingList , ' does not exist.'
                    return False
            elif isinstance(names, str):
                if names not in chkList:
                    print 'Error!!! ', names , ' does not exist.'
                    return False
            else:
                print 'Error!!! Incorrect format'
                return False
            return True
           
        except Exception as e:
            print e
    
    #to get details of quantities names
    def getQuantities(self, names = None):
        try:
            if names is not None:
                checking = self.checkAvailability(names, self.qNamesList)
                if not checking:
                    return
                if isinstance(names, str):
                    qlistnames = []
                    for q in self.quantitiesList:	
                        if names == q.name:
                            qlistnames.append({'Name: ':q.name, 'Vlaue: ':q.start,'Changeable:' : q.changable, 'Variability: ': q.variability, 'Description: ':q.description})
                            break
                    return qlistnames
                elif isinstance(names, list):
                    qlist = []
                    for n in names:                        
                        for q in self.quantitiesList:
                            if n == q.name:
                                qlist.append({'Name: ':q.name, 'Vlaue: ':q.start,'Changeable:' : q.changable, 'Variability: ': q.variability, 'Description: ':q.description})
                                break
                    return qlist
                else:
                    print 'Error!!! Incorrect format'
            else:
                qlist = []
                                      
                for q in self.quantitiesList:
                    qlist.append({'Name: ':q.name, 'Vlaue: ':q.start,'Changeable:' : q.changable, 'Variability: ': q.variability, 'Description: ':q.description})
            
            
    
                return qlist
        except Exception as e:
            print e
    
    #to get list of quantities name that are continuous variability
    def getContinuousNames(self):
        if not self.cNamesList:
            for l in self.quantitiesList:
                if(l.variability == "continuous"):
                    self.cNamesList.append(l.name)
        return self.cNamesList
    
    
    def getParameterNames(self):
        if not self.pNamesList:
            for l in self.quantitiesList:
                if(l.variability == "parameter"):
                    self.pNamesList.append(l.name)
        return self.pNamesList
    
    #to get list of quantities name that are input
    def getInputNames(self):
        if not self.iNamesList:
            for l in self.quantitiesList:
                if(l.causality == "input"):
                    self.iNamesList.append(l.name)
        return self.iNamesList
    
    #set input value list size
    def setInputSize(self):
        size = len(self.iNamesList)
        self.inputsVal = [None]*size		
    
    #to get list of quantities name that are output
    def getOutputNames(self):
        if not self.oNamesList:
            for l in self.quantitiesList:
                if(l.causality == "output"):
                    self.oNamesList.append(l.name)
        return self.oNamesList
    
    #to get values of continuous quantities name
    def getContinuousValues(self, contiName=None):
        if contiName is None:
            if not self.cValuesList:
                for l in self.quantitiesList:
                    if(l.variability == "continuous"):
                        str_ = l.start
                        if str_ is None:
                            self.cValuesList.append(str_)
                        else:
                            self.cValuesList.append(float(str_))
            return self.cValuesList
        else:
            try:
                #if isinstance(contiName, list):
                checking = self.checkAvailability(contiName, self.cNamesList)
                #if checking is False:
                if not checking:
                    return
                if isinstance (contiName, str):
                    index_ = self.cNamesList.index(contiName)
                    return (self.cValuesList[index_])
                valList = []
                for n in contiName:
                    index_ = self.cNamesList.index(n)
                    valList.append(self.cValuesList[index_])
                return valList
            except Exception as e:
                print e
    
    #to get values of parameter quantities name    
    def getParameterValues(self, paraName = None):
        if paraName is None:					
            if not self.pValuesList:
                for l in self.quantitiesList:
                    if(l.variability == "parameter"):
                        str_ = l.start
                        if ((str_ is None) or (str_ == 'true' or str_ == 'false')):
                            if (str_ == 'ture'):
                                str_ = True
                            elif str_ == 'false':
                                str_ = False
                            self.pValuesList.append(str_)
                        else:
                            self.pValuesList.append(float(str_))
            return self.pValuesList
        else:
            try:
                #if isinstance(paraName, list):
                checking = self.checkAvailability(paraName, self.pNamesList)
                #if checking is False:
                if not checking:
                    return
                if isinstance(paraName, str):
                    index_ = self.pNamesList.index(paraName)
                    return (self.pValuesList[index_])
                valList = []
                for n in paraName:
                    index_ = self.pNamesList.index(n)
                    valList.append(self.pValuesList[index_])
                return valList
            except Exception as e:
                print e
    
    #to get values of input names
    def getInputValues(self, iName=None):
        try:
            if iName is None:
                return self.inputsVal
            else:
                checking = self.checkAvailability(iName,self.iNamesList)
            if not checking:
                return
            index_ = self.iNamesList.index(iName)
            return self.inputsVal[index_]
        except Exception as e:
            print e

    #to get values of output quantities name
    def getOutputValues(self, oName=None):
        if oName is None:			
            if not self.oValuesList:
                for l in self.quantitiesList:
                    if(l.causality == "output"):
                        self.oValuesList.append(l.start)
            return self.oValuesList
        else:
            if oName in self.oNamesList:
                index_ = self.oNamesList.index(oName)
                return self.oValuesList[index_]
            else:
                print '!!! ', oName, ' does not exist'
                return
    
    #to get simulation options values
    def getSimulationValue(self):
        if not self.simValuesList:
            root = self.tree.getroot()
            rootGSV = self.root
            for attr in rootGSV.iter('DefaultExperiment'):
                startTime = attr.get('startTime')
                self.simValuesList.append(startTime)
                stopTime = attr.get('stopTime')
                self.simValuesList.append(stopTime)
                stepSize = attr.get('stepSize')
                self.simValuesList.append(stepSize)
                tolerance = attr.get('tolerance')
                self.simValuesList.append(tolerance)
                solver = attr.get('solver')
                self.simValuesList.append(solver)
        return self.simValuesList
  
    #to display simulation options
    def getSimulationOptions(self):
        for simN, simV in zip(self.simNamesList, self.simValuesList):
            print simN, ' = ', simV
  
    #to display optimization options
    def getOptimizationOptions(self):
        for optN, optV in zip(self.optimizeOptionsNamesList, self.optimizeOptionsValuesList):
            print optN, ' = ', optV
    
    #to display linearization options
    def getLinearizationOptions(self):
        for linN, linV in zip(self.linearizeOptionsNamesList, self.linearizeOptionsValuesList):
            print linN, ' = ', linV
        
    
    #to simulate or re-simulate model
    def simulate(self):
        #if (self.inputFlag == True):
        if (self.inputFlag):#if model has input quantities
            self.simInput()#create csv file
            getExeFile = '{}.{}'.format(self.modelName, "exe")
            check_exeFile_ = os.path.exists(getExeFile)
            if(check_exeFile_):
                cmd = getExeFile + " -csvInput=" + self.csvFile
            
                subprocess.call(cmd, shell = False)
                return
            else:
                print "Error: application file not generated yet"
                return
        else:
            getExeFile = '{}.{}'.format(self.modelName, "exe")
            check_exeFile_ = os.path.exists(getExeFile)
            if(check_exeFile_):
                cmd = getExeFile
                subprocess.call(cmd, shell = False)
                return
            else:
                print "Error: application file not generated yet"
    
    #to extract simulation results
    def getSolutions(self, varList):
        if isinstance(varList, list):
            for v in varList:
                if v == 'time':
                    continue
                if v not in [l.name for l in self.quantitiesList]:
                    print '!!! ', v, ' does not exist\n'
                    return 
            res_mat = '_res.mat'
            resFile = "".join([self.modelName, res_mat])
            check_resFile_ = os.path.exists(resFile)
            variables = ",".join(varList)
            #vars = []
            #results = []

            if(check_resFile_):
                exp = "readSimulationResult(\"" + resFile + '",{' + variables + "})"
                res = self.getconn.sendExpression(exp)
                npRes = np.array(res)
                exp2 = "closeSimulationResultFile()"
                self.getconn.sendExpression(exp2)
                return npRes
            else:
                print "Error: mat file does not exist"
      
        else:
            print 'Error! should be list of Model variables'
      
    #to set continuous quantities values
    def setContinuousValues(self, names, values):
        try:
            errMsgFormat = 'Error!!! Incorrect format'
            errMsgStr = 'Error!!! value should not be string'
            checking = self.checkAvailability(names, self.cNamesList)
            #if checking is False:
            if not checking:
                return
            for v in values:
                if not isinstance(v,int) or isinstance(v,float):
                    if isinstance(v,str):
                        print errMsgStr
                        return
                    print errMsgFormat
                    return
            variability = "variability"
            attrValue = "continuous"
            self.setValue(names, values, variability, attrValue, self.cNamesList, self.cValuesList)
        except Exception as e:
          print e
    
    #to set parameter quantities values
    def setParameterValues(self, names, values):
        try:
            errMsgFormat = 'Error!!! Incorrect format'
            errMsgStr = 'Error!!! value should not be string'
            checking = self.checkAvailability(names, self.pNamesList)
            #if checking is False:
            if not checking:
                return
            for v in values:
                if not isinstance(v,int) or isinstance(v,float):
                    if isinstance(v,str):
                        print errMsgStr
                        return
                    print errMsgFormat
                    return
            variability = "variability"
            attrValue = "parameter"
            self.setValue(names, values, variability, attrValue, self.pNamesList, self.pValuesList)
            return
        except Exception as e:
            print e
    
    #to set input quantities value
    def setInputValues(self, name, inputsValList):
        try:
            errMsgFormat = 'Error!!! Incorrect format'
            errMsgStr = 'Error!!! value should not be string'
            errMsgTime = 'Time values should be increasing order'
            for i in inputsValList:
                if len(i) != 2:#tuple length must be 2
                    print errMsgFormat
                    return
            checking = self.checkAvailability(name, self.iNamesList)
            if checking is False:
                return
            for v in inputsValList:
                if isinstance(v[0], str) or isinstance(v[1], str):
                    print errMsgStr
                    return
            if inputsValList != sorted(inputsValList):
                print errMsgTime
                return
            index = self.iNamesList.index(name)
            self.inputsVal[index] = inputsValList
            self.inputFlag = True
        except Exception as e:
            print e
  
    #to create csv file
    def simInput(self):
        timestamps = set()
        for i in self.inputsVal:
            for (t,x) in i:
                timestamps.add(t)
        timestamps=sorted(timestamps)
        
        interpolated_inputs = list(np.interp(timestamps, zip(*l)[0], zip(*l)[1]) for l in self.inputsVal)
        name_ ='time'
        
        name = ','.join(self.iNamesList)
        name = '{},{},{}'.format(name_,name,'end')
        
        a=''
        l=[]
        l.append(name)
        for i in range(0,len(timestamps)):
            a =("%s,%s" % (str(float(timestamps[i])),",".join(list(str(float(inp[i])) for inp in interpolated_inputs))))+',0'
            l.append(a)
            if(i<(len(timestamps)-2)):
                a=("%s,%s" % (str(float(timestamps[i+1])),",".join(list(str(float(inp[i])) for inp in interpolated_inputs))))+',0'
                l.append(a)
          
        self.csvFile = '{}.csv'.format(self.modelName)
        
        with open (self.csvFile, "w") as f:
            writer=csv.writer(f, delimiter='\n')
            writer.writerow(l)
        return
  
    #to set values for continuous and parameter quantities
    def setValue(self, names, values, attrName, attrValue, namesList, valuesList):
        index = 0
        if(len(names) == len(values)):
            for n in names:
                for l in self.quantitiesList:
                    if(l.name == n):
                        attrCheckVaria = l.variability
                        attrCheckCau = l.causality
                        if (attrCheckVaria == attrValue or attrCheckCau == attrValue):
                            if l.changable == "false":
                                print 'Value cannot be set for "' + l.name +  '" !!!'
                            else:
                                l.start = values[index]
                                index_ = namesList.index(n)
                                valuesList[index_] = l.start
                                break
                        else:
                            print 'Error!!! This is not ' + attrValue + ' variable'
                            return
                #to change in xml file
                rootSet = self.root
                for paramVar in rootSet.iter('ScalarVariable'):
                    if paramVar.get('name') == names[index]:
                        c=paramVar.getchildren()
                        for attr in c:
                            attr.set('start', str(values[index]))
                            self.tree.write(self.xmlFile,  encoding='UTF-8', xml_declaration=True)
                index = index + 1
        else:
            print 'Error: Both list must be of same length!!!'
            return None

        return
  
    #to set simulation options values
    def setSimulationOptions(self, **simOptions):
        return self.setOptions(simOptions, self.simNamesList, self.simValuesList,0)
    
    #to set optimization options values
    def setOptimizationOptions(self, **optimizationOptions):
        return self.setOptions(optimizationOptions, self.optimizeOptionsNamesList, self.optimizeOptionsValuesList)
    
    #to set linearization options values
    def setLinearizationOptions(self, **linearizationOptions):
        return self.setOptions(linearizationOptions, self.linearizeOptionsNamesList, self.linearizeOptionsValuesList)
    
    #to set options for simulation, optimization and linearization
    def setOptions(self, options, namesList, valuesList, index = None):
        try:
            for opt in options: 
                if opt in namesList: 
                    if opt == 'stopTime':
                        if float(options.get(opt))<=float(valuesList[0]):
                            print '!!! stoptTime should be greater than startTime'
                            return
                    if opt == 'startTime':
                        if float(options.get(opt))>=float(valuesList[1]):
                            print '!!! startTime should be less than stopTime'
                            return
                    index_ = namesList.index(opt)
                    valuesList[index_] = options.get(opt)
                else:
                    print '!!!', opt, ' is not an option'
                    continue
                if index is not None:
                    rootSSC = self.root
                    for sim in rootSSC.iter('DefaultExperiment'):
                        sim.set(opt, str(options.get(opt)))
                        self.tree.write(self.xmlFile,  encoding='UTF-8', xml_declaration=True)
                    index = index + 1
        except Exception as e:
            print e
     
    #to convert Modelica model to FMU
    def convertMo2Fmu(self):
        convertMo2FmuError = ''
        translateModelFMUResult = self.requestApi('translateModelFMU', self.modelName)
    
        return translateModelFMUResult
    
    #to convert FMU to Modelica model
    def convertFmu2Mo(self, fmuName):
        convertFmu2MoError = ''
        importResult = self.requestApi__('importFMU', fmuName)
        convertFmu2MoError = self.requestApi('getErrorString')
        if convertFmu2MoError:
            print convertFmu2MoError
            return
        return importResult
    
    #to optimize model
    def optimize(self):
        cName = self.modelName
        properties = '{}={}, {}={}, {}={}, {}={}, {}={}, {}="{}"'.format(self.optimizeOptionsNamesList[0],self.optimizeOptionsValuesList[0],self.optimizeOptionsNamesList[1],self.optimizeOptionsValuesList[1],self.optimizeOptionsNamesList[2],self.optimizeOptionsValuesList[2],self.optimizeOptionsNamesList[3],self.optimizeOptionsValuesList[3],self.optimizeOptionsNamesList[4],self.optimizeOptionsValuesList[4],self.optimizeOptionsNamesList[5],self.optimizeOptionsValuesList[5])
        
        optimizeError = ''
        optimizeResult = self.requestApi('optimize', cName, properties)
        optimizeError = self.requestApi('getErrorString')
        if optimizeError:
            print optimizeError
            return
        return optimizeResult
    
    #to linearize model
    def linearize(self):
        cName = self.modelName
        self.requestApi("setCommandLineOptions", "+generateSymbolicLinearization")
        properties = "{}={}, {}={}, {}={}, {}={}, {}={}, {}='{}'".format(self.linearizeOptionsNamesList[0],self.linearizeOptionsValuesList[0],self.linearizeOptionsNamesList[1],self.linearizeOptionsValuesList[1],self.linearizeOptionsNamesList[2],self.linearizeOptionsValuesList[2],self.linearizeOptionsNamesList[3],self.linearizeOptionsValuesList[3],self.linearizeOptionsNamesList[4],self.linearizeOptionsValuesList[4],self.linearizeOptionsNamesList[5],self.linearizeOptionsValuesList[5])
        linearizeError = ''
        linearizeResult = self.requestApi('linearize', cName, properties)
        linearizeError = self.requestApi('getErrorString')
        if linearizeError:
            print linearizeError
            return
        return linearizeResult