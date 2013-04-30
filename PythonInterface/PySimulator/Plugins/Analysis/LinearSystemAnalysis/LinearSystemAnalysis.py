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
    @author: Matthias J. Reiner (Matthias.Reiner@dlr.de)  
                     
    Plugin that allows to linearize a nonlinear model   
'''



from Plugins.Analysis.LinearSystemAnalysis.LinearizeFMU  import LinearizeFMU

def linearizeToMAT(model):
    ''' Example callback function for model specific actions
        parameter: a model instance    '''      
    if model.modelType != 'FMU1.0':            
        print("Error: Selected model must be an FMU !\n")           
        return
    try:
        matFileName=model.fileName[:-4]+'_lin.mat'           
        linSys=LinearizeFMU(FMUModel=model)
        linSys.writeDataToMat(matFileName)
        print("Writing A,B,C,D matrices to:")
        print(matFileName+"\n") 
        model.pluginData["LinearSystemAnalysis"] = linSys
    except:
        print("Error: Could not linearize model. FMU-model must have inputs and outputs defined!\n")

def linearizeAndShowABCD(model):
    ''' Example callback function for model specific actions
        parameter: a model instance    '''      
    if model.modelType != 'FMU1.0':            
        print("Error: Selected model must be an FMU !\n")           
        return
    try:       
        linSys=LinearizeFMU(FMUModel=model)                  
        print "Linearizing system with %i states, %i inputs and %i outputs" % (linSys.nx, linSys.nu, linSys.ny)      
        print("A = ")
        print linSys.A       
        print("B = ")
        print linSys.B        
        print("C = ")
        print linSys.C      
        print("D = ")
        print linSys.D       
        model.pluginData["LinearSystemAnalysis"] = linSys
    except:
        print("Error: Could not linearize model. FMU-model must have inputs and outputs defined!\n")
      
def fun1(model):
    print "Frequency Response."
    pass

def getModelCallbacks():
    ''' Registers model callbacks with main application
        return a list of lists, one list for each callback, each sublist
        containing a name for the function and a function pointer
    '''
    return [["Save to .mat", linearizeToMAT],["Display A,B,C,D", linearizeAndShowABCD],['Frequency Response', fun1]]


def getPlotCallbacks():
    ''' see getModelCallbacks
    '''    
    return []

