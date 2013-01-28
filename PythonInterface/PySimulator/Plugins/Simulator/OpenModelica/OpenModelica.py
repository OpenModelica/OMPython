"""
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

 Author : Anand Kalaiarasi Ganeson, ganan642@student.liu.se,
 Maintainer: Adeel Asghar, adeel.asghar@liu.se
 Version: 1.0
"""

'''
***************************
This OpenModelica plugin can load Modelica models (assuming that OpenModelica 1.8 or later is installed)
and simulation executable of OpenModelica. It runs the executable and loads the result file.
***************************
'''

import Plugins.Simulator.SimulatorBase
import OMPython
import Plugins.SimulationResult.DymolaMat as DymolaMat
import os, shutil
import subprocess
import SocketServer
import re
import threading


modelExtension = ['mo', 'exe']  # e.g. ['mo']
parameters_changed = False
simulationProgressData = 0.0

def closeSimulationPlugin():
    try:
        OMPython.execute("quit()")
    except SystemExit:
        pass
    pass

# Change the parameters of the model file
def setNewParameters(cmd):
    OMPython.execute(cmd);
    global parameters_changed   # Set this variable if the parameters are changed
    parameters_changed = True
    return

# Set the parameters in the model_init.xml file
def setInitXmlValues(modelName,varName,value):
    modelName = modelName+"_init.xml"
    OMPython.execute("setInitXmlStartValue(\""+modelName+"\",variableName=\""+varName+"\",startValue=\""+value+"\",outputFile=\"temp.xml\")")

    if os.path.exists(modelName):
        os.remove(modelName)
        os.rename("temp.xml", modelName)
    return

class Model(Plugins.Simulator.SimulatorBase.Model):

    def __init__(self, modelName, modelFileName):

        Plugins.Simulator.SimulatorBase.Model.__init__(self, modelName, modelFileName, 'OpenModelica')

        self.onlyResultFile=False
        self.integrationSettings.resultFileExtension = 'mat'

        self._avilableIntegrationAlgorithms = ['Dassl', 'Euler','Rungekutta','Dopri5','Inline-Euler','Inline-Rungekutta']
        self.integrationSettings.algorithmName = self._avilableIntegrationAlgorithms[0]

        self._IntegrationAlgorithmHasFixedStepSize = [False,True,False,False,True,False]
        self._IntegrationAlgorithmCanProvideStepSizeResults = [False,True,False,False,True,False]

        self.compileModel()

        if self.resFile !='""':
            self._initialResult = loadResultFileInit(os.path.abspath('.') + "/"+self.name+ "_res.mat")
        else:
            print "The selected model could not be instantiated, check for any dependencies that the model might have"
            return

        #SocketServer setup to visualize the simulation progress bar
        HOST, PORT = "localhost",0
        self.server = SocketServer.TCPServer((HOST, PORT), ThreadedTCPRequestHandler)
        self.ip, self.port = self.server.server_address
        self.server_port = self.port

        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon=True
        self.server_thread.setDaemon(True)

        if self.server_thread.isAlive():
            self.server_thread._Thread__stop()

        self.file_thread=None

    def compileModel(self):
        """
        This function is needed to load the data into the VariablesBrowser
        before simulating the model with parameters.
        """

        if not os.path.isfile(self.fileName):
            raise FileDoesNotExist("File '" + self.fileName + "' does not exist")

        preCompiledResultFileName = os.path.abspath('.') + "/"+self.name+ "_res.mat"
        self.resFile = "True"

        #simulate the model if necessary
        if not os.path.isfile(preCompiledResultFileName):
            # load the OpenModelica Standard library
            OMPython.execute("loadModel(Modelica)")
            OMPython.execute("loadFile(\""+self.fileName+"\")")
            simResult = OMPython.execute("simulate("+self.name+")")
            self.resFile = OMPython.get(simResult,"SimulationResults.resultFile")

    def getReachedSimulationTime(self):
        '''
        Read the current simulation time during a simulation
        from the Model.exe file generated during loadFile()
        '''
        fName = os.path.abspath('.') + "/"+self.name+ ".exe"

        if self.file_thread is None:
            self.file_thread = threading.Thread(runExeFile(fName, self.server_port))
            self.server_thread.start()
            self.file_thread.start()
            self.server.shutdown()

        if simulationProgressData>=float(100.0):
            self.server_thread._Thread__stop()

        return ((simulationProgressData*self.integrationSettings.stopTime)/100.0)

    def simulate(self):

        def compile_model(simulate_options):
            if self.fileName !=None:
                OMPython.execute("loadFile(\""+self.fileName+"\")")

            s = self.integrationSettings

            # prepare the simulate command string
            if simulate_options != '':
                simulate_string = "simulate(" + self.name + simulate_options + ")"
            else:
                simulate_string = "simulate(" + self.name + ")"

            #simulate the model
            sim_results = OMPython.execute(simulate_string)

            #rename the OpenModelica result file
            result_file = OMPython.get(sim_results, 'SimulationResults.resultFile')
            result_file = (result_file).strip('\"')
            result_file = os.path.join(result_file)

            old_file_name = os.path.basename(result_file)
            old_file_name = old_file_name.strip('\"')
            file_path = result_file.replace(old_file_name, '').strip()
            file_path = file_path.strip('\"')
            file_path = os.path.join(result_file)

            if self.name + "_" in result_file:
                if os.path.exists(s.resultFileName):
                    shutil.copy(s.resultFileName, (file_path + "temp.mat"))
                    os.remove(result_file)
                    os.remove(s.resultFileName)
                    os.rename((file_path + "temp.mat"), s.resultFileName)
                else:
                    os.rename(result_file, s.resultFileName)

        def precheck_for_set_sim_options():
            s = self.integrationSettings
            settings = s.__dict__

            # prepare the simulation options string for OpenModelica
            set_sim_options = ['startTime', 'stopTime', 'errorToleranceTol', 'resultFileFormat', 'fixedStepSize', 'algorithmName']
            om_sim_options = ['startTime', 'stopTime', 'tolerance', 'outputFormat', 'fixedStepSize', 'method']
            simulate_options = ""
            for k, v in settings.iteritems():
                if k in set_sim_options:
                    i = set_sim_options.index(k)
                    if v != None and v != "":
                        if k == "algorithmName":
                            v = "\"" + str(v).lower() + '\"'
                        simulate_options = simulate_options + "," + om_sim_options[i] + "=" + str(v)

            return simulate_options

        def precheck_for_model():
            work_dir = os.getcwd()
            result_exe = work_dir + '\\' + self.name + ".exe"
            sim_opts = precheck_for_set_sim_options()
            if os.path.isfile(result_exe):
                exe_modify_time = os.path.getmtime(result_exe)
                mo_modify_time = os.path.getmtime(self.fileName)

                if (mo_modify_time > exe_modify_time) or (parameters_changed == True):
                    if sim_opts!='':
                        compile_model(sim_opts)
                    else:
                        compile_model('')
                else:
                    if sim_opts!='':
                        compile_model(sim_opts)

                    # prepare the flags and the parameters for simulating from the executable file
                    flags = " -f " + self.name + "_init.xml " + "-r " + self.integrationSettings.resultFileName + self.integrationSettings.resultFileFormat
                    subprocess.call(result_exe + flags)
            else:
                if sim_opts!='':
                    compile_model(sim_opts)
                else:
                    compile_model('')

        def readStatistics():
            '''
            Read statistics from the LOG_STATS.txt file
            '''
            work_dir = os.getcwd()
            result_exe = work_dir + '\\' + self.name + ".exe -lv LOG_STATS"

            with open('LOG_STATS.txt', 'w') as output_f:
                p = subprocess.Popen(result_exe,
                    stdout=output_f, shell=True)

            import time
            attempts = 0
            while True:
                if not os.path.isfile('LOG_STATS.txt'):
                    time.sleep(0.15)
                    attempts +=1
                    if attempts == 10:
                        return
                else:
                    statistics = open('LOG_STATS.txt', 'r')
                    break

            nTimeEvents = 0
            nStateEvents = 0
            currentGridPoints = 0
            currentTime = self.integrationSettings.startTime

            if statistics != None:
                fact = [line.strip() for line in statistics]
                for i in fact:
                    if "State Events" in i:
                        nStateEvents = int(i.split(':',1)[1])
                    if "Sample Events" in i:
                        nTimeEvents = int(i.split(':',1)[1])
                    if "simulation time" in i:
                        currentTime = float(i.split(':',1)[1])
                statistics.close()

            currentTime = self.integrationSettings.stopTime

            self.integrationStatistics.nTimeEvents = nTimeEvents
            self.integrationStatistics.nStateEvents = nStateEvents
            self.integrationStatistics.nGridPoints = currentGridPoints
            self.integrationStatistics.reachedTime = currentTime

        precheck_for_model()
        readStatistics()

    def setVariableTree(self):
        if self.resFile == '""':
            return
        for i in xrange(len(self._initialResult.name)):
            if   self._initialResult.value[i,0] == 1:
                causality = 'parameter'
            elif self._initialResult.value[i,1] == 2:
                causality = 'state'
            elif self._initialResult.value[i,0] == 3:
                causality = 'stateDerivative'
            elif self._initialResult.value[i,0] == 4:
                causality = 'output'
            elif self._initialResult.value[i,0] == 5:
                causality = 'input'
            else:
                causality = 'local'
                #variability = 'fixed' if causality == 'parameter' else 'continuous'
            # The format of self._initialResult.value[i,5] is unclear. Try to include inital values for states
            #valueEdit = True if int(self._initialResult.value[i,0]) == -1 and int(self._initialResult.value[i,5]) >= 280 else False

            binStr = bin(int(self._initialResult.value[i,0]))[2:]
            binStr = '0'*(15-len(binStr)) + binStr
            variability = 'continuous'
            if causality == 'parameter':
                variability = 'fixed'
            elif binStr[-7] == '1': # 64
                variability = 'discrete'

            valueEdit = False
            if int(self._initialResult.value[i,0]) == -1:
                if binStr[-4] == '1' or binStr[-6] == '1': # 8 or 32
                    valueEdit = True

            dataType = 'Real'
            if binStr[-2:] == '01': # 1
                dataType = 'Boolean'
            elif binStr[-2:] == '10': # 2
                dataType = 'Real'

            value = None
            if variability == 'fixed' or valueEdit:
                value = self._initialResult.value[i,1]

            unit = self._initialResult.unit[i]
            variableAttribute = ''
            if self._initialResult.description[i] != '' :
                variableAttribute += 'Description:' + chr(9) + self._initialResult.description[i] + '\n'
            variableAttribute += 'Causality:' + chr(9) + causality + '\n'
            variableAttribute += 'Variability:' + chr(9) + variability + '\n'
            variableAttribute += 'Type:' + chr(9) + dataType
            self.variableTree.variable[self._initialResult.name[i].replace('[', '.[')] = Plugins.Simulator.SimulatorBase.TreeVariable(value, valueEdit, unit, variability, variableAttribute)


    def loadResultFile(self, resultFileName, convert=False):
        self.integrationResults = DymolaMat.DymolaMat.loadDymolaResult(self.integrationSettings.resultFileName)

    def getAvailableIntegrationAlgorithms(self):
        return self._avilableIntegrationAlgorithms

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        return self._IntegrationAlgorithmHasFixedStepSize[self._avilableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._avilableIntegrationAlgorithms.index(algorithmName)]


# Adapted from DymolaMat/DymolaMat.py for OpenModelica #

import scipy.io, string

# Exception classes
class FileDoesNotExist     (Exception): pass
class WrongResultFile(Exception): pass


def charArrayToStrList(charArray):
    """Transform a numpy character array to a list of strings
    """
    strList = [];
    for item in charArray:
        strList.append(str(string.rstrip(string.join(item,""))))
    return strList;


def loadResultFileInit(fileName):
    """ Load Dymola initial data in an object.    
       
    """
    # Correct file path if needed
    fileName = fileName.replace("/","\\")

    # If no fileName given, inquire it interactively
    if fileName == None:
        return
        #fileName = selectResultFile()


    # Check if fileName exists
    if not os.path.isfile(fileName):
        raise FileDoesNotExist("File '" + fileName + "' does not exist")

    # Determine complete file name
    fullFileName = os.path.abspath(fileName)

    # Read data from file
    fileData = scipy.io.loadmat(fullFileName, matlab_compatible=True)

    # Check Aclass array
    if not("Aclass" in fileData):
        raise WrongResultFile("Matrix 'Aclass' is missing in file " + fullFileName)
    Aclass  = charArrayToStrList( fileData["Aclass"] )
    if len(Aclass) < 3:
        raise WrongResultFile("Matrix 'Aclass' has not 3 or more rows in file " + fullFileName)
    if Aclass[1] != "1.1":
        raise WrongResultFile("Amatrix[1] is not '1.1' in file " + fullFileName)

    # Check whether other matrices are on the result file
    if not("name" in fileData):
        raise WrongResultFile("Matrix 'name' is not in file " + fullFileName)
    if not("description" in fileData):
        raise WrongResultFile("Matrix 'description' is not in file " + fullFileName)
    if not("dataInfo" in fileData):
        raise WrongResultFile("Matrix 'dataInfo' is not in file " + fullFileName)


    # Get the raw matrices
    name        = fileData["name"]
    description = fileData["description"]
    value    = fileData["dataInfo"]


    # Transpose the data, if necessary
    if len(Aclass) > 3 and Aclass[3] == "binTrans":
        name        = name.T
        description = description.T
        value       = value.T


    # Transform the charArrays in string lists
    name        = charArrayToStrList(name)
    description = charArrayToStrList(description)

    # Extract units and update description
    unit = ['' for i in xrange(len(description))]
    for index, s in enumerate(description):
        t = s.rsplit('[', 1)
        if len(t) > 1:
            if len(t[1]) > 0:
                if t[1][-1] == ']':
                    if '|' in t[1]:
                        if ':#' not in t[1]:
                            unit[index] = t[1].split('|',1)[0]
                    elif ':#' not in t[1]:
                        unit[index] = t[1][:-1]

                    if len(t[0]) > 0:
                        description[index] = t[0][:-1] # Delete space
                    else:
                        description[index] = ''


    # Generate a DymolaResult object
    result = ResultFileInit(name, value, unit, description)
    return result

class ResultFileInit():
    def __init__(self, name, value, unit, description):
        self.name = name
        self.value = value
        self.unit = unit
        self.description = description



def MyStrtod(s):
    regex = re.compile(r"[+-]?\b\d+(?:\.\d+)?(?:e[+-]?\d+)?\b", re.I)
    for match in regex.finditer(s):
        return float (match.group())

def runExeFile(exeFile,server_port):
    args = "-port"
    import subprocess
    p = subprocess.Popen([exeFile, args, str(server_port)], shell=True, stdout=None, stderr=None)
    return

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        global simulationProgressData
        while self.request.recv(1024).strip()!=None:
            self.data = self.request.recv(1024).strip()
            if self.data:
                simulationProgressData=MyStrtod(self.data)/100.0
                if simulationProgressData >= 100.0:
                    break
            elif self.data == '':
                if self.request.recv(1024).strip()== '':
                    simulationProgressData=100.0
                    break
            else:
                continue
        return

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass
