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


'''
This module provides a framework to write and read files in the MTSF format.
MTSF is the abbreviation for Modelica Association Time Series File Format.
For a detailed description of the MTSF format, please see [1].

[1] Pfeiffer A., Bausch-Gall I. and Otter M.: Proposal for a Standard Time Series File Format in HDF5.
Proc. of 9th International Modelica Conference, Munich, Germany, Sept. 2012.
'''


import h5py
import numpy



''' 
Some helpful global variables:
'''
DataType = {'Real': 1, 'Integer': 2, 'Boolean': 3, 'String': 4, 'Enumeration': 5}
CausalityType = {'parameter': 1, 'input': 2, 'output': 3, 'local': 4, 'option': 5}
VariabilityType = {'constant': 1, 'fixed': 2, 'tunable': 3, 'discrete': 4, 'continuous': 5}

CategoryMapping = {'Real': 'H5T_NATIVE_DOUBLE',
                'Integer': 'H5T_NATIVE_INT32',
                'Boolean': 'H5T_NATIVE_INT8',
                 'String': 'H5T_C_S1',
            'Enumeration': 'H5T_NATIVE_INT32'}
CategoryReverseMapping = {'H5T_NATIVE_DOUBLE': 'Real',
                           'H5T_NATIVE_INT32': 'Integer',
                            'H5T_NATIVE_INT8': 'Boolean',
                                   'H5T_C_S1': 'String'}

StandardCategoryNames = ['H5T_NATIVE_DOUBLE',
                         'H5T_NATIVE_FLOAT',
                         'H5T_IEEE_F64LE',
                         'H5T_NATIVE_INT64',
                         'H5T_NATIVE_INT32',
                         'H5T_NATIVE_INT32',
                         'H5T_NATIVE_INT8',
                         'H5T_C_S1',
                         'H5T_FORTRAN_S1']


class ModelDescription:
    ''' Class hosting the attributes of /ModelDescription
    '''    
    def __init__(self, modelName, description, author, version, generationTool,
                 generationDateAndTime, variableNamingConvention):
        self.modelName = modelName
        self.description = description
        self.author = author
        self.version = version
        self.generationTool = generationTool
        self.generationDateAndTime = generationDateAndTime
        self.variableNamingConvention = variableNamingConvention


class ScalarModelVariable:
    ''' Class hosting information about a variable in /ModelDescription/Variables
    '''
    def __init__(self, description=None, unit=None, causality=None, simpleTypeRow=-1, variability=None, seriesIndex=-1, categoryIndex=-1, aliasName=None, aliasNegated=None):
        if description is None:
            self.description = ''
        else:
            self.description = description
        if unit is None:
            self.unit = ''
        else:
            self.unit = unit
        if causality is None:
            self.causality = CausalityType['local']
        else:
            self.causality = CausalityType[causality]
        self.simpleTypeRow = simpleTypeRow
        if variability is None:
            self.variability = VariabilityType['continuous']
        elif type(variability) == str:
            self.variability = VariabilityType[variability]
        else:
            self.variability = variability
        self.seriesIndex = seriesIndex
        self.categoryIndex = categoryIndex
        self.aliasName = aliasName
        self.aliasNegated = aliasNegated
        self.handle = None
        self.columnIndex = None
        self.category = None
        self.rowIndex = None


class ModelVariables:
    ''' Class hosting information about all model variables.
        Only used to initialize an MTSF object.
    '''
    def __init__(self, variable, allSeries, allCategories):
        self.variable = variable
        self.allSeries = allSeries
        self.allCategories = allCategories


class SimpleType:
    ''' Class to hold information about one Simple Type (in the sense of MTSF)    
    '''
    def __init__(self, name, dataType, quantity, relativeQuantity, unitRow, description):
        if name is None:
            self.name = ''
        else:
            self.name = name
        self.dataType = dataType
        if quantity is None:
            self.quantity = ''
        else:
            self.quantity = quantity
        self.unitOrEnumerationRow = unitRow
        self.relativeQuantity = relativeQuantity
        if description is None:
            self.description = ''
        else:
            self.description = description


class Unit:
    ''' Class to hold information about one Unit (in the sense of MTSF)    
    '''
    def __init__(self, name, factor, offset, mode):
        if name is None:
            self.name = ''
        else:
            self.name = name
        self.factor = factor
        self.offset = offset
        self.mode = mode


class Enumeration:
    ''' Class to hold information about one enumeration (in the sense of MTSF)    
    '''
    def __init__(self, name, value, description, firstEntry):
        if name is None:
            self.name = ''
        else:
            self.name = name
        self.value = value
        if description is None:
            self.description = ''
        else:
            self.description = description
        self.firstEntry = firstEntry


class ExperimentSetup:
    ''' Class hosting the attributes of /Results
    '''
    def __init__(self, startTime, stopTime, algorithm, relativeTolerance, author, description,
                generationDateAndTime, generationTool, machine, cpuTime):
        self.startTime = startTime
        self.stopTime = stopTime
        self.algorithm = algorithm
        self.relativeTolerance = relativeTolerance
        self.author = author
        self.description = description
        self.generationDateAndTime = generationDateAndTime
        self.generationTool = generationTool
        self.machine = machine
        self.cpuTime = cpuTime


class Category:
    ''' Class to handle a category. A category is a dataset of a time series group.    
    '''
    def __init__(self, name, series=None):
        #Create the dataset in the HDF5 file
        self.nColumn = 0
        self.currentRow = 0
        self.name = name
        self.series = series

    def writeInitial(self, host, initialRows):
        compression = None
        if self.name != 'H5T_C_S1':
            if self.nColumn >= 8:
                #compression = "szip"
                compression = None
        self.dataset = host.create_dataset(self.name, shape=(initialRows, self.nColumn), dtype=eval('h5py.h5t.' + self.name[4:]), maxshape=(None, None), compression=compression)  # chunks=(c1,c2))
        self._data = numpy.zeros((max(min(10000000 / self.nColumn, initialRows), 1), self.nColumn))
        self._currentRow = 0

    def writeData(self, dataMatrix):
        if dataMatrix.ndim == 1:
            # Enough space?
            if 1 + self._currentRow > self._data.shape[0]:
                self._writeDataToFile()

            if 1 + self._currentRow > self._data.shape[0]:
                self._writeDataToFile(dataMatrix)
            else:
                self._data[self._currentRow:self._currentRow + 1, :] = dataMatrix[:]
                self._currentRow += 1
        else:
            # Enough space?
            if dataMatrix.shape[0] + self._currentRow > self._data.shape[0]:
                self._writeDataToFile()
            if dataMatrix.shape[0] + self._currentRow > self._data.shape[0]:
                self._writeDataToFile(dataMatrix)
            else:
                self._data[self._currentRow:self._currentRow + dataMatrix.shape[0], :] = dataMatrix[:, :]
                self._currentRow += dataMatrix.shape[0]

    def _writeDataToFile(self, dataMatrix=None):
        ''' Write data in a HDF5 dataset
        '''
        useInternalData = False
        if dataMatrix is None:
            useInternalData = True
            dataMatrix = self._data
        if dataMatrix.ndim == 1:
            if 1 + self.currentRow > self.dataset.shape[0]:
                # Increase space about 30%
                #print "Increasing space"
                newSize = self.dataset.shape[0] + max(self.dataset.shape[0] * 3 / 10, 1)
                self.dataset.resize(newSize, axis=0)
            # Write data
            if useInternalData:
                row = self._currentRow
            else:
                row = 1
            if row > 0:
                self.dataset[self.currentRow:self.currentRow + row, :] = dataMatrix[0:row, :]
        else:
            if dataMatrix.shape[0] + self.currentRow > self.dataset.shape[0]:
                # Increase space about 30%
                #print "Increasing space"
                newSize = self.dataset.shape[0] + max(self.dataset.shape[0] * 3 / 10, dataMatrix.shape[0])
                self.dataset.resize(newSize, axis=0)
            # Write data
            if useInternalData:
                row = self._currentRow
            else:
                row = dataMatrix.shape[0]
            if row > 0:
                self.dataset[self.currentRow:self.currentRow + row, :] = dataMatrix[0:row, :]

        self.currentRow += row
        # Reset internal data
        self._currentRow = 0

    def close(self):
        if self._currentRow > 0:
            self._writeDataToFile()
        if self.currentRow < self.dataset.shape[0]:
            self.dataset.resize(self.currentRow, axis=0)

class Series:
    ''' Class to handle a time series. A time series may contain several datasets.
        We call each dataset a category.
    '''
    def __init__(self, name, independentVariable, interpolationMethod, initialRows):
        ''' Basically a series consists of the attributes independentVariableRow and
            interpolationMethod. Further it contains (possibly several) categories        
        '''
        self.name = name
        self.independentVariable = independentVariable
        self.interpolationMethod = interpolationMethod
        self.category = {}
        self.handle = None
        self.initialRows = initialRows
        self.independentVariableRow = -2

    def writeInitial(self, mtfs):
        # Create HDF5 group for series
        self.handle = mtfs.resultsHandle.create_group(self.name)
        self.handle.attrs['interpolationMethod'] = self.interpolationMethod
        for category in self.category.values():
                category.writeInitial(self.handle, self.initialRows)

    def writeIndependentVariable(self, mtfs):
        # Set link to independent variable
        if self.independentVariable is not None:
            self.independentVariableRow = mtfs.modelVariable[self.independentVariable].rowIndex
        else:
            self.independentVariableRow = -1
        self.handle.attrs['independentVariableRow'] = self.independentVariableRow

    def close(self):
        for category in self.category.values():
            category.close()



class Results:
    ''' Class to handle the structure and data of /Results
    '''
    def __init__(self, modelVariables):
        '''  Type of modelVariables: ModelVariables
        '''        
        self.series = {}
        # In a first step process all non-alias variables
        for scalar in modelVariables.variable.values():
            if scalar.aliasName is None:
                seriesName = modelVariables.allSeries[scalar.seriesIndex].name
                categoryName = modelVariables.allCategories[scalar.categoryIndex]
                if not self.series.has_key(seriesName):
                    self.series[seriesName] = Series(seriesName, modelVariables.allSeries[scalar.seriesIndex].independentVariable, modelVariables.allSeries[scalar.seriesIndex].interpolationMethod, modelVariables.allSeries[scalar.seriesIndex].initialRows)
                if not self.series[seriesName].category.has_key(categoryName):
                    self.series[seriesName].category[categoryName] = Category(categoryName, self.series[seriesName])

                self.series[seriesName].category[categoryName].nColumn += 1
                scalar.columnIndex = self.series[seriesName].category[categoryName].nColumn - 1
                scalar.category = self.series[seriesName].category[categoryName]

        # In a second step process all alias variables
        for scalarName, scalar in modelVariables.variable.iteritems():
            if scalar.aliasName is not None:
                seriesName = modelVariables.allSeries[scalar.seriesIndex].name
                categoryName = modelVariables.allCategories[scalar.categoryIndex]
                scalar.columnIndex = modelVariables.variable[scalar.aliasName].columnIndex
                scalar.category = modelVariables.variable[scalar.aliasName].category
                if modelVariables.variable[scalar.aliasName].categoryIndex != scalar.categoryIndex:                    
                    print("Categories do not match for " + scalar.aliasName + " and "
                                    + scalarName + ": " + modelVariables.variable[scalar.aliasName].category.name
                                    + "  vs.  " + scalar.category.name)
                    seriesName = modelVariables.allSeries[scalar.seriesIndex].name
                    categoryName = modelVariables.allCategories[scalar.categoryIndex]
                    if not self.series.has_key(seriesName):
                        self.series[seriesName] = Series(seriesName, modelVariables.allSeries[scalar.seriesIndex].independentVariable, modelVariables.allSeries[scalar.seriesIndex].interpolationMethod, modelVariables.allSeries[scalar.seriesIndex].initialRows)
                    if not self.series[seriesName].category.has_key(categoryName):
                        self.series[seriesName].category[categoryName] = Category(categoryName, self.series[seriesName])
                    self.series[seriesName].category[categoryName].nColumn += 1
                    scalar.columnIndex = self.series[seriesName].category[categoryName].nColumn - 1
                    scalar.category = self.series[seriesName].category[categoryName]


class FileData:
    ''' Class to hold some information when reading an MTSF file
    '''
    def __init__(self):
        self.variables = None
        self.nameList = None
        self.objectIdList = None
        self.columnList = None
        self.negatedList = None
        self.descriptionList = None


def convertDer(variableName):
    ''' Converts a variable name  a.b.c.d_(der)  to  a.b.c.der(d)
        If no "_(der)" is contained in variableName, the name
        is returned unchanged.
    ''' 
    x = variableName
    x = x.replace('.[', '[')
    if len(x) > 6:
        if x[-6:] == '_(der)':
            x = x[:-6]
            k = x.rfind('.')
            if k > -1:
                x = x[:k] + '.der(' + x[k+1:] + ')'                
            else:
                x = 'der(' + x + ')'
    return x


class MTSF:
    ''' This is the main class to write and read files in MTSF format
    '''    
    def __init__(self, resultFileName, modelDescription=None, modelVariables=None, experimentSetup=None, simpleTypes=None, units=None, enumerations=None):
        '''                              Type        
            resultFileName               String
            modelDescription             ModelDescription
            modelVariables               ModelVariables
            experimentSetup              ExperimentSetup
            simpleTypes                  list of SimpleTypes
            units                        list of Units
            enumerations                 list of Enumerations
            
            If modelDescription is not None then /ModelDescription is written, also the structure of /Results
            Otherwise the file given by resultFileName is opened for reading.
            
            Currently, values of Enumerations are written as Integer, because reading of enumeration by h5py causes a Python crash.
            The correct formats are disabled, see the comments beginning by     '# h5py.special_dtype(enum=('
        '''

        self.readable = False
        self.fileName = resultFileName        
        self.file = None        

        if resultFileName is None:
            return
        if resultFileName == '':
            return

        if modelDescription is None:
            self._openFileForReading(resultFileName)
            self.readable = True
            return

        #Get model description
        self.modelDescription = modelDescription
        self.modelVariable = modelVariables.variable
        self.allSeries = modelVariables.allSeries
        self.allCategories = modelVariables.allCategories
        self.experimentSetup = experimentSetup
        self.results = Results(modelVariables)
        self.simpleTypes = simpleTypes
        self.units = units
        self.enumerations = enumerations

        # Create hdf5 file
        try:
            self.file = h5py.File(self.fileName, 'w', libver='latest')
        except:
            self.file = None
            return

        self.access = 'write'
        self.file.attrs['mtsfVersion'] = "0.3"

        self.WriteResultStructure()

        self.WriteModelVariables()
        self.WriteSimpleTypes()
        self.WriteUnits()
        self.WriteEnumerations()
        for series in self.results.series.values():
            series.writeIndependentVariable(self)
           
        self.readable = True


    def WriteEnumerations(self):
        if len(self.enumerations) == 0:
            return

        maxLenName = self._getMaxLength([x.name for x in self.enumerations])
        maxLenDescription = self._getMaxLength([x.description for x in self.enumerations])
        numpyDataType = numpy.dtype({'names': ['name', 'value',
                                              'description', 'firstEntry'],
                               'formats': ['S' + str(max(maxLenName, 1)),
                                          'int32',
                                          'S' + str(max(maxLenDescription, 1)),
                                          'uint8']})  # h5py.special_dtype(enum=(numpy.uint8, {'false':0, 'true':1}))]})
        dataset = self.description.create_dataset('Enumerations', (len(self.enumerations), 1), dtype=numpyDataType, maxshape=(len(self.enumerations), 1), compression='gzip')
        allData = []
        for enum in self.enumerations:
            allData.append((enum.name, enum.value, enum.description, enum.firstEntry))
        dataset[:, 0] = allData

    def WriteUnits(self):
        if len(self.units) == 0:
            return

        maxLenTypeName = self._getMaxLength([x.name for x in self.units])
        numpyDataType = numpy.dtype({'names': ['name', 'factor',
                                              'offset', 'mode'],
                               'formats': ['S' + str(max(maxLenTypeName, 1)),
                                          'double',
                                          'double',
                                          'uint8']})  # h5py.special_dtype(enum=(numpy.uint8, {'BaseUnit':0, 'Unit':1, 'DefaultDisplayUnit':2}))]})

        dataset = self.description.create_dataset('Units', (len(self.units), 1), dtype=numpyDataType, maxshape=(len(self.units), 1), compression='gzip')
        allData = []
        for unit in self.units:
            allData.append((unit.name, unit.factor, unit.offset, unit.mode))
        dataset[:, 0] = allData

    def WriteSimpleTypes(self):
        if len(self.simpleTypes) == 0:
            return

        maxLenTypeName = self._getMaxLength([x.name for x in self.simpleTypes])
        maxLenQuantity = self._getMaxLength([x.quantity for x in self.simpleTypes])
        #maxLenUnit = self._getMaxLength([x.unit for x in self.simpleTypes])
        numpyDataType = numpy.dtype({'names': ['name', 'dataType',
                                              'quantity',
                                              'relativeQuantity',
                                              'description',
                                              'unitOrEnumerationRow',
                                              ],
                               'formats': ['S' + str(max(maxLenTypeName, 1)),
                                          'uint8',  # h5py.special_dtype(enum=(numpy.uint8, DataType)),
                                          'S' + str(max(maxLenQuantity, 1)),
                                          'uint8',  # h5py.special_dtype(enum=(numpy.uint8, {'false':0, 'true':1})),
                                          'S1',
                                          'int32']})
        dataset = self.description.create_dataset('SimpleTypes', (len(self.simpleTypes), 1), dtype=numpyDataType, maxshape=(len(self.simpleTypes), 1), compression='gzip')
        allData = []
        for simpleType in self.simpleTypes:
            allData.append((simpleType.name, simpleType.dataType,
                            simpleType.quantity,
                            simpleType.relativeQuantity,
                            '',
                            simpleType.unitOrEnumerationRow))
        dataset[:, 0] = allData

    def _getMaxLength(self, mylist):
        lenList = [len(x) for x in mylist]
        if len(lenList) > 0:
            return max(lenList)
        else:
            return 0

    def WriteModelVariables(self):
        scalarVariables = self.modelVariable
        # Get maximum length of string vectors
        maxLenName = self._getMaxLength(scalarVariables.keys())
        maxLenDescription = self._getMaxLength([x.description for x in scalarVariables.values()])
        #Create dtype object
        numpyDataType = numpy.dtype({'names': ['name', 'simpleTypeRow',
                                              'causality', 'variability',
                                              'description', 'objectId', 'column', 'negated'],
                               'formats': ['S' + str(max(maxLenName, 1)),
                                          'uint32',
                                          'uint8',  # h5py.special_dtype(enum=(numpy.uint8, CausalityType)),
                                          'uint8',  # h5py.special_dtype(enum=(numpy.uint8, VariabilityType)),
                                          'S' + str(max(maxLenDescription, 1)),
                                          h5py.special_dtype(ref=h5py.Reference),
                                          'uint32',
                                          'uint8']})  # h5py.special_dtype(enum=(numpy.uint8, {'false':0, 'true':1}))]})
        self.description = self.file.create_group("ModelDescription")
        #Write information on Simulation group
        description = self.modelDescription
        self.description.attrs['modelName'] = description.modelName
        self.description.attrs['description'] = description.description
        self.description.attrs['author'] = description.author
        self.description.attrs['version'] = description.version
        self.description.attrs['generationTool'] = description.generationTool
        self.description.attrs['generationDateAndTime'] = description.generationDateAndTime
        self.description.attrs['variableNamingConvention'] = description.variableNamingConvention
        dataset = self.description.create_dataset('Variables', (len(scalarVariables), 1), dtype=numpyDataType, maxshape=(len(scalarVariables), 1), compression='gzip')
        # Sort Variables by names
        nameList = [x for x in scalarVariables.keys()]
        nameList.sort()
        allData = []
        i = -1
        for variableName in nameList:
            variable = scalarVariables[variableName]
            i += 1
            variable.rowIndex = i
            x = convertDer(variableName)
            allData.append((x, variable.simpleTypeRow,
                            variable.causality, variable.variability,
                            variable.description,
                            variable.category.dataset.ref, variable.columnIndex, variable.aliasNegated))
        dataset[:, 0] = allData
        return

    def WriteResultStructure(self):
        self.resultsHandle = self.file.create_group('Results')
        setup = self.experimentSetup
        self.resultsHandle.attrs["ResultType"] = "Simulation"
        self.resultsHandle.attrs["startTime"] = str(setup.startTime)
        self.resultsHandle.attrs["stopTime"] = str(setup.stopTime)
        self.resultsHandle.attrs["relativeTolerance"] = str(setup.relativeTolerance)
        self.resultsHandle.attrs["generationDateAndTime"] = setup.generationDateAndTime
        self.resultsHandle.attrs["algorithm"] = setup.algorithm
        self.resultsHandle.attrs["author"] = setup.author
        self.resultsHandle.attrs["description"] = setup.description
        self.resultsHandle.attrs["generationTool"] = setup.generationTool
        self.resultsHandle.attrs["machine"] = setup.machine
        self.resultsHandle.attrs["cpuTime"] = setup.cpuTime
        for series in self.results.series.values():
            series.writeInitial(self)

    def close(self):
        ''' Close the HDF5 file.

        '''
        self.readable = False
        if self.file is not None:
            f = self.file
            access = self.access
            self.access = None
            self.file = None
            if access == 'write':
                for series in self.results.series.values():
                    series.close()
            f.close()

    def _openFileForReading(self, fileName):
        self.fileData = FileData()
        self.file = h5py.File(fileName, 'r')       
        if not 'mtsfVersion' in self.file.attrs.keys():
            print "Can only read mtsf-file. Unsupported file type for " + fileName
            self.close()           
        else:
            self.fileName = fileName
            self.access = 'read'
          

    def readVariableList(self):
        if not hasattr(self, 'fileData'):
            self.fileData = FileData()
        if self.fileData.variables is None:
            self.fileData.variables = self.file["ModelDescription/Variables"]
        if self.fileData.nameList is None:
            self.fileData.nameList = self.fileData.variables["name", :, 0].tolist()
        if self.fileData.objectIdList is None:
            self.fileData.objectIdList = self.fileData.variables["objectId", :, 0].tolist()
        if self.fileData.columnList is None:
            self.fileData.columnList = self.fileData.variables["column", :, 0].tolist()
        if self.fileData.negatedList is None:
            self.fileData.negatedList = self.fileData.variables["negated", :, 0].tolist()
        if self.fileData.descriptionList is None:
            self.fileData.descriptionList = self.fileData.variables["description", :, 0].tolist()


    def readData(self, variableNameIn):
        ''' Reads numerical data from file for the variable given by its String-name  variableNameIn
        
            Outputs:
               t        numpy-array       Values of independent variable (normally time)
               y        numpy-array       Values of the given variable
               method   String            Interpolation method, e.g. 'linear', 'constant' or 'clocked'
        '''        
        
        if not self.readable:
            return None, None, None            
        
        variableName = convertDer(variableNameIn)
        self.readVariableList()
        variableRowIndex = self.fileData.nameList.index(variableName)        
        seriesOfVariable = self.file[self.fileData.objectIdList[variableRowIndex]].parent.ref
        method = self.file[seriesOfVariable].attrs["interpolationMethod"]
        if self.access == 'write':
            scalar = self.modelVariable[variableNameIn]
            seriesName = self.allSeries[scalar.seriesIndex].name
            categoryName = self.allCategories[scalar.categoryIndex]
            category = self.results.series[seriesName].category[categoryName]
            row = category.currentRow
            _row = category._currentRow
        else:
            row = self.file[self.fileData.objectIdList[variableRowIndex]].shape[0]
            _row = 0
        if row > 0 or _row > 0:
            variableColumn = self.fileData.columnList[variableRowIndex]
            independentVariableRow = self.file[seriesOfVariable].attrs["independentVariableRow"]
            if independentVariableRow > -1:
                TimeRowIndex = independentVariableRow
                timeColumn = self.fileData.columnList[TimeRowIndex]
            else:
                TimeRowIndex = None
        y1 = None
        t1 = None
        if row > 0:
            if self.fileData.negatedList[variableRowIndex] == 1:
                y1 = -self.file[self.fileData.objectIdList[variableRowIndex]][:row, variableColumn]
            else:
                y1 = self.file[self.fileData.objectIdList[variableRowIndex]][:row, variableColumn]
            if TimeRowIndex is not None:
                t1 = self.file[self.fileData.objectIdList[TimeRowIndex]][:row, timeColumn]
        y2 = None
        t2 = None
        if _row > 0:
            y2 = category._data[0:_row, variableColumn]
            if TimeRowIndex is not None:
                timeName = self.fileData.nameList[TimeRowIndex]
                scalar = self.modelVariable[timeName]
                seriesName = self.allSeries[scalar.seriesIndex].name
                categoryName = self.allCategories[scalar.categoryIndex]
                category = self.results.series[seriesName].category[categoryName]
                t2 = category._data[0:_row, timeColumn]
        if y1 is None:
            if y2 is None:
                y = None
            else:
                y = y2
        else:
            if y2 is None:
                y = y1
            else:
                y = numpy.concatenate((y1, y2))
        if t1 is None:
            if t2 is None:
                t = None
            else:
                t = t2
        else:
            if t2 is None:
                t = t1
            else:
                t = numpy.concatenate((t1, t2))
        return t, y, method

    def getResultAttributes(self):
        ''' Returns the HDF5 attributes of /Results        
        '''
        info = dict()
        for aName, a in self.file["Results"].attrs.items():
            x = str(a)
            if len(x) > 0:
                info[aName] = x
        return info

    




