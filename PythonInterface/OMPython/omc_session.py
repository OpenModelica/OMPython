__author__ = 'Zsolt'

import os
import sys
import time
import logging
import uuid
import subprocess
import tempfile
import pyparsing

if sys.platform == 'darwin':
    # on Mac let's assume omc is installed
    # OMPython packages are coming from here
    sys.path.append('/opt/local/lib/python2.7/site-packages/')
    # omc is here
    #sys.path.append('/opt/local/bin')

# TODO: replace this with the new parser
from OMPython import OMTypedParser, OMParser


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
            self.omhome = os.environ['OPENMODELICAHOME']
            # add OPENMODELICAHOME\lib to PYTHONPATH so python can load omniORB libraries
            sys.path.append(os.path.join(self.omhome, 'lib'))
            sys.path.append(os.path.join(self.omhome, 'lib', 'python'))
            # add OPENMODELICAHOME\bin to path so python can find the omniORB binaries
            pathVar = os.getenv('PATH')
            pathVar += ';'
            pathVar += os.path.join(self.omhome, 'bin')
            os.putenv('PATH', pathVar)
            self._set_omc_corba_command(os.path.join(self.omhome, 'bin', 'omc'))
            self._start_server()
        except:
            # FIXME: what is this case? are we looking at platform specifics? or different versions of OpenModelica?
            try:
                import OMConfig

                PREFIX = OMConfig.DEFAULT_OPENMODELICAHOME
                self.omhome = os.path.join(PREFIX)
                self._set_omc_corba_command(os.path.join(self.omhome, 'bin', 'omc'))
                self._start_server()
            except:
                # FIXME: what is this case? are we looking at platform specifics? or different versions of OpenModelica?
                try:
                    self._set_omc_corba_command('/opt/local/bin/omc')
                    self._start_server()
                except Exception as ex:
                    self.logger.error("The OpenModelica compiler is missing in the System path, please install it")
                    raise ex

    def _connect_to_omc(self):
        # import the skeletons for the global module
        from omniORB import CORBA
        from OMPythonIDL import _OMCIDL
        # Locating and using the IOR
        if sys.platform == 'win32':
            self._ior_file = "openmodelica.objid." + self._random_string
        else:
            self.currentUser = os.environ['USER']
            if not self.currentUser:
                self.currentUser = "nobody"

            self._ior_file = "openmodelica." + self.currentUser + ".objid." + self._random_string
        self._ior_file = os.path.join(self._temp_dir, self._ior_file)
        self._omc_corba_uri = "file:///" + self._ior_file
        # See if the omc server is running
        if os.path.isfile(self._ior_file):
            self.logger.info("OMC Server is up and running at {0}".format(self._omc_corba_uri))
        else:
            attempts = 0
            while True:
                if not os.path.isfile(self._ior_file):
                    time.sleep(0.25)
                    attempts += 1
                    if attempts == 10:
                        self.logger.error("OMC Server is down. Please start it!")
                        raise Exception
                    else:
                        self.logger.info("OMC Server is up and running at {0}".format(self._omc_corba_uri))
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
            self.logger.error("Object reference is not valid")
            raise Exception

    def __init__(self, readonly=False):
        self.readonly = readonly
        self.omc_cache = {}

        self.logger = logging.getLogger('py_modelica_exporter::OMCSession')
        self.logger.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        self.logger_console_handler = logging.StreamHandler()
        self.logger_console_handler.setLevel(logging.INFO)

        # create formatter and add it to the handlers
        self.logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger_console_handler.setFormatter(self.logger_formatter)

        # add the handlers to the logger
        self.logger.addHandler(self.logger_console_handler)

        # FIXME: this code is not well written... need to be refactored
        self._temp_dir = tempfile.gettempdir()
        # this file must be closed in the destructor
        self._omc_log_file = open(os.path.join(self._temp_dir, "openmodelica.omc.output.OMPython"), 'w')

        # generate a random string for this session
        self._random_string = uuid.uuid4().hex

        # start up omc executable, which is waiting for the CORBA connection
        self._start_omc()

        # connect to the running omc instance using CORBA
        self._connect_to_omc()

    def __del__(self):
        self._omc.sendExpression("quit();") # FIXME: does not work in a virtual python environment
        self._omc_log_file.close()
        # kill self._server process if it is still running/exists
        if self._server.returncode is None:
            self._server.kill()

    # TODO: this method will be replaced by the new parser
    def execute(self, command):
        result = self._omc.sendExpression(command)
        answer = OMTypedParser.parseString(result)
        return answer

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

        self.logger.debug('OMC ask: {0}  - parsed: {1}'.format(expression, parsed))

        try:
            if parsed:
                res = self.execute(expression)
            else:
                res = self._omc.sendExpression(expression)
        except Exception as e:
            self.logger.error("OMC failed: {0}, {1}, parsed={2}".format(question, opt, parsed))
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
            self.logger.warning("Method 'getClassComment' failed for {0}".format(className))
            self.logger.warning('OMTypedParser error: {0}'.format(ex.message))
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
            self.logger.warning('OMPython error: {0}'.format(ex.message))
            # FIXME: OMC returns with a different structure for empty parameter set
            return []

    def getParameterValue(self, className, parameterName):
        try:
            return self.ask('getParameterValue', '{0}, {1}'.format(className, parameterName))
        except pyparsing.ParseException as ex:
            self.logger.warning('OMTypedParser error: {0}'.format(ex.message))
            return ""

    def getComponentModifierNames(self, className, componentName):
        return self.ask('getComponentModifierNames', '{0}, {1}'.format(className, componentName))

    def getComponentModifierValue(self, className, componentName):
        try:
            # FIXME: OMPython exception UnboundLocalError exception for 'Modelica.Fluid.Machines.ControlledPump'
            return self.ask('getComponentModifierValue', '{0}, {1}'.format(className, componentName))
        except pyparsing.ParseException as ex:
            self.logger.warning('OMTypedParser error: {0}'.format(ex.message))
            result = self.ask('getComponentModifierValue', '{0}, {1}'.format(className, componentName), parsed=False)
            try:
                answer = OMParser.check_for_values(result)
                OMParser.result = {}
                return answer[2:]
            except (TypeError, UnboundLocalError) as ex:
                self.logger.warning('OMParser error: {0}'.format(ex.message))
                return result

    def getExtendsModifierNames(self, className, componentName):
        return self.ask('getExtendsModifierNames', '{0}, {1}'.format(className, componentName))

    def getExtendsModifierValue(self, className, extendsName, modifierName):
        try:
            # FIXME: OMPython exception UnboundLocalError exception for 'Modelica.Fluid.Machines.ControlledPump'
            return self.ask('getExtendsModifierValue', '{0}, {1}, {2}'.format(className, extendsName, modifierName))
        except pyparsing.ParseException as ex:
            self.logger.warning('OMTypedParser error: {0}'.format(ex.message))
            result = self.ask('getExtendsModifierValue', '{0}, {1}, {2}'.format(className, extendsName, modifierName), parsed=False)
            try:
                answer = OMParser.check_for_values(result)
                OMParser.result = {}
                return answer[2:]
            except (TypeError, UnboundLocalError) as ex:
                self.logger.warning('OMParser error: {0}'.format(ex.message))
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