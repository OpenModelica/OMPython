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

import os, numpy, scipy.io, string, collections 
from Plugins.SimulationResult import IntegrationResults

# Exception classes
class FileDoesNotExist     (Exception): pass
class UnknownIndex         (Exception): pass
class UnknownArgument      (Exception): pass
class WrongDymolaResultFile(Exception): pass


def charArrayToStrList(charArray):
    """Transform a numpy character array to a list of strings
    """
    strList = []
    for item in charArray:
        strList.append(str(string.rstrip(string.join(item,""))))
    return strList


def convertDer(variableName):
    ''' Converts a variable name  a.b.c.d_(der)  to  a.b.c.der(d)
        If no "_(der)" is contained in variableName, the name
        is returned unchanged.
    '''    
    x = variableName
    x = x.replace('.[', '[')
    if len(x) > 6:
        if x[-6:] == '_(der)':
            x= x[:-6]
            k = x.rfind('.')
            if k > -1:
                x = x[:k] + '.der(' + x[k+1:] + ')'
            else:
                x = 'der(' + x + ')'
    return x    
        
class DymolaResult(IntegrationResults.Results):
    """ Result Object to hold a Dymola result file, see also
        class IntegrationResults.Results
    """
    def __init__(self, fileName, name, description, unit, dataInfo, data):
        IntegrationResults.Results.__init__(self)
        if fileName is not None:
            if fileName is not '':
                self.isAvailable = True
                
        # Not possible to load data from a partially written mat-file
        self.canLoadPartialData = False
        
        self.fileName     = fileName
        self._name        = name
        self._description = description
        self._unit        = unit
        self._dataInfo    = dataInfo
        self._data        = data
        
    def index(self, name):
        """ Return the index of variable 'name' (= full Modelica name)
        
            Examples:
               result = loadDymolaResult()
               i_v1   = result.index("a.b.c")   # get index of signal
        """
        try: 
            nameIndex = self._name.index(name)
        except ValueError:
            return -1
            #print("'" + name + "' is not present in the result")
        return nameIndex
        
    def readData(self, variableName):
        name = convertDer(variableName)
        y = self.data(name)
        t = self.data("Time")
        method = 'linear'
        return t, y, method
    
    
        
    def data(self, name):
        """ Return the result values of variable 'name' (= full Modelica name)
        
            Examples:
               result = loadDymolaResult()
               time   = result.data("Time")     # numpy vector of time instants
               v1     = result.data("a.b.c")    # numpy vector of v1 values
               i_v1   = result.index("a.b.c")   # get index of signal
               v1     = result.data(i_v1)       # numpy vector of v1 values
        """
        # Get index of the desired signal and check it
        if isinstance(name,str):
            nameIndex = self.index(name)
        elif isinstance(name,int):
            if name < 0 or name >= len(self._name):
                raise UnknownIndex("Index = " + str(name) + " is not correct")
            nameIndex = name
        else:
            raise UnknownArgument("Argument name must be a string or an int")
        if nameIndex < 0:
            return None
        
        # Determine location of data
        signalInfo   = self._dataInfo[nameIndex,:]
        signalMatrix = signalInfo[0] if nameIndex > 0 else 2
        if signalMatrix < 1 or signalMatrix > 2:
            raise WrongDymolaResultFile("dataInfo[" + str(nameIndex) +
                                        ",0] = " + str(signalMatrix) +
                                        ", but must be 1 or 2")
        signalColumn = abs(signalInfo[1])-1
        signalSign   = +1 if signalInfo[1] >= 0 else -1
        if signalMatrix == 1:
            # Data consists of constant data, expand data to match abscissa vector
            n = self._data[1].shape[0]
            signalData = signalSign*self._data[0][0,signalColumn]*numpy.ones(n)
        else: # signalMatrix = 2
            signalData = signalSign*self._data[1][:,signalColumn]
        return signalData
      
    
    def getFileInfos(self):
        # No relevant file infos stored in a Dymola result file
        return dict()
   
    def getVariables(self):        
        # Generate the dict           
        variables = dict()
        
        # Fill the values of the dict        
        for i in xrange(len(self._name)):
            name = self._name[i].replace('[', '.[')
            if self._dataInfo[i,0] == 1:
                variability = 'fixed'
            else:
                variability = 'continuous'
            
            value = None
            if variability == 'fixed':                    
                y = self.data(name)                                           
                value = y[0]
                        
            infos = collections.OrderedDict()
            if self._description[i] is not None:
                if len(self._description[i]) > 0: 
                    infos['Description'] = self._description[i]
            infos['Variability'] = variability                
            if len(self._unit[i]):
                unit = self._unit[i]
            else:
                unit = None
                
            variables[name] = IntegrationResults.ResultVariable(value, unit, variability, infos)          
        
        return variables

def loadDymolaResult(fileName):
    """ Load Dymola simulation result data in a DymolaResult object.
    
        Example:
           result = loadDymolaResult("controller.mat")          
           result.name  # Variable names of the result
    """   
    # If no fileName given, return
    if fileName == None:
        return        
    
    # Check if fileName exists
    if not os.path.isfile(fileName):
        raise FileDoesNotExist("File '" + fileName + "' does not exist")
    
    # Determine complete file name
    fullFileName = os.path.abspath(fileName)

    # Read data from file
    fileData = scipy.io.loadmat(fullFileName, matlab_compatible=True)
    
    # Check Aclass array
    if not("Aclass" in fileData):
        raise WrongDymolaResultFile("Matrix 'Aclass' is missing in result file " + fullFileName)
    Aclass  = charArrayToStrList( fileData["Aclass"] ) 
    if len(Aclass) < 3:
        raise WrongDymolaResultFile("Matrix 'Aclass' has not 3 or more rows in result file " + fullFileName)
    if Aclass[1] != "1.1":
        raise WrongDymolaResultFile("Amatrix[1] is not '1.1' in result file " + fullFileName)
   
    # Check whether other matrices are on the result file
    if not("name" in fileData):
        raise WrongDymolaResultFile("Matrix 'name' is not in result file " + fullFileName)
    if not("description" in fileData):
        raise WrongDymolaResultFile("Matrix 'description' is not in result file " + fullFileName)
    if not("dataInfo" in fileData):
        raise WrongDymolaResultFile("Matrix 'dataInfo' is not in result file " + fullFileName)
    if not("data_1" in fileData):
        raise WrongDymolaResultFile("Matrix 'data_1' is not in result file " + fullFileName)
    if not("data_2" in fileData):
        raise WrongDymolaResultFile("Matrix 'data_2' is not in result file " + fullFileName)
    
    # Get the raw matrices
    name        = fileData["name"]
    description = fileData["description"]
    dataInfo    = fileData["dataInfo"]
    data        = [ fileData["data_1"], fileData["data_2"] ]
        
    # Transpose the data, if necessary
    if len(Aclass) > 3 and Aclass[3] == "binTrans":
        name        = name.T
        description = description.T
        dataInfo    = dataInfo.T
        data[0]     = data[0].T
        data[1]     = data[1].T
        
   
    # Transform the charArrays in string lists
    name        = charArrayToStrList(name)
    # Hack for OpenModelica: Rename variable 'time' to 'Time'
    if name.count('time') > 0:
        name[name.index('time')] = 'Time'
        
    description = charArrayToStrList(description)
    
    # Extract units and update description
    unit, description = extractUnits(description)                
        
    # Generate a DymolaResult object and return it
    result = DymolaResult(fullFileName, name, description, unit, dataInfo, data)
    return result

def extractUnits(description):
    ''' Extract units from description and update description
    '''
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
                        description[index] = ''#
    return unit, description


class DymolaInit():
    ''' Separate class for initialization file of Dymola's simulation executable    
    '''
    def __init__(self, name, value, unit, description):
        self.name = name
        self.value = value
        self.unit = unit
        self.description = description
        

def loadDymolaInit(fileName):
    """ Load Dymola initial data in an object.       
    """
    
    # If no fileName given, return
    if fileName == None:
        return        
    
    # Check if fileName exists
    if not os.path.isfile(fileName):
        raise FileDoesNotExist("File '" + fileName + "' does not exist")
    
    # Determine complete file name
    fullFileName = os.path.abspath(fileName)

    # Read data from file
    fileData = scipy.io.loadmat(fullFileName, matlab_compatible=True)
    
    # Check Aclass array
    if not("Aclass" in fileData):
        raise WrongDymolaResultFile("Matrix 'Aclass' is missing in file " + fullFileName)
    Aclass  = charArrayToStrList( fileData["Aclass"] ) 
    if len(Aclass) < 3:
        raise WrongDymolaResultFile("Matrix 'Aclass' has not 3 or more rows in file " + fullFileName)
    if Aclass[1] != "1.4":
        raise WrongDymolaResultFile("Amatrix[1] is not '1.1' in file " + fullFileName)
   
    # Check whether other matrices are on the result file
    if not("initialName" in fileData):
        raise WrongDymolaResultFile("Matrix 'initialName' is not in file " + fullFileName)
    if not("initialDescription" in fileData):
        raise WrongDymolaResultFile("Matrix 'initialDescription' is not in file " + fullFileName)
    if not("initialValue" in fileData):
        raise WrongDymolaResultFile("Matrix 'initialValue' is not in file " + fullFileName)
   
    
    # Get the raw matrices
    name        = fileData["initialName"]
    description = fileData["initialDescription"]
    value    = fileData["initialValue"]
    
        
    # Transpose the data, if necessary
    if len(Aclass) > 3 and Aclass[3] == "binTrans":
        name        = name.T
        description = description.T
        value       = value.T
        
    
    # Transform the charArrays in string lists
    name        = charArrayToStrList(name)            
    description = charArrayToStrList(description)
    
    # Extract units
    unit, description = extractUnits(description)                   
        
    # Generate a DymolaInit object and return it
    result = DymolaInit(name, value, unit, description)
    return result
    
    

##+++++++++++++++++++++++++++++++++++++++++++++++++++++
##++++++++++++++++        +++++++++++++++++++++++++++++
##+++++++++++++++  main()  ++++++++++++++++++++++++++++
##++++++++++++++++        +++++++++++++++++++++++++++++
##+++++++++++++++++++++++++++++++++++++++++++++++++++++

if __name__ == "__main__":
    print("... started")
    result = loadDymolaResult('Modelica.Blocks.Examples.PID_Controller.mat')
    print result.fileName
    print result._name
    print result._description
    t = result.index("Time")
    print("time="+str(t))
    t1 = result.data("Time")
    v1 = result.data("PI.y")
    result.plot("PI.y")
    raw_input("Press Enter: ") 
    


