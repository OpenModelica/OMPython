''' 
Copyright (C) 2011-2012 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.), 
Institute of System Dynamics and Control
All rights reserved.

This file is part of PySimulator.

PySimulator is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PySimulator is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with PySimulator. If not, see www.gnu.org/licenses.
'''

'''
*************************** 
This Simulator plugin can load Modelica models (assumed Dymola is installed)
and simulation executable of Dymola. It runs the executable and loads the result file.
***************************
'''


import os, sys, string
import subprocess

import Plugins.Simulator.SimulatorBase
import Plugins.SimulationResult.DymolaMat.DymolaMat as DymolaMat

modelExtension = ['mo', 'moe', 'exe']
def closeSimulatorPlugin():
    pass

class Model(Plugins.Simulator.SimulatorBase.Model):   
      
    def __init__(self, modelName, modelFileName):             
        
        Plugins.Simulator.SimulatorBase.Model.__init__(self, modelName, modelFileName, 'Dymola')
                            
        # A dummy object to get result properties:
        self.integrationResults = DymolaMat.DymolaResult('', None, None, None, None, None) 
        self.integrationSettings.resultFileExtension = 'mat'                
        
        self._avilableIntegrationAlgorithms = ["Dassl", "Explicit Euler", "Lsodar", "Rkfix2", "Rkfix3", "Rkfix4"]        
        '''
        ,"Radau IIa","Esdirk23a","Esdirk34a","Esdirk45a",
        "Dopri45","Dopri853","Sdirk34hw","Cerk23","Cerk34","Cerk45"]
        '''     
        self._IntegrationAlgorithmHasFixedStepSize = [False, True, False, True, True, True] #, False, False, False, False, False, False, False, False, False, False]
        self._IntegrationAlgorithmCanProvideStepSizeResults = [False, False, False, False, False, False] #, False, False, False, False, False, False, False, False, False, False]
        
        self.integrationSettings.algorithmName = self._avilableIntegrationAlgorithms[0]

        # Compile model, generate initialization file (including all avariable names) and read this file
        self._compileModel()       
        subprocess.call(self.fileNameExec + ' -ib dsin.mat')
        self._initialResult = DymolaMat.loadDymolaInit(os.path.abspath('.') + '/dsin.mat')
        
        
    def setVariableTree(self):
        ''' Generate variable tree from initialization file        
        '''                
        for i in xrange(len(self._initialResult.name)):
            if   self._initialResult.value[i,4] == 1:
                causality = 'parameter'
            elif self._initialResult.value[i,4] == 2:
                causality = 'state'
            elif self._initialResult.value[i,4] == 3:
                causality = 'stateDerivative'
            elif self._initialResult.value[i,4] == 4:
                causality = 'output'
            elif self._initialResult.value[i,4] == 5:
                causality = 'input'
            else:
                causality = 'local'
            
            # De-chiffre of Dymola's initialValue matrix, see also Dymola/source/adymosim.h
            # Set variable properties accordingly.
            binStr = bin(int(self._initialResult.value[i,5]))[2:]
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
                dataType = 'Integer'
                        
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
  
    def _compileModel(self):
        ''' Compiles a Modelica model by calling Dymola and running a mos-file
            If there is already a simulation executable that is newer than the
            Modelica model file, then this executable is used.
        '''
        sp = string.rsplit(self.fileName, '.', 1)           
        suffix = sp[1]
        if suffix not in ['mo', 'moe']:                
            # Can only compile *.mo and *.moe files
            self.fileNameExec = self.fileName               
            return
        
        # Check whether a up-to-date executable is available
        if 'win' in sys.platform:
            suffix = '.exe'
        else:
            suffix = ''           
        
        pwd = os.path.abspath('.')
        self.fileNameExec = pwd + '/' + self.name + suffix 
        
        if os.path.exists(self.fileNameExec):            
            timeStampModel = os.path.getmtime(self.fileName)
            timeStampExec  = os.path.getmtime(self.fileNameExec)
            if timeStampModel < timeStampExec:
                return           
        
        print "Translate Modelica model " + self.name + " by Dymola ... "         
        
        mosFileName = 'openTranslate.mos'
        mosFile = open(mosFileName, "w")        
        if self.fileName != '':        
            mosFile.write("openModel(\"" + self.fileName + "\");\n")
        mosFile.write("cd(\"" + pwd + "\");\n")
        mosFile.write("translateModel(\"" + self.name + "\");\n")
        mosFile.write("exit();\n")        
        mosFile.close()
        
        subprocess.call('c:/Program Files (x86)/Dymola 2012 FD01/bin/dymola /nowindow ' + pwd + '/' + mosFileName)
        
        if os.path.exists(self.fileNameExec):
            os.remove(self.fileNameExec)
        if os.path.exists(pwd + '/dymosim' + suffix):
            os.rename(pwd + '/dymosim' + suffix, self.fileNameExec)
            print "done.\n"
        else:
            print "failed.\n"

    def getReachedSimulationTime(self):
        ''' Read the current simulation time during a simulation
            from the file "status"        
        '''
        rTime = None
        # Read current time from file "status"
        try:
            f = open('status.', 'r')
            s = f.readline()
            if 'Time' in s:
                rTime = float(s.rsplit('=',1)[1])                
            f.close()
        except:
            pass
        return rTime
     
    def simulate(self):
        ''' Simulate a Modelica model by executing Dymola's simulation executable.        
        '''
        
        # First, define some functions:
        
        def writeDsin(changedStartValue):
            ''' Write input file for Dymola's simulation executable            
            '''        
            s = self.integrationSettings
            
            if s.gridPointsMode == 'NumberOf':   
                nGridPoints = s.gridPoints
                gridWidth = 0
                method1 = 1
            elif s.gridPointsMode == 'Width':
                nGridPoints = 1
                gridWidth = s.gridWidth
                method1 = 1
            else:
                nGridPoints = 2
                gridWidth = 0
                method1 = 3
            nGridPoints = max(1,nGridPoints)
            
            algorithm = dict()
            algorithm['Explicit Euler'] = 11
            algorithm['Dassl'] = 8
            algorithm['Lsodar'] = 4
            algorithm['Rkfix2'] = 12
            algorithm['Rkfix3'] = 13
            algorithm['Rkfix4'] = 14 
            algorithm['Radau IIa'] = 15  
            algorithm['Esdirk23a'] = 16 
            algorithm['Esdirk34a'] = 17 
            algorithm['Esdirk45a'] = 18 
            algorithm['Dopri45'] = 19 
            algorithm['Dopri853'] = 21 
            algorithm['Sdirk34hw'] = 24 
            algorithm['Cerk23'] = 26 
            algorithm['Cerk34'] = 27 
            algorithm['Cerk45'] = 28   
            
            experiment = [s.startTime,s.stopTime, gridWidth, nGridPoints-1, s.errorToleranceRel, s.fixedStepSize, algorithm[s.algorithmName]]
            method = [method1,1,3,1,1,0,0,0,0,0,0,0,0,100,0,0,0,0,0,1e-12,1e-10,20,0,1,1,1,2473]
            settings = [1,1,1,1,1,1,1,1,0,1,1,0,1]
            initialName = changedStartValue.keys()
            initialValue = [float(x) for x in changedStartValue.values()] 
            
                            
            f = open('dsin.txt', "w")        
            f.write('#1\n')
            f.write('char Aclass(3,36)\n')
            f.write('Adymosim\n')
            f.write('1.4\n')
            f.write('Input file generated by PySimulator\n')
            f.write('\n\n')
            
            f.write('#    Experiment parameters\n')
            f.write('double experiment(7,1)\n')
            for value in experiment:
                f.write('{0:0.16e}'.format(value) + '\n')          
            f.write('\n\n')
            
            f.write('#    Method tuning parameters\n')
            f.write('double method(27,1)\n')
            for value in method:
                f.write('{0:0.16e}'.format(value) + '\n')       
            f.write('\n\n')
            
            f.write('#    Output parameters\n')
            f.write('int settings(13,1)\n')
            for value in settings:
                f.write(str(value) + '\n')  
            
            f.write('\n\n')
            
            nVariables = len(initialName)
            if nVariables != len(initialValue):
                print("Length of initialValues and initialNames is not identical ... ")
                raise(Exception)              
            if nVariables > 0:
                maxLength = max([len(x) for x in initialName])
                f.write('#    Names of initial variables\n')
                f.write('char initialName(' + str(nVariables) + ',' + str(maxLength) + ')\n')
                for value in initialName:
                    f.write(value + '\n')
                f.write('\n\n')
                            
                f.write('#    Values of initial variables\n')
                f.write('double initialValue(' + str(nVariables) + ',6)\n')
                for value in initialValue:
                    f.write('-1  ' + '{0:0.16e}'.format(value) + '  0  0  1  0' + '\n')        
                f.write('\n\n')       
              
            f.close()
        
        def readStatistics():
            ''' Reads some integration statistics from the file "dslog.txt"
            '''          
            
            f = open('dslog.txt', "r")
            
            content = f.readlines()
            
            nTimeEvents = 0
            nStateEvents = 0
            currentGridPoints = 0
            currentTime = self.integrationSettings.startTime
            endCondition = False
            for c in content:
                if 'Number of result points' in c:
                    currentGridPoints = int(c.split(':',1)[1])
                if 'Number of state    events' in c:
                    nStateEvents = int(c.split(':',1)[1])
                if 'Number of (model) time events' in c:
                    nTimeEvents = nTimeEvents + int(c.split(':',1)[1])
                if 'Number of (U) time events' in c:
                    nTimeEvents = nTimeEvents + int(c.split(':',1)[1])
                if 'Integration terminated' in c:
                    if 'Integration terminated successfully' in c and not endCondition:
                        # Time in dslog.txt is not accurate enough
                        currentTime = self.integrationSettings.stopTime 
                    else:
                        currentTime = float(c.rsplit('T =',1)[1])
                if 'End condition reached' in c:
                    endCondition = True
                                  
                            
            self.integrationStatistics.nTimeEvents = nTimeEvents
            self.integrationStatistics.nStateEvents = nStateEvents
            self.integrationStatistics.nGridPoints = currentGridPoints
            self.integrationStatistics.reachedTime = currentTime
            
            f.close()
        
        # End of defining functions in simulate           
            
        
        # Compile the model if neccessary:        
        self._compileModel()        
       
        # Write input file and start simulation
        writeDsin(self.changedStartValue)
        subprocess.call(self.fileNameExec + ' -s dsin.txt ' + self.integrationSettings.resultFileName)
        
        # Simulation statistics from dslog.txt
        readStatistics()
        
        # Integration is finished


    def getAvailableIntegrationAlgorithms(self): 
        ''' Returns a list of strings with available integration algorithms
        '''       
        return self._avilableIntegrationAlgorithms
    
    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        ''' Returns True or False dependent on the fact, 
            if the integration algorithm given by the string algorithmName
            has a fixed step size or not (if not it has a variable step size).
        '''
        return self._IntegrationAlgorithmHasFixedStepSize[self._avilableIntegrationAlgorithms.index(algorithmName)]
    
    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        ''' Returns True or False dependent on the fact,
            if the integration algorithm given by the string algorithmName
            can provide result points at every integration step.
        '''
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._avilableIntegrationAlgorithms.index(algorithmName)]
  
    
