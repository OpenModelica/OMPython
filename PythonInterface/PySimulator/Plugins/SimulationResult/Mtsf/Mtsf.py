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


import numpy
import collections
from operator import itemgetter
import time
import os
from Plugins.SimulationResult import IntegrationResults
import Plugins.SimulationResult.DymolaMat.DymolaMat as DymolaMat

import pyMtsf
import MtsfFmi


class MTSF(IntegrationResults.Results):
    ''' Result file object for an MTSF file    
    '''
    
    def __init__(self, resultFileName, modelDescription=None, modelVariables=None, experimentSetup=None, simpleTypes=None, units=None, enumerations=None):
        IntegrationResults.Results.__init__(self)        

        self._mtsf = pyMtsf.MTSF(resultFileName, modelDescription, modelVariables, experimentSetup, simpleTypes, units, enumerations)
                       
        self.fileName = self._mtsf.fileName
        self.isAvailable = self._mtsf.file is not None
        self.canLoadPartialData = True        

    def close(self):        
        self._mtsf.close()    
            
    def readData(self, variableName):
        return self._mtsf.readData(variableName)
       
    def getFileInfos(self):
        return self._mtsf.getResultAttributes()     
 
    def getVariables(self):
        self._mtsf.readVariableList()
        variabilityList = self._mtsf.fileData.variables["variability", :, 0].tolist()
        causalityList = self._mtsf.fileData.variables["causality", :, 0].tolist()
        SimpleTypeRows = self._mtsf.fileData.variables["simpleTypeRow", :, 0].tolist()
        UnitRows = self._mtsf.file["ModelDescription/SimpleTypes"]["unitOrEnumerationRow", :, 0].tolist()
        DataTypes = self._mtsf.file["ModelDescription/SimpleTypes"]["dataType", :, 0].tolist()
        try:
            Units = self._mtsf.file["ModelDescription/Units"]["name", :, 0].tolist()
        except:
            # No Units dataset found
            pass
        CausalityStrings = range(len(pyMtsf.CausalityType) + 1)
        for i, k in pyMtsf.CausalityType.items():
            CausalityStrings[k] = i
        DataTypeStrings = range(len(pyMtsf.DataType) + 1)
        for i, k in pyMtsf.DataType.items():
            DataTypeStrings[k] = i
        # Generate the dict
        variables = dict()
        # Fill the values of the dict
        for i in xrange(len(self._mtsf.fileData.nameList)):
            name = self._mtsf.fileData.nameList[i].replace('[', '.[')
            simpleTypeRow = SimpleTypeRows[i]
            unitRow = UnitRows[simpleTypeRow]
            dataType = DataTypes[simpleTypeRow]
            if variabilityList[i] in [pyMtsf.VariabilityType['constant'], pyMtsf.VariabilityType['fixed']]:
                variability = 'fixed'
            elif variabilityList[i] in [pyMtsf.VariabilityType['tunable'], pyMtsf.VariabilityType['discrete']]:
                variability = 'discrete'
            else:
                variability = 'continuous'
            value = None
            if variability == 'fixed':
                t, y, method = self._mtsf.readData(name)
                value = y[0]
                if dataType == pyMtsf.DataType['Boolean']:
                    if value == 0:
                        value = 'false'
                    else:
                        value = 'true'

            infos = collections.OrderedDict()
            if self._mtsf.fileData.descriptionList[i] is not None:
                if len(self._mtsf.fileData.descriptionList[i]) > 0:
                    infos['Description'] = self._mtsf.fileData.descriptionList[i]
            infos['Variability'] = variability
            infos['Causality'] = CausalityStrings[causalityList[i]]
            infos['Type'] = DataTypeStrings[dataType]
            if unitRow > -1:
                unit = Units[unitRow]
            else:
                unit = None
            variables[name] = IntegrationResults.ResultVariable(value, unit, variability, infos)
        return variables



def convertFromDymolaMatFile(matFilename, mtsfFilename=None):
    ''' Converts a Dymola result file (in mat-format) into the MTSF format.
        Returns the filename of the new result file
    '''    
    
    # Define file name of result file
    if mtsfFilename is None:
        if len(matFilename) >= 4:
            if matFilename[-4:] == '.mat':
                resultFileName = matFilename[:-4] + '.mtsf'
            else:
                resultFileName = matFilename + '.mtsf'
        else:
            resultFileName = matFilename + '.mtsf'
    else:
        if '.mtsf' in mtsfFilename:
            if mtsfFilename[-5:] == '.mtsf':
                resultFileName = mtsfFilename
            else:
                resultFileName = mtsfFilename + '.mtsf'
        else:
            resultFileName = mtsfFilename + '.mtsf'
    
    # Load mat-file
    res = DymolaMat.loadDymolaResult(matFilename)

    # Define basic structure of result file
    variable = collections.OrderedDict()

    # Search for aliases
    sortedVariables = [(i, res._dataInfo[i, 0], abs(res._dataInfo[i, 1])) for i in xrange(len(res._name))]
    sortedVariables.sort(key=itemgetter(2))
    sortedVariables.sort(key=itemgetter(1))
    aliasName = [None for i in xrange(len(res._name))]
    for i, var in enumerate(sortedVariables):
        index = var[0]
        alias = None
        j = i
        while j > 0:
            if sortedVariables[j - 1][1] != var[1] or sortedVariables[j - 1][2] != var[2]:
                break
            else:
                j -= 1
        if j < i:
            alias = res._name[sortedVariables[j][0]]
        aliasName[index] = alias
    dataIndexFixed = []
    dataIndexContinuous = []
    categoryIndex = pyMtsf.StandardCategoryNames.index(pyMtsf.CategoryMapping['Real'])
    for index, variableName in enumerate(res._name):
        aliasNegated = False
        if res._dataInfo[index, 0] == 1:
            variability = 'fixed'
            seriesIndex = 0  # Fixed
        else:
            variability = 'continuous'
            seriesIndex = 1  # Continuous
            if res._dataInfo[index, 1] < 0:
                aliasNegated = True
        if aliasName[index] is None:
            if variability == 'fixed':
                dataIndexFixed.append(abs(res._dataInfo[index, 1]) - 1)
            else:
                dataIndexContinuous.append(abs(res._dataInfo[index, 1]) - 1)
        variable[variableName] = pyMtsf.ScalarModelVariable(res._description[index],
                                                    res._unit[index],
                                                    'option',
                                                    0,  # may be set later
                                                    variability,
                                                    seriesIndex, categoryIndex,
                                                    aliasName[index], aliasNegated)
    modelVariables = pyMtsf.ModelVariables(variable, MtsfFmi.StandardSeriesForFmi, pyMtsf.StandardCategoryNames)
    timeData = res.data("Time")
    modelVariables.allSeries[1].initialRows = len(timeData)  # Continuous
    simpleTypes = []
    units = []
    enumerations = []
    simpleTypes.append(pyMtsf.SimpleType('Real without unit', pyMtsf.DataType["Real"], '',  False, -1, ''))  # No unit

    unitList = [(index, unit) for index, unit in enumerate(res._unit)]
    unitList.sort(key=itemgetter(1))
    preUnit = ''
    for x in unitList:
        index = x[0]
        unit = x[1]
        if unit != '':
            if preUnit != unit:
                units.append(pyMtsf.Unit(unit, 1.0, 0.0, 0))
                simpleTypes.append(pyMtsf.SimpleType('Real, Unit = ' + unit, pyMtsf.DataType["Real"], '',  False, len(units) - 1, ''))
                preUnit = unit
                modelVariables.variable[res._name[index]].simpleTypeRow = len(simpleTypes) - 1
            else:
                modelVariables.variable[res._name[index]].simpleTypeRow = len(simpleTypes) - 1
    experimentSetup = pyMtsf.ExperimentSetup(startTime=timeData[0], stopTime=timeData[-1], algorithm="",
                        relativeTolerance='', author="", description="",
                        generationDateAndTime=time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()),
                        generationTool="Python", machine=os.getenv('COMPUTERNAME'),
                        cpuTime="")
    modelDescription = pyMtsf.ModelDescription(resultFileName[:-5], '', '', '', '', '', 'structured')
    #Create result object
    mtsf = MTSF(resultFileName, modelDescription, modelVariables, experimentSetup, simpleTypes, units, enumerations)
    # Write numeric data
    fixedValues = numpy.ndarray((len(dataIndexFixed,)))
    for i, index in enumerate(dataIndexFixed):
        fixedValues[i] = res._data[0][0, index]
    continuousValues = numpy.ndarray((len(timeData), len(dataIndexContinuous)))
    for i, index in enumerate(dataIndexContinuous):
        continuousValues[:, i] = res._data[1][:, index]
    mtsf._mtsf.results.series['Fixed'].category[pyMtsf.CategoryMapping['Real']].writeData(fixedValues)
    mtsf._mtsf.results.series['Continuous'].category[pyMtsf.CategoryMapping['Real']].writeData(continuousValues)

    # Close file
    mtsf.close()
    return resultFileName

