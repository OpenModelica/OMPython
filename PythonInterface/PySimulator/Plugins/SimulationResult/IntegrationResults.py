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


import os


class ResultVariable():
    ''' Class to hold information about a variable in a result file 
    '''
    def __init__(self, value, unit, variability, infos):
        #                                  Types
        self.value = value               # E.g. Float, Integer, Boolean
        self.unit = unit                 # String
        self.variability = variability   # String
        self.infos = infos               # Dictionary of Strings


class Results():
    ''' Base Class for hosting simulation results of each type.    
    '''
    def __init__(self):
        ''' Set important variables to default values 
        '''
        self.fileName = ''               # File name of result file
        self.isAvailable = False         # Shows, if there is a file available to be read 
        self.canLoadPartialData = False  # True, if data can be loaded from
        #                                  result file although simulation is not finished

    
    def readData(self, variableName):
        ''' Returns numeric data of the variable given by its name variableName.
            The Time vector t is returned as well as the data-vector y. Both
            vectors are numpy vectors.
            The third return value method is a String, that indicates how the
            result points shall be interpreted. Possible values for method are
            'linear' for linear interpolation, 'constant' for constant interpolation
            and 'clocked' for discrete values only at the time instances.        
        '''
        pass
        #return t, y, method  # Types  numpy-array, numpy-array, String
    
    def getVariables(self):
        ''' Returns a dictionary with names of variables as keys
            and instances of ResultVariable as values. This
            dictionary is used to generate the variable tree
            in the variable browser (see SimulatorBase.py),
            if the model type is 'None'. It means that this function
            is called if only the
            result file is loaded without model information.         
        '''
        pass
        # return allVariables
    
    def getFileInfos(self):
        ''' Returns a dictionary with property names as keys
            and property Strings as values. This
            dictionary is used to generate result file informations
            for variable browser (see SimulatorBase.py),
            if the model type is 'None'. It means that this function
            is called if only the
            result file is loaded without model information.        
        '''
        pass
        # return fileInfos
    
    def fileSize(self):
        ''' Returns a String with the file size of the result file in MB.
            If file does not exist, the return value is None. 
        '''
        fs = None
        if self.fileName is not None and self.fileName != '':
            if os.path.exists(self.fileName):
                fs = os.path.getsize(self.fileName) / 1048576.0
        return fs   
     
    def close(self):
        ''' Closes the simulation result, especially closing the file 
            or releasing resources can be done here.        
        '''
        pass
