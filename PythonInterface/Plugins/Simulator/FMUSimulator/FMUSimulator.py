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
This Simulator plugin can load Functional Mockup Units (FMUs) and simulate them
mainly by a solver of the Sundials solver suite. The result file is saved
in the MTSF format in HDF5.
***************************

For documentation of general Simulator plugins, see also SimulatorBase.py 
'''


import numpy
import getpass
import time
import os
import types
from operator import itemgetter


import FMUInterface
import FMIDescription
import Plugins.Simulator.SimulatorBase
import Plugins.SimulationResult.IntegrationResults
import Plugins.SimulationResult.Mtsf.Mtsf as Mtsf
import Plugins.SimulationResult.Mtsf.pyMtsf as pyMtsf
import Plugins.SimulationResult.Mtsf.MtsfFmi as MtsfFmi


from Plugins.Algorithms.Integrator.Sundials.SundialsIntegrators import SundialsCVode, SundialsIDA
from FMUInterface import fmiTrue, fmiFalse


modelExtension = ['fmu']

def closeSimulatorPlugin():
    ''' Function is called when closing the plugin (normally when PySimulator is closed).
        It can be used to release resources used by the plugin.
    '''    
    pass

class Model(Plugins.Simulator.SimulatorBase.Model):
    ''' Class to describe a whole "model", including all FMU information
        and some more information that is needed.
    '''
    def __init__(self, modelName=None, modelFileName=None, loggingOn=True):
        ''' Opens a given model and sets it up with its default values
            @param modelFileName: fully qualified file name and path of model
        '''

        def updateSettingsByFMI(description):
            '''
                Function to update the settings with the experiment settings
                in the model's FMI description
            '''
            if description is not None:
                if description.defaultStartTime is not None:
                    self.integrationSettings.startTime = float(description.defaultStartTime)
                if description.defaultStopTime is not None:
                    self.integrationSettings.stopTime = float(description.defaultStopTime)
                if description.defaultTolerance is not None:
                    self.integrationSettings.errorToleranceRel = float(description.defaultTolerance)

        if modelFileName is None:
            self.interface = None
            self.description = FMIDescription.FMIDescription(None)
        else:
            self.interface = FMUInterface.FMUInterface(modelFileName, self, loggingOn)
            self.description = self.interface.description

        # modelName will not be used, because the modelName of FMIDescription is used
        Plugins.Simulator.SimulatorBase.Model.__init__(self, self.description.modelName, modelFileName, 'FMU1.0')

        # Dummy object to get properties
        self.integrationResults = Mtsf.MTSF('')
        self.integrationSettings.resultFileExtension = 'mtsf'
        #Default values
        updateSettingsByFMI(self.description)
        self._avilableIntegrationAlgorithms = ["BDF (IDA, Dassl like)", "BDF (CVode)", "Adams (CVode)", "Explicit Euler (fixed step size)"]
        self._IntegrationAlgorithmHasFixedStepSize = [False, False, False, True]
        self._IntegrationAlgorithmCanProvideStepSizeResults = [True, True, True, True]

        self.integrationSettings.algorithmName = self._avilableIntegrationAlgorithms[0]


    def close(self):
        ''' Closing the model, release of resources
        '''
        print "Deleting model instance ", self.description.modelName
        self.interface.free()

    def _setDefaultStartValues(self):
        ''' Reads given start values from FMI model description and sets variables accordingly
        '''
        for index in self.description.scalarVariables:
            if self.description.scalarVariables[index].type.start != None:
                self.setValue(index, self.description.scalarVariables[index].type.start)

    def setValue(self, valueName, valueValue):
        ''' set the variable valueName to valueValue
            @param valueName: name of variable to be set
            @type valueName: string
            @param valueValue: new value
            @type valueValue: any type castable to the type of the variable valueName
        '''
        ScalarVariableReferenceVector = FMUInterface.createfmiReferenceVector(1)
        ScalarVariableReferenceVector[0] = self.description.scalarVariables[valueName].valueReference
        if self.description.scalarVariables[valueName].type.type == 'Real':
            ScalarVariableValueVector = FMUInterface.createfmiRealVector(1)
            ScalarVariableValueVector[0] = float(valueValue)
            self.interface.fmiSetReal(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.type in ['Integer', 'Enumeration']:
            ScalarVariableValueVector = FMUInterface.createfmiIntegerVector(1)
            ScalarVariableValueVector[0] = int(valueValue)
            self.interface.fmiSetInteger(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.type == 'Boolean':
            ScalarVariableValueVector = FMUInterface.createfmiBooleanVector(1)
            if valueValue == "true":
                ScalarVariableValueVector[0] = fmiTrue
            else:
                ScalarVariableValueVector[0] = fmiFalse
            self.interface.fmiSetBoolean(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.type == 'String':
            ScalarVariableValueVector = FMUInterface.createfmiStringVector(1)
            ScalarVariableValueVector[0] = str(valueValue)
            self.interface.fmiSetString(ScalarVariableReferenceVector, ScalarVariableValueVector)

    def getDerivatives(self, t, x):
        ''' Returns the right hand side of the dynamic system for
            given time t and state vector x.
        '''   
        self.interface.fmiSetTime(t)
        if self.description.numberOfContinuousStates == 0:
            dx = numpy.ndarray([1, ])
        else:
            self.interface.fmiSetContinuousStates(x)
            dx = self.interface.fmiGetDerivatives()
        return dx

    def getEventIndicators(self, t, x):
        ''' Returns the event indicator functions for
            given time t and state vector x.
        ''' 
        self.interface.fmiSetTime(t)
        if not self.description.numberOfContinuousStates == 0:
            self.interface.fmiSetContinuousStates(x)
        return self.interface.fmiGetEventIndicators()

    def getValue(self, name):
        ''' Returns the values of the variables given in name;
            name is either a String or a list of Strings.            
        '''
        if types.TypeType(name) == types.ListType:
            n = len(name)
            nameList = True
            names = name
        else:
            n = 1
            nameList = False
            names = [name]

        iReal = []
        iInteger = []
        iBoolean = []
        iString = []
        refReal = []
        refInteger = []
        refBoolean = []
        refString = []
        for i, x in enumerate(names):
            dataType = self.description.scalarVariables[x].type.type
            if dataType == 'Real':
                refReal.append(self.description.scalarVariables[x].valueReference)
                iReal.append(i)
            elif dataType == 'Integer':
                refInteger.append(self.description.scalarVariables[x].valueReference)
                iInteger.append(i)
            elif dataType == 'Boolean':
                refBoolean.append(self.description.scalarVariables[x].valueReference)
                iBoolean.append(i)
            elif dataType == 'String':
                refString.append(self.description.scalarVariables[x].valueReference)
                iString.append(i)

        retValue = range(n)
        k = len(refReal)
        if k > 0:
            ref = FMUInterface.createfmiReferenceVector(k)
            for i in xrange(k):
                ref[i] = refReal[i]
            values = self.interface.fmiGetReal(ref)
            for i in xrange(k):
                retValue[iReal[i]] = values[i]
        k = len(refInteger)
        if k > 0:
            ref = FMUInterface.createfmiReferenceVector(k)
            for i in xrange(k):
                ref[i] = refInteger[i]
            values = self.interface.fmiGetInteger(ref)
            for i in xrange(k):
                retValue[iInteger[i]] = values[i]
        k = len(refBoolean)
        if k > 0:
            ref = FMUInterface.createfmiReferenceVector(k)
            for i in xrange(k):
                ref[i] = refBoolean[i]
            values = self.interface.fmiGetBoolean(ref)
            for i in xrange(k):
                retValue[iBoolean[i]] = values[i]
        k = len(refString)
        if k > 0:
            ref = FMUInterface.createfmiReferenceVector(k)
            for i in xrange(k):
                ref[i] = refString[i]
            values = self.interface.fmiGetString(ref)
            for i in xrange(k):
                retValue[iString[i]] = values[i]

        if nameList:
            return retValue
        else:
            return retValue[0]

    def getStates(self):
        ''' Returns a vector with the values of the states.
        '''        
        return self.interface.fmiGetContinuousStates()

    def getStateNames(self):
        ''' Returns a list of Strings: the names of all states in the model.
        '''
        references = self.interface.fmiGetStateValueReferences()
        allVars = self.description.scalarVariables.items()
        referenceListSorted = [(index, var[1].valueReference) for index, var in enumerate(allVars)]
        referenceListSorted.sort(key=itemgetter(1))
        referenceList = [r[1] for r in referenceListSorted]

        names = []
        for ref in references:
            if ref == -1:
                # No reference available -> name is hidden
                names.append('')
            else:
                k = referenceList.count(ref)
                if k > 0:
                    index = -1
                    i = 0
                    while i < k:
                        i += 1
                        index = referenceList.index(ref, index + 1)
                        if allVars[referenceListSorted[index][0]][1].alias is None:
                            name = allVars[referenceListSorted[index][0]][0]
                            names.append(name)
                            break
                else:
                    # Reference not found. Should not occur.
                    names.append('')
        return names

    def initialize(self, t, errorTolerance=1e-9):
        ''' Initializes the model at time = t with
            changed start values given by the dictionary
            self.changedStartValue.
            The function returns a status flag and the next time event.
        '''
        
        # Terminate last simulation in model
        self.interface.fmiTerminate()
        # Set start time
        self.interface.fmiSetTime(t)
        # Set start values
        self._setDefaultStartValues()
        for name in self.changedStartValue.keys():
            self.setValue(name, self.changedStartValue[name])
        # Initialize model
        (eventInfo, status) = self.interface.fmiInitialize(fmiTrue, errorTolerance)
        # Information about next time event
        if eventInfo.upcomingTimeEvent == fmiTrue:
            nextTimeEvent = eventInfo.nextEventTime
        else:
            nextTimeEvent = None
        # status > 1 means error during initialization
        return status, nextTimeEvent

    def getReachedSimulationTime(self):
        ''' Results are avialable up to the returned time        
        '''
        return self.integrationStatistics.reachedTime

    def simulate(self):
        ''' The main simulation function
        '''        
        
        def prepareResultFile():
            # Prepare result file
            fmi = self.description
            (modelDescription, modelVariables, simpleTypes, units, enumerations) = MtsfFmi.convertFromFmi('', fmi)
            # Phase 1 of result file generation
            settings = self.integrationSettings
            experimentSetup = pyMtsf.ExperimentSetup(startTime=settings.startTime, stopTime=settings.stopTime,
                                                     algorithm=settings.algorithmName, relativeTolerance=settings.errorToleranceRel,
                                                     author=getpass.getuser(), description="",
                                                     generationDateAndTime=time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()),
                                                     generationTool="PySimulator", machine=os.getenv('COMPUTERNAME'),
                                                     cpuTime="")
            modelVariables.allSeries[0].initialRows = 1  # Fixed
            modelVariables.allSeries[2].initialRows = 10  # Discrete
            if settings.gridPointsMode == 'NumberOf':
                nGridPoints = settings.gridPoints
            elif settings.gridPointsMode == 'Width':
                nGridPoints = 1 + int((settings.stopTime - settings.startTime) / settings.gridWidth)
            else:
                nGridPoints = 1
            modelVariables.allSeries[1].initialRows = max(nGridPoints, modelVariables.allSeries[2].initialRows)  # Continuous
            
            # Create result object
            mtsf = Mtsf.MTSF(settings.resultFileName,
                               modelDescription, modelVariables, experimentSetup, simpleTypes, units, enumerations)
            if not mtsf.isAvailable:
                print("Result file " + settings.resultFileName + " cannot be opened for write access.\n")
                self.integrationResults = Plugins.SimulationResult.IntegrationResults.Results()
                return False

            # Create fmi reference lists in categories
            for series in mtsf._mtsf.results.series.values():
                for category in series.category.values():
                    category.references = FMUInterface.createfmiReferenceVector(category.nColumn)
                    category.iReferences = -1
                    dataType = pyMtsf.CategoryReverseMapping[category.name]
                    if dataType == 'Real':
                        category.fmiGetValues = self.interface.fmiGetReal
                    elif dataType == 'Integer':
                        category.fmiGetValues = self.interface.fmiGetInteger
                    elif dataType == 'Boolean':
                        category.fmiGetValues = self.interface.fmiGetBoolean
                    elif dataType == 'String':
                        category.fmiGetValues = self.interface.fmiGetString
            for name, variable in modelVariables.variable.items():
                if variable.aliasName is None:
                    variable.category.iReferences += 1
                    if name in fmi.scalarVariables:
                        #print variable.seriesIndex, variable.category.name, name, variable.category.iReferences, len(variable.category.references)
                        variable.category.references[variable.category.iReferences] = fmi.scalarVariables[name].valueReference
                    else:
                        # e.g. for time variables, that do not exist in fmi-world
                        series = variable.category.series
                        series.independentVariableCategory = variable.category
                        variable.category.independentVariableColumn = variable.columnIndex
                        variable.category.references[variable.category.iReferences] = 0

            for series in mtsf._mtsf.results.series.values():
                if hasattr(series, 'independentVariableCategory'):
                    category = series.independentVariableCategory
                    column = category.independentVariableColumn
                    if column > 0:
                        dummy = 0
                    else:
                        dummy = 1
                    if category.references.shape[0] > dummy:
                        category.references[column] = category.references[dummy]
                    else:
                        category.references = numpy.array([])
                else:
                    series.independentVariableCategory = None
            self.integrationResults = mtsf
            return True

        def writeResults(seriesName, time):
            ''' Writes variable values at time 'time' to result file.
                Only variables of the given series are written.
            '''
            self.integrationResultFileSemaphore.acquire()
            series = self.integrationResults._mtsf.results.series[seriesName]
            for category in series.category.values():
                if category.references.shape[0] > 0:
                    values = category.fmiGetValues(category.references)
                else:
                    values = numpy.ndarray((1,))
                if category == series.independentVariableCategory:
                    # There is a time
                    index = category.independentVariableColumn
                    values[index] = time
                category.writeData(values)
            self.integrationResultFileSemaphore.release()

        def right_hand_side(t, x, xd=None):
            ''' Returns the right hand side (or the delta to xd for implicit solvers) 
            '''
            dx = self.getDerivatives(t, x)
            if implicitSolver:
                return dx - xd
            else:
                return dx

        def state_events(t, x):
            ''' Returns event indicator functions at time=t, states=x 
            '''
            return self.getEventIndicators(t, x)

        def time_events(t, x):
            ''' Returns the next time event
            '''
            return simulator.nextTimeEvent

        def handle_result(t, x):
            ''' This function is called when new values
                (in time) for variables shall be saved.
            '''
                        
            # Check, if simulation shall be interrupted
            if self.simulationStopRequest:
                finalize()
                raise(Plugins.Simulator.SimulatorBase.Stopping)

            # Update integration statistics
            self.integrationStatistics.reachedTime = t

            # Write results
            self.interface.fmiSetTime(t)
            if not self.description.numberOfContinuousStates == 0:
                self.interface.fmiSetContinuousStates(x)

            writeResults('Continuous', t)
            self.integrationStatistics.nGridPoints += 1

        def finalize():
            ''' Function that is called at the end of the simulation
            '''
            # Terminate last simulation in model
            self.interface.fmiTerminate()

        def handle_event(solver, event_info=None):
            ''' There is an event. Do the re-initialization and prepare
                the simulation to be proceeded.
                
                Returns True,  if simulation shall be continued
                        False, if simulation shall be terminated    
            '''
            
            if event_info[1]:
                self.integrationStatistics.nTimeEvents += 1
                #print "Handle time event at   ", solver.t_cur
            else:
                self.integrationStatistics.nStateEvents += 1
                #print "Handle state event at  ", solver.t_cur

            # To ensure that the current values are set in the model
            self.interface.fmiSetTime(solver.t_cur)
            if not self.description.numberOfContinuousStates == 0:
                self.interface.fmiSetContinuousStates(solver.y_cur)

            # Results at events are not handled by the Integrator,
            # so we handle it here before the event updates
            handle_result(solver.t_cur, solver.y_cur)

            # Do the event updates
            eventInfo = self.interface.fmiEventUpdate(fmiFalse)
            if eventInfo.upcomingTimeEvent == fmiTrue:
                solver.nextTimeEvent = eventInfo.nextEventTime
            else:
                solver.nextTimeEvent = None
            if eventInfo.stateValuesChanged == fmiTrue:
                # The model signals a value change of states, retrieve them
                if not self.description.numberOfContinuousStates == 0:
                    solver.y_cur = self.interface.fmiGetContinuousStates()
            if eventInfo.terminateSimulation == fmiTrue:
                print("terminated by model ... ")
                return False
                #raise(Exception)

            # Results at events are not handled by the Integrator,
            # so we handle it here after the event updates
            handle_result(solver.t_cur, solver.y_cur)

            if 'Discrete' in self.integrationResults._mtsf.results.series:
                # Write discrete Variables
                writeResults('Discrete', solver.t_cur)
                
            return True

        
        def completed_step(solver):
            ''' Function that is called after each successfull integrator step
                Returns True,  if there was a step event
                        False, if there was no step event 
            '''            
            if self.interface.fmiCompletedIntegratorStep() == fmiTrue:
                solver.handle_event(solver)
                return True
            else:
                return False
            
        ''' *********************************
            Here the simulate function starts:
            **********************************
        '''

        # Initialize result file
        if not prepareResultFile():
            return

        # Set Simulation options
        Tstart = self.integrationSettings.startTime
        Tend = self.integrationSettings.stopTime
        IntegrationMethod = self.integrationSettings.algorithmName
        if "BDF (CVode)" in IntegrationMethod:
            IntegrationMethod = 'BDF'
        elif 'Adams' in IntegrationMethod:
            IntegrationMethod = 'Adams'
        if self.integrationSettings.gridPointsMode == 'NumberOf':
            nIntervals = self.integrationSettings.gridPoints - 1
            gridWidth = None
        elif self.integrationSettings.gridPointsMode == 'Width':
            nIntervals = None
            gridWidth = self.integrationSettings.gridWidth            
        else:
            nIntervals = 0
            gridWidth = None
        ErrorTolerance = self.integrationSettings.errorToleranceRel

        # Initialize integration statistics
        self.integrationStatistics.nTimeEvents = 0
        self.integrationStatistics.nStateEvents = 0
        self.integrationStatistics.nGridPoints = 0
        self.integrationStatistics.reachedTime = Tstart

        # Run the integration
        ######################
        # Initialize model
        (status, nextTimeEvent) = self.initialize(Tstart, ErrorTolerance)
        if status > 1:
            print("Model initialization failed. fmiStatus = " + str(status))
            return
        
        if 'Fixed' in self.integrationResults._mtsf.results.series:
            # Write parameter values
            writeResults('Fixed', Tstart)
        if 'Discrete' in self.integrationResults._mtsf.results.series:
            # Write discrete variables
            writeResults('Discrete', Tstart)

        # Retrieve initial state x
        if self.description.numberOfContinuousStates == 0:
            x0 = numpy.ndarray([1, ])
        else:
            x0 = self.interface.fmiGetContinuousStates()
        #x_nominal = numpy.array(self.interface.fmiGetNominalContinuousStates())

        #Prepare the solver
        implicitSolver = False
        if "IDA" in IntegrationMethod:
            implicitSolver = True           
            # Define the solver object            
            simulator = SundialsIDA()
            
            # Retrieve initial derivatives dx
            if self.description.numberOfContinuousStates == 0:
                dx0 = numpy.ndarray([1, ])
            else:
                dx0 = self.interface.fmiGetDerivatives()            
            
            simulator.yd0 = dx0           
            # Set the integration parameters            
            simulator.atol = ErrorTolerance  # Default 1e-6
            simulator.rtol = ErrorTolerance  # Default 1e-6
            simulator.verbosity = 0            
        elif not "Euler" in IntegrationMethod:   # Use CVode
            # Define the solver object            
            simulator = SundialsCVode()           

            # Set the integration parameters
            simulator.iter = 'Newton'  # Default 'FixedPoint'
            simulator.discr = IntegrationMethod  # Default 'Adams'
            simulator.atol = ErrorTolerance  # Default 1e-6
            simulator.rtol = ErrorTolerance  # Default 1e-6
            simulator.verbosity = 0
        else:
            simulator = ExplicitEulerSolver()            

        simulator.t0 = Tstart            
        simulator.y0 = x0
        
        simulator.rhs = right_hand_side
        simulator.handle_result = handle_result
        simulator.state_events = state_events
        simulator.handle_event = handle_event
        simulator.time_events = time_events
        simulator.finalize = finalize
        simulator.completed_step = completed_step # is not supported by python-sundials


        # Store information about next time event in solver
        simulator.nextTimeEvent = nextTimeEvent
       
        print("Start integration of " + self.numberedModelName + " ... ")

        # Simulate until end of integration interval        
        if "Euler" in IntegrationMethod:
            if nIntervals == None:
                nIntervals = (Tend - Tstart) / gridWidth - 1
            simulator.simulate(Tstart, self.integrationSettings.fixedStepSize, Tend, x0, nIntervals, gridWidth)
        else:
            simulator.simulate(Tend, nIntervals, gridWidth)           

        return

    def getAvailableIntegrationAlgorithms(self):
        return self._avilableIntegrationAlgorithms

    def getIntegrationAlgorithmHasFixedStepSize(self, algorithmName):
        return self._IntegrationAlgorithmHasFixedStepSize[self._avilableIntegrationAlgorithms.index(algorithmName)]

    def getIntegrationAlgorithmCanProvideStepSizeResults(self, algorithmName):
        return self._IntegrationAlgorithmCanProvideStepSizeResults[self._avilableIntegrationAlgorithms.index(algorithmName)]

    def setVariableTree(self):
        ''' Sets the variable tree to be displayed in the variable browser.
            The data is set in self.variableTree that is an instance of the class SimulatorBase.VariableTree
        '''

        tipText = ''
        tipText += 'FMI Version:       ' + chr(9) + self.description.fmiVersion + '\n'
        tipText += 'Model name:        ' + chr(9) + self.description.modelName + '\n'
        tipText += 'Model identifier:  ' + chr(9) + self.description.modelIdentifier + '\n'
        tipText += 'Guid:                       ' + chr(9) + self.description.guid + '\n'
        tipText += 'Description:           ' + chr(9) + self.description.description + '\n'
        tipText += 'Author:                   ' + chr(9) + self.description.author + '\n'
        tipText += 'Version:                ' + chr(9) + self.description.version + '\n'
        tipText += 'Generation tool:   ' + chr(9) + self.description.generationTool + '\n'
        tipText += 'Gen. date and time:' + chr(9) + self.description.generationDateAndTime + '\n'
        tipText += 'Naming convention: ' + chr(9) + self.description.variableNamingConvention + '\n'
        tipText += 'Continuous states: ' + chr(9) + str(self.description.numberOfContinuousStates) + '\n'
        tipText += 'Event indicators:  ' + chr(9) + str(self.description.numberOfEventIndicators) + '\n'
        tipText += 'Default start time:' + chr(9) + str(self.description.defaultStartTime) + '\n'
        tipText += 'Default stop time: ' + chr(9) + str(self.description.defaultStopTime) + '\n'
        tipText += 'Default tolerance: ' + chr(9) + str(self.description.defaultTolerance)
        
        # ----> Here the rootAttribute of self.variableTree is set
        self.variableTree.rootAttribute = tipText

        for vName, v in self.description.scalarVariables.iteritems():
            variableAttribute = ''
            if v.description is not None:
                variableAttribute += 'Description:' + chr(9) + v.description + '\n'
            variableAttribute += 'Reference:' + chr(9) + str(v.valueReference)
            if v.variability is not None:
                variableAttribute += '\nVariability:' + chr(9) + v.variability
            if v.causality is not None:
                variableAttribute += '\nCausality:' + chr(9) + v.causality
            if v.alias is not None:
                if v.alias is not 'noAlias':
                    variableAttribute += '\nAlias:' + chr(9) + v.alias
            if v.directDependency is not None:
                variableAttribute += '\nDirect dep.:' + chr(9) + str(v.directDependency)
            if v.type is not None:
                variableAttribute += '\nType:' + chr(9) + v.type.type
                if v.type.description is not None:
                    variableAttribute += '\nType info:' + chr(9) + v.type.description
                if v.type.quantity is not None:
                    variableAttribute += '\nQuantity:' + chr(9) + v.type.quantity
                if v.type.unit is not None:
                    variableAttribute += '\nUnit:' + chr(9) + v.type.unit
                if v.type.displayUnit is not None:
                    variableAttribute += '\nDisplay unit:' + chr(9) + v.type.displayUnit
                if v.type.relativeQuantity is not None:
                    variableAttribute += '\nRel. quantity:' + chr(9) + str(v.type.relativeQuantity)
                if v.type.min is not None:
                    variableAttribute += '\nMin:' + chr(9) + v.type.min
                if v.type.max is not None:
                    variableAttribute += '\nMax:' + chr(9) + v.type.max
                if v.type.nominal is not None:
                    variableAttribute += '\nNominal:' + chr(9) + v.type.nominal
                if v.type.start is not None:
                    variableAttribute += '\nStart:' + chr(9) + v.type.start
                if v.type.fixed is not None:
                    variableAttribute += '\nFixed:' + chr(9) + str(v.type.fixed)
            valueEdit = True  # for the moment
            # ----> Here variable of self.variableTree is set (one entry of the dictionary)
            self.variableTree.variable[vName] = Plugins.Simulator.SimulatorBase.TreeVariable(v.type.start, valueEdit, v.type.unit, v.variability, variableAttribute)


class ExplicitEulerSolver():
    '''
        Integration method: Explicit Euler with event handling (without rootfinding)
    '''
    def simulate(self, Tstart, dt, Tend, y0, nOutputIntervals, gridWidth):
        ''' Simulates an ODE-sytem defined by different functions
            from Tstart to Tend by the explicit Euler method with the fixed step size dt.
            The inital start values of the states are given by the vector y0.
            Time or state events are handled after a successful step if necessary.
            Result points are defined by the number of output intervals 'nOutputIntervals'
            that define a time grid between Tstart and Tend with constant width.
            The grid width can be equal to dt or less or greater than dt.
        '''

        self.t_cur = Tstart
        self.y_cur = y0.copy()
        y_cur0 = y0.copy()
        # Define vectors for crossing and indicator functions
        z = self.state_events(self.t_cur, self.y_cur)
        zb = numpy.empty(len(z))
        zb_new = zb.copy()
        for i in xrange(len(z)):
            zb[i] = (z[i] > 0.0)
        nextTimeEvent = self.time_events(self.t_cur, self.y_cur)
        # Write initial values to results
        self.handle_result(self.t_cur, self.y_cur)
        # Define next step point and next output point
        stepCounter = 1
        nextStepPoint = min(Tstart + dt, Tend)
        if nOutputIntervals > 0:
            dOutput = (Tend - Tstart) / nOutputIntervals
        else:
            dOutput = dt
        outputStepCounter = 1
        nextOutputPoint = min(Tstart + dOutput, Tend)

        # Start the integration loop
        while self.t_cur < Tend:
            # Define stepsize h, next step point, t_new and time_event
            if nextTimeEvent is None or nextStepPoint < nextTimeEvent:
                time_event = False
                h = min(dt, Tend - self.t_cur)
                stepCounter += 1
                t_new = nextStepPoint
                nextStepPoint = min(Tstart + stepCounter * dt, Tend)
            else:
                time_event = True
                h = nextTimeEvent - self.t_cur
                t_new = nextTimeEvent
                if nextStepPoint == nextTimeEvent:
                    stepCounter += 1
                    nextStepPoint = min(Tstart + stepCounter * dt, Tend)

            # Do the explicit Euler step
            temp = self.y_cur
            self.y_cur = y_cur0
            self.y_cur[:] = temp[:]
            y_cur0 = temp
            t_cur0 = self.t_cur
            self.y_cur = self.y_cur + h * self.rhs(self.t_cur, self.y_cur)
            self.t_cur = t_new

            # Check for state events
            z = self.state_events(self.t_cur, self.y_cur)
            for i in xrange(len(z)):
                zb_new[i] = (z[i] > 0.0)
            state_event = (zb_new != zb)
            temp = zb
            zb = zb_new
            zb_new = temp

            # Inform about completed step
            self.completed_step(self)

            def interpolateLinear(a1, b1, a2, b2, t):
                return (b2 - b1) / (a2 - a1) * (t - a1) + b1

            # Write output points until the current time
            while nextOutputPoint < self.t_cur:
                y_Output = interpolateLinear(t_cur0, y_cur0, self.t_cur, self.y_cur, nextOutputPoint)
                self.handle_result(nextOutputPoint, y_Output)
                outputStepCounter += 1
                nextOutputPoint = min(Tstart + outputStepCounter * dOutput, Tend)

            # Depending on events have been detected do different tasks
            if state_event.any() or time_event:
                # Event handling
                event_info = [state_event, time_event]
                if not self.handle_event(self, event_info):
                    break                
                z = self.state_events(self.t_cur, self.y_cur)
                for i in xrange(len(z)):
                    zb[i] = (z[i] > 0.0)
                nextTimeEvent = self.time_events(self.t_cur, self.y_cur)
            elif nextOutputPoint == self.t_cur:
                y_Output = interpolateLinear(t_cur0, y_cur0, self.t_cur, self.y_cur, nextOutputPoint)
                self.handle_result(nextOutputPoint, y_Output)
                outputStepCounter += 1
                nextOutputPoint = min(Tstart + outputStepCounter * dOutput, Tend)

        self.finalize()
