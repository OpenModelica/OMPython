''' 
Copyright (C) 2011-2012 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.), 
Institute of System Dynamics and Control
and BAUSCH-GALL GmbH, Munich
All rights reserved.

This file is licensed under the "BSD New" license
(see also http://opensource.org/licenses/BSD-3-Clause):

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:
   - Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
   - Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
   - Neither the name of the German Aerospace Center nor the names of its contributors 
     may be used to endorse or promote products derived from this software 
     without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY 
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, 
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import zipfile
import collections
import os
from operator import itemgetter

import pyMtsf
from Plugins.Simulator.FMUSimulator.FMIDescription import FMIDescription



StandardSeriesForFmi = [pyMtsf.Series('Fixed', None, 'constant', 1), pyMtsf.Series('Continuous', 'Time', 'linear', 100), pyMtsf.Series('Discrete', 'TimeDiscrete', 'constant', 10)]

def convertFromFmi(fmuFilename, fmi=None):
    ''' Returns data to initialize an MTSF result file from an FMU.
        The call to initialize an MTSF result file is 
            pyMtsf.MTSF(resultFileName, modelDescription, modelVariables, experimentSetup, simpleTypes, units, enumerationsMatrix)
        The missing data is resultFileName and experimentSetup to be specified before initializing the MTSF object.   
        
        Inputs                       Type:
            fmuFilename              String
            fmi                      FMIDescription      [optional]
            if fmi is given, then fmuFilename is ignored. Otherwise the FMI description is loaded from the given file.
            
        Outputs
           modelDescription          pyMtsf.ModelDescription        
           modelVariables            pyMtsf.ModelVariables
           simpleTypes               list of pyMtsf.SimpleType
           units                     list of pyMtsf.Unit
           enumerationsMatrix        list of pyMtsf.Enumeration
    '''
  
    def _None2Str(x):
        if x is None:
            return ''
        else:
            return x


    # Load FMIDescription if necessary
    if fmi is None:
        fmuFile = zipfile.ZipFile(os.getcwd() + '\\' + fmuFilename + '.fmu',  'r')
        fmi = FMIDescription(fmuFile.open('modelDescription.xml'))

    # Prepare some variables
    allSeriesNames = [x.name for x in StandardSeriesForFmi]
    variable = collections.OrderedDict()
    simpleTypes = []
    units = []
    enumerationsMatrix = []
    variable['Time'] = pyMtsf.ScalarModelVariable('Continuous Time', 's', 'input', 0, 'continuous', allSeriesNames.index('Continuous'), pyMtsf.StandardCategoryNames.index(pyMtsf.CategoryMapping['Real']), None, 0)
    variable['TimeDiscrete'] = pyMtsf.ScalarModelVariable('Discrete Time at events', 's', 'input', 0, 'discrete', allSeriesNames.index('Discrete'), pyMtsf.StandardCategoryNames.index(pyMtsf.CategoryMapping['Real']), None, 0)

    # Alias
    for var in fmi.scalarVariables.values():
        if var.alias is None or var.alias == "noAlias":
            var.alias = 'NOAlias'   # To guarantee that this variable is the first
                                    # one in sorted order
    referenceList = [(x, y.valueReference, y.alias) for x, y in fmi.scalarVariables.iteritems()]
    referenceList.sort(key=itemgetter(2))
    referenceList.sort(key=itemgetter(1))

    for index in xrange(len(referenceList)):
        variableName = referenceList[index][0]
        if referenceList[index][2] in ['alias', 'negatedAlias']:
            valueReference = referenceList[index][1]
            prevValueReference = referenceList[index - 1][1]
            if prevValueReference != valueReference:
                raise ValueError("No original variable found for alias " + variableName)
            if referenceList[index - 1][2] == "NOAlias":
                originName = referenceList[index - 1][0]
            else:
                originName = fmi.scalarVariables[referenceList[index - 1][0]].aliasName
            fmi.scalarVariables[variableName].aliasName = originName
        else:
            fmi.scalarVariables[variableName].aliasName = None

    # Types and display units
    uniqueSimpleType = []
    for fmiVariableName, fmiVariable in fmi.scalarVariables.iteritems():
        type = fmiVariable.type
        unitList = [_None2Str(type.unit) + _None2Str(type.displayUnit)]
        if fmi.units.has_key(type.unit):
            for displayUnitName, displayUnit in fmi.units[type.unit].iteritems():
                if displayUnitName != type.unit:
                    unitList.append(displayUnitName + '{:.16e}'.format(displayUnit.gain) + '{:.16e}'.format(displayUnit.offset))
            #unitList.sort()
        dataType = type.type
        enumerations = ''
        if dataType == 'Enumeration':
            enumerations = ''.join([_None2Str(x[0]) + _None2Str(x[1]) for x in type.item])
        uniqueSimpleType.append((fmiVariableName, type, _None2Str(type.name) + str(pyMtsf.DataType[dataType]) + _None2Str(type.quantity) + str(type.relativeQuantity), ''.join(unitList), enumerations))
    
    # Simple Types
    uniqueSimpleType.sort(key=itemgetter(3))
    uniqueSimpleType.sort(key=itemgetter(2))
    lastUniqueStr = ''
    rowIndex = dict()
    lastIndex = -1
    uniqueDisplayUnit = []
    uniqueEnumerations = []
    for s in uniqueSimpleType:
        fmiVariableName = s[0]
        type = s[1]
        uniqueStr = s[2] + s[3] + s[4]
        if uniqueStr == lastUniqueStr:
            rowIndex[fmiVariableName] = lastIndex
        else:
            lastUniqueStr = uniqueStr
            lastIndex += 1
            rowIndex[fmiVariableName] = lastIndex
            uniqueDisplayUnit.append((type, lastIndex, s[3]))
            uniqueEnumerations.append((type, lastIndex, s[4]))
            dataType = type.type
            simpleTypes.append(pyMtsf.SimpleType(type.name, pyMtsf.DataType[dataType], type.quantity, type.relativeQuantity, -1, type.description))

    # Units
    uniqueDisplayUnit.sort(key=itemgetter(2))
    lastUniqueStr = ''
    startRow = -1
    for s in uniqueDisplayUnit:
        type = s[0]
        k = s[1]
        uniqueStr = s[2]
        if uniqueStr == lastUniqueStr:
            simpleTypes[k].unitOrEnumerationRow = startRow
        else:
            lastUniqueStr = uniqueStr
            if uniqueStr != '':  # There is a unit definition
                startRow = len(units)
                units.append(pyMtsf.Unit(type.unit, 1.0, 0.0, 0))
                if fmi.units.has_key(type.unit):
                    for displayUnitName, displayUnit in fmi.units[type.unit].iteritems():
                        if displayUnitName != type.unit:
                            if type.displayUnit is not None and type.displayUnit != '' and type.displayUnit == displayUnitName:
                                mode = 2  # DefaultDisplayUnit
                            else:
                                mode = 1  # DisplayUnit
                            units.append(pyMtsf.Unit(displayUnitName, displayUnit.gain, displayUnit.offset, mode))

                simpleTypes[k].unitOrEnumerationRow = startRow
            else:
                startRow = -1

    # Enumerations
    uniqueEnumerations.sort(key=itemgetter(2))
    lastUniqueStr = ''
    startRow = -1
    for s in uniqueEnumerations:
        type = s[0]
        k = s[1]
        uniqueStr = s[2]
        if uniqueStr != '':
            if uniqueStr == lastUniqueStr:
                simpleTypes[k].unitOrEnumerationRow = startRow
            else:
                lastUniqueStr = uniqueStr
                startRow = len(enumerationsMatrix)
                j = 0
                for enum in type.item:
                    j += 1
                    if j == 1:
                        firstEntry = 1
                    else:
                        firstEntry = 0
                    enumerationsMatrix.append(pyMtsf.Enumeration(enum[0], j, enum[1], firstEntry))
                simpleTypes[k].unitOrEnumerationRow = startRow

    # Iterate over all fmi-variables
    for fmiVariableName, fmiVariable in fmi.scalarVariables.iteritems():
        variableType = fmiVariable.type.type
        if variableType != "String":  # Do not support strings
            variability = fmiVariable.variability

            aliasNegated = 0
            aliasName = fmiVariable.aliasName
            if aliasName is not None:
                if fmiVariable.alias == 'negatedAlias':
                    aliasNegated = 1
                # Due to possibly insufficient information in xml-file
                variability = fmi.scalarVariables[aliasName].variability
            categoryIndex = pyMtsf.StandardCategoryNames.index(pyMtsf.CategoryMapping[variableType])
            if variability in ['constant', 'parameter']:
                seriesIndex = allSeriesNames.index('Fixed')
            elif variability == 'discrete':
                seriesIndex = allSeriesNames.index('Discrete')
            else:
                seriesIndex = allSeriesNames.index('Continuous')

            causality = fmiVariable.causality
            # Due to FMI 1.0; in vers. 2.0 this should not be neccessary
            if causality is None:
                causality = 'local'
            if variability == 'parameter':
                causality = 'parameter'
                variability = 'fixed'

            simpleTypeRow = rowIndex[fmiVariableName]
            variable[fmiVariableName] = pyMtsf.ScalarModelVariable(fmiVariable.description,
                                                    fmiVariable.type.unit,
                                                    causality,
                                                    simpleTypeRow,
                                                    variability,
                                                    seriesIndex, categoryIndex,
                                                    aliasName, aliasNegated)

    # Some basics for independent time variables
    startRow = len(units)
    units.append(pyMtsf.Unit('s', 1.0, 0.0, 0))
    units.append(pyMtsf.Unit('ms', 0.001, 0.0, 1))
    units.append(pyMtsf.Unit('min', 60.0, 0.0, 1))
    units.append(pyMtsf.Unit('h', 3600.0, 0.0, 1))
    units.append(pyMtsf.Unit('d', 86400.0, 0.0, 1))
   
    simpleTypes.append(pyMtsf.SimpleType('Time', pyMtsf.DataType["Real"], 'Time',  False, startRow, ''))
    variable['Time'].simpleTypeRow = len(simpleTypes) - 1
    variable['TimeDiscrete'].simpleTypeRow = len(simpleTypes) - 1

    modelDescription = pyMtsf.ModelDescription(fmi.modelName, fmi.description, fmi.author, fmi.version, fmi.generationTool, fmi.generationDateAndTime, fmi.variableNamingConvention)
    modelVariables = pyMtsf.ModelVariables(variable, StandardSeriesForFmi, pyMtsf.StandardCategoryNames)

    return modelDescription, modelVariables, simpleTypes, units, enumerationsMatrix




if __name__ == '__main__':
    
    import time
    import numpy
         
    nPoints = 60
    BlockSize = 100
        
    # Prepare information from FMU
    name_fmu_file = 'Examples/fullRobot'    
    (modelDescription, modelVariables, simpleTypes, units, enumerations) = convertFromFmi(name_fmu_file)
    modelVariables.allSeries[1].initialRows = nPoints * BlockSize  # Continuous
    # Phase 1 of result file generation
    resultFileName = name_fmu_file + str(nPoints) + '.mtsf'
    experimentSetup = pyMtsf.ExperimentSetup(startTime=0.0, stopTime=4.78, algorithm="Dassl",
                        relativeTolerance=1e-7, author="", description="Test experiment",
                        generationDateAndTime=time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()),
                        generationTool="Python", machine=os.getenv('COMPUTERNAME'),
                        cpuTime="")
    
    startTime = time.clock()
    #Create result object
    mtsf = pyMtsf.MTSF(resultFileName, modelDescription, modelVariables, experimentSetup, simpleTypes, units, enumerations)
    
    # Some aliases
    realParameter = mtsf.results.series['Fixed'].category[pyMtsf.CategoryMapping['Real']]
    #integerParameter = mtsf.results.series['Fixed'].category[CategoryMapping['Integer']]
    booleanParameter = mtsf.results.series['Fixed'].category[pyMtsf.CategoryMapping['Boolean']]
    realContinuous = mtsf.results.series['Continuous'].category[pyMtsf.CategoryMapping['Real']]
    realDiscrete = mtsf.results.series['Discrete'].category[pyMtsf.CategoryMapping['Real']]
    #integerDiscrete = mtsf.results.series['Discrete'].category[CategoryMapping['Integer']]
    booleanDiscrete = mtsf.results.series['Discrete'].category[pyMtsf.CategoryMapping['Boolean']]

    # *************************************
    # Phase 2 of result file generation
    print "Write Data ..."
    realParameter.writeData(numpy.random.rand(1, realParameter.nColumn) * 2e5 - 1e5)
    #integerParameter.writeData(numpy.floor(0.5+numpy.random.rand(1,integerParameter.nColumn)*2e5-1e5).astype(int))
    booleanParameter.writeData(numpy.floor(0.5 + numpy.random.rand(1, booleanParameter.nColumn)).astype(int))

    for i in range(nPoints):        
        #write continuous
        realContinuous.writeData(numpy.random.rand(BlockSize, realContinuous.nColumn) * 2e5 - 1e5)
        #write discrete
        #booleanDiscrete.writeData(numpy.floor(0.5+numpy.random.rand(2, booleanDiscrete.nColumn)).astype(int))
        #realDiscrete.writeData(numpy.random.rand(2, realDiscrete.nColumn)*2e5 - 1e5)
        #integerDiscrete.writeData(numpy.floor(0.5+numpy.random.rand(2, integerDiscrete.nColumn)*2e5-1e5).astype(int))
        #write String
        #mtsf.series['Continuous'].categories['H5T_C_S1'].writeData(numpy.ones((1,k_str),dtype=numpy.str_))
    
    # Write times:
    #realContinuous.member[0].dataset[:,0] = numpy.linspace(0,1,realContinuous.member[0].dataset.shape[0])
    #realDiscrete.member[0].dataset[:,0] = numpy.linspace(0,1,realDiscrete.member[0].dataset.shape[0])
    print "Data written."

    # ****************************************
    # Phase 3 of result file generation
    mtsf.close()
    print  "Elapsed time = " + format(time.clock() - startTime, '0.2f') + " s."
   
