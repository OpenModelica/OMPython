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
'''

import numpy
from Plugins.Simulator.FMUSimulator import  FMUSimulator

import scipy.io

class LinearizeFMU:
    ''' 
    This class generates a linear system represented by A.B,C,D matrices from a (nonlinear) FMU.
    The class in also provides some functions to analyze the linear system. 
    '''
    def __init__(self, FMUfileName=None,x=None,t=0.0,p=None,u_ss=None,tol=6e-6,FMUModel=None):
        ''' 
        Initialize the class with either the FMU directly via the file name (FMUfileName) or with an instance of a FMU (FMUModel).
        In addition a state (x) and start time (t) as well as a steady state input (u_ss) and 
        a tolerance for the linearization can be used as optional inputs.
        The parameters of the FMU for the linearization can be set by a dictionary (list) of parameters and their value for the linearization.
        
        An example for the use of the class:
            myLin=LinearizeFMU('./Examples/PythonLinearization_LinSys.fmu',x=numpy.array([1,2]),p={'p':2.0},u_ss=numpy.array([5]),tol=1e-4)
            print myLin.A
            print myLin.B
            print myLin.C
            print myLin.D
        '''    
        if FMUModel is None:
            self.fmu = FMUSimulator.Model(modelName=None,modelFileName=FMUfileName,loggingOn=False) 
        else:
            self.fmu=FMUModel
        self.inputNames=[]
        self.outputNames=[]
        self.stateNames = self.fmu.getStateNames()   
        scalVars=self.fmu.description.scalarVariables        
        for name, v in scalVars.iteritems():              
            if v.causality=='output':                
                self.outputNames.append(name)
            if v.causality=='input':                
                self.inputNames.append(name)
        self.outputNames.sort()
        self.inputNames.sort()       
        self.nx=len(self.stateNames)       
        self.nu=len(self.inputNames)
        self.ny=len(self.outputNames)
        #if p is not None:
        self.p=p
        self.A,self.B,self.C,self.D = self.linearize(x,t,p,u_ss,tol)
    def changeModel(self, FMUmodel,x=None,t=0.0,u_ss=None,tol=6e-6):
        '''
        Change the FMU model used for the linearization and linearize the model.
        In addition a state (x) and start time (t) as well as a steady state input (u_ss) and 
        a tolerance for the linearization can be used as inputs.
        '''
        self.fmu = FMUmodel
        self.inputNames=[]
        self.outputNames=[]
        self.stateNames = self.fmu.getStateNames()   
        scalVars=self.fmu.description.scalarVariables        
        for name, v in scalVars.iteritems():              
            if v.causality=='output':                
                self.outputNames.append(name)
            if v.causality=='input':                
                self.inputNames.append(name)
        self.outputNames.sort()
        self.inputNames.sort()       
        self.nx=len(self.stateNames)       
        self.nu=len(self.inputNames)
        self.ny=len(self.outputNames)
        self.p=self.fmu.changedStartValue
        self.A,self.B,self.C,self.D = self.linearize(x,t,self.p,u_ss,tol)
    @property
    def eigenValues(self):
        '''Get the eigenvalues a of A.'''                   
        if self.A.shape[0] > 1:
            D, _ = numpy.linalg.eig(self.A)            
        else:
            D = self.A  
        return numpy.array(D) 
    @property
    def eigenVectors(self):
        '''Get the eigenvectors of A.'''                   
        if self.A.shape[0] > 1:
            _, V = numpy.linalg.eig(self.A)
        else:
            V = 1            
        return numpy.array(V) 
    def jacobian(self,x=None,t=0.0,p=None,u_ss=None,tol=6e-6):
        ''' Calculate the Jacobian at time t, parameter p and state x, input u_ss. Use tolerance tol for FMU and central diff. quotient'''
        if p is not None:
            self.fmu.changedStartValue=p
        self.fmu.initialize(t, tol)
        '''Define defaults if empty'''
        if x is None:            
            x=self.fmu.getStates()
        if u_ss is None:
            u_ss=0.0*numpy.ones(self.nx) 
        Jacobian=numpy.zeros((self.nx,self.nx))    
        E = numpy.identity(self.nx)
        for i in range(self.nx):
            h = tol* max( (numpy.abs(x[i]),1))
            x1 = x + E[i,:]*h/2
            ''' Set values'''
            for ii in range(self.nx):
                self.fmu.setValue(self.stateNames[ii],x1[ii])
            for ii in range(self.nu):
                self.fmu.setValue(self.inputNames[ii],u_ss[ii])              
            dx1=numpy.array(self.fmu.getDerivatives(t, x1))            
            x2 = x - E[i,:]*h/2
            ''' Set values'''
            for ii in range(self.nx):
                self.fmu.setValue(self.stateNames[ii],x2[ii])
            for ii in range(self.nu):
                self.fmu.setValue(self.inputNames[ii],u_ss[ii])                 
            dx2=numpy.array(self.fmu.getDerivatives(t, x2))
            Jacobian[:,i] = (dx1 - dx2)/h    
        return Jacobian
    
    
    def linearize(self,x=None,t=0.0,p=None,u_ss=None,tol=6e-6):
        ''' Calculate the A,B,C,D at time t, parameter p and state x, input u_ss. Use tolerance tol for FMU and central diff. quotient'''
        if p is not None:
            self.fmu.changedStartValue=p
        self.fmu.initialize(t, tol) 
        #Define defaults if empty
        if x is None:                  
            x=self.fmu.getStates()   
        if u_ss is None:
            u_ss=numpy.zeros(self.nx)        
        A=self.jacobian(x, t, p, u_ss, tol)
        B=numpy.zeros((self.nx,self.nu))   
        C=numpy.zeros((self.ny,self.nx))  
        D=numpy.zeros((self.ny,self.nu))   
        #Calc B
        E = numpy.identity(self.nx)
        for i in range(self.nu):
            h = tol* max( (numpy.abs(u_ss[i]),1))
            u1 = u_ss + E[i,:]*h/2           
            #Set values
            for ii in range(self.nx):
                self.fmu.setValue(self.stateNames[ii],x[ii])
            for ii in range(self.nu):
                self.fmu.setValue(self.inputNames[ii],u1[ii])        
            du1=numpy.array(self.fmu.getDerivatives(t, x))        
            u2 = u_ss - E[i,:]*h/2            
            #Set values
            for ii in range(self.nx):
                self.fmu.setValue(self.stateNames[ii],x[ii])
            for ii in range(self.nu):
                self.fmu.setValue(self.inputNames[ii],u2[ii])          
            du2=numpy.array(self.fmu.getDerivatives(t, x))
            B[:,i] = (du1 - du2)/h
            
        #Calc C    
        E = numpy.identity(self.nx)
        for i in range(self.nx):
            h = tol* max( (numpy.abs(x[i]),1))  
            x1 = x + E[i,:]*h/2             
            for ii in range(self.nx):
                self.fmu.setValue(self.stateNames[ii],x1[ii])
            for ii in range(self.nu):
                self.fmu.setValue(self.inputNames[ii],u_ss[ii])  
            dh1=[]
            for output in self.outputNames:           
                dh1.append(self.fmu.getValue(output))            
            dh1=numpy.array(dh1)
            x2 = x - E[i,:]*h/2              
            for ii in range(self.nx):
                self.fmu.setValue(self.stateNames[ii],x2[ii])
            for ii in range(self.nu):
                self.fmu.setValue(self.inputNames[ii],u_ss[ii])                     
            dh2=[]            
            for output in self.outputNames:           
                dh2.append(self.fmu.getValue(output))            
            dh2=numpy.array(dh2)
            C[:,i] = (dh1 - dh2)/h
        #Calc D    
        E = numpy.identity(self.nx)
        for i in range(self.nu):
            h = tol* max( (numpy.abs(u_ss[i]),1))
            u1 = u_ss + E[i,:]*h/2           
            for ii in range(self.nx):
                self.fmu.setValue(self.stateNames[ii],x[ii])
            for ii in range(self.nu):
                self.fmu.setValue(self.inputNames[ii],u1[ii])  
            dh1=[]
            for output in self.outputNames:           
                dh1.append(self.fmu.getValue(output))            
            dh1=numpy.array(dh1)
            u2 = u_ss - E[i,:]*h/2           
            for ii in range(self.nx):
                self.fmu.setValue(self.stateNames[ii],x[ii])
            for ii in range(self.nu):
                self.fmu.setValue(self.inputNames[ii],u2[ii])                     
            dh2=[]            
            for output in self.outputNames:           
                dh2.append(self.fmu.getValue(output))            
            dh2=numpy.array(dh2)
            D[:,i] = (dh1 - dh2)/h  
            self.A=A
            self.B=B
            self.C=C
            self.D=D
            self.p=p
        return A,B,C,D
    def writeDataToMat(self,matFileName):
        '''Write linearization data to MATLAB .mat file (with file name matFileName)'''
        try: 
            data = {}
            data['A'] = self.A
            data['B'] = self.B
            data['C'] = self.C
            data['D'] = self.D
            data['eigenValues']=self.eigenValues
            data['eigenVectors']=self.eigenVectors
            data['inputNames']=self.inputNames
            data['outputNames']=self.outputNames
            data['stateNames']=self.stateNames
            if self.p != None:           
                for name, value in self.p.iteritems():                    
                    data[name]=value            
            scipy.io.savemat(file_name=matFileName,mdict=data,oned_as='row')
        except Exception, info:
                print 'Error in writeDataToMat()'
                print info.message

    
if __name__ == '__main__':
    '''
    Test class functionality with simple examples
    '''
    fileName='./Examples/PythonLinearization_LinSys.fmu'    
    myLin=LinearizeFMU(fileName,x=numpy.array([1,2]),p={'p':2.0},u_ss=numpy.array([5]),tol=1e-4)
    print 'Linearization:'
    print myLin.A
    print myLin.B
    print myLin.C
    print myLin.D
    myLin.writeDataToMat('./Examples/PythonLinearization_LinSys.mat')
    fileName='./Examples/PythonLinearization_LinSysMIMO.fmu'
    myLin2=LinearizeFMU(fileName)
    print 'Linearization 2:'
    print myLin2.A
    print myLin2.B
    print myLin2.C
    print myLin2.D
    print myLin2.eigenValues
    print myLin2.eigenVectors    
    print myLin2.inputNames
    print myLin2.outputNames
    myLin2.writeDataToMat('./Examples/PythonLinearization_LinSysMIMO.mat')
    
    
    