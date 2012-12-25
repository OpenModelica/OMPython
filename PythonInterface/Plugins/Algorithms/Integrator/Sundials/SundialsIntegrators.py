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


import numpy as np
from sundials import *


class SundialsCVode():  
    
    def __init__(self):
                       
        #Have to be set from outside:
        self.iter = 'FixedPoint'
        self.discr = 'Adams'
        self.atol = 1e-6 
        self.rtol = 1e-6
        self.verbosity = 0

        self.rhs = None
        self.handle_result = None
        self.state_events = None
        self.handle_event = None
        self.time_events = None
        self.finalize = None
        self.completed_step = None # NOT supported
        self.t0 = 0           
        self.y0 = None
        self.yd0 = None
        

    def f(self, t, y, sw):
        yarray = np.array(y)    
        return self.rhs(t,yarray)

    def rootf(self, t, y, sw):
        yarray = np.array(y)       
        rootfunctions = self.state_events(t, yarray)
        return rootfunctions

    
    def simulate(self, Tend, nIntervals, gridWidth):   
        # Create Solver and set settings 
        noRootFunctions = np.size(self.state_events(self.t0, np.array(self.y0) ))        
        solver = CVodeSolver(RHS = self.f, ROOT = self.rootf, SW = [False]*noRootFunctions,
                       abstol = self.atol, reltol = self.rtol)
        
        

        #Change multistep method: 'adams' or 'bdf'
        if self.discr == 'Adams':
            solver.settings.lmm = "adams"
            solver.settings.maxord = 12
        else:
            solver.settings.lmm = "bdf"    
            solver.settings.maxord = 5
        '''  '''    
        #Change iteration algorithm: functional(FixedPoint) or newton
        if self.iter == 'FixedPoint':
            solver.settings.iter = 'functional'  
        else:
            solver.settings.iter = 'newton'
                               
        solver.settings.JAC = None   #Add user-dependent jacobian here        
        
        '''Initialize problem '''
        solver.init(self.t0, self.y0)
        self.handle_result(self.t0, self.y0) 
        nextTimeEvent = self.time_events(self.t0, self.y0)   
        self.t_cur = self.t0
        self.y_cur = self.y0
        state_event = False
               
               
        if gridWidth <> None:
            nOutputIntervals = int((Tend - self.t0)/gridWidth)
        else:
            nOutputIntervals = nIntervals
        #Define step length depending on if gridWidth or nIntervals has been chosen
        if nOutputIntervals > 0:
            #Last point on grid (does not have to be Tend:)
            if(gridWidth <> None):
                dOutput = gridWidth
            else:
                dOutput = (Tend - self.t0) / nIntervals
        else:
            dOutput = Tend
        
        outputStepCounter = long(1)        
        nextOutputPoint = min(self.t0 + dOutput, Tend)        
               
        while self.t_cur < Tend:

            
            #Time-Event detection and step time adjustment
            if nextTimeEvent is None or nextOutputPoint < nextTimeEvent:
                time_event = False
                self.t_cur = nextOutputPoint
            else:
                time_event = True             
                self.t_cur = nextTimeEvent                       

   
            try:
                #Integrator step
                self.y_cur = solver.step(self.t_cur) 
                self.y_cur = np.array(self.y_cur)                
                state_event = False                    
                
            except CVodeRootException, info:
                self.t_cur = info.t
                self.y_cur = info.y
                self.y_cur = np.array(self.y_cur)
                time_event = False             
                state_event = True
                
            
            # Depending on events have been detected do different tasks  
            if time_event or state_event:
                event_info = [state_event, time_event]
                if not self.handle_event(self, event_info):
                    break          
                solver.init(self.t_cur, self.y_cur)                   
                
                nextTimeEvent = self.time_events(self.t_cur, self.y_cur) 
                #If no timeEvent happens:
                if nextTimeEvent<=self.t_cur:
                    nextTimeEvent = None
            
            if self.t_cur == nextOutputPoint:           
                #Write output if not happened before:
                if not time_event and not state_event:
                    self.handle_result(nextOutputPoint, self.y_cur)                
                outputStepCounter += 1
                nextOutputPoint = min(self.t0 + outputStepCounter * dOutput, Tend)  
                              
        self.finalize()    


class SundialsIDA():  
    
    def __init__(self):
        
        #Have to be set from outside:
        self.iter = 'FixedPoint'
        self.discr = 'Adams'
        self.atol = 1e-6 
        self.rtol = 1e-6
        self.verbosity = 0

        self.rhs = None
        self.handle_result = None
        self.state_events = None
        self.handle_event = None
        self.time_events = None
        self.finalize = None
        self.completed_step = None # NOT supported
        self.t0 = 0           
        self.y0 = None
        self.yd0 = None


    def f(self, t, y, yd, sw):
        yarray = np.array(y)
        ydarray = np.array(yd)   
        return self.rhs(t,yarray, ydarray)

    def rootf(self, t, y, yd, sw):
        yarray = np.array(y)                 
        rootfunctions = self.state_events(t, yarray)
        return rootfunctions
    
        
    def simulate(self, Tend, nIntervals, gridWidth):   

        ''' Create Solver and set settings '''
        noRootFunctions = np.size(self.state_events(self.t0, np.array(self.y0) ))          
        solver = IDASolver(RES = self.f, ROOT = self.rootf, SW = [False]*noRootFunctions,       
                       abstol = self.atol, reltol = self.rtol)
   
        solver.settings.maxord = 5          #default 5, Maximum order
        solver.settings.mxsteps = 5000      #default 500, Maximum steps allowed to reach next output time
        solver.settings.hmax = 1e37         #default inf, Maximum step size allowed         
        solver.settings.suppressalg = False #default False, indicates if algebraic var. should be suppressed in error testing
        solver.settings.lsoff = False       #default False, flag to turn off(True) or keep(False) linesearch algorithm
        
        solver.settings.JAC = None          #Add user-dependent jacobian here

        
        
        '''Initialize problem '''
        solver.init(self.t0, self.y0, self.yd0)
        self.handle_result(self.t0, self.y0) 
        nextTimeEvent = self.time_events(self.t0, self.y0)   
        self.t_cur = self.t0
        self.y_cur = self.y0
        self.yd_cur = self.yd0
        state_event = False
               
               
        if gridWidth <> None:
            nOutputIntervals = int((Tend - self.t0)/gridWidth)
        else:
            nOutputIntervals = nIntervals
        #Define step length depending on if gridWidth or nIntervals has been chosen
        if nOutputIntervals > 0:
            #Last point on grid does not have to be Tend:
            if(gridWidth <> None):
                dOutput = gridWidth
            else:
                dOutput = (Tend - self.t0) / nIntervals
        else:
            dOutput = Tend
        
        outputStepCounter = long(1)        
        nextOutputPoint = min(self.t0 + dOutput, Tend)        
               
        
        while self.t_cur < Tend:
            
            #Time-Event detection and step time adjustment
            if nextTimeEvent is None or nextOutputPoint < nextTimeEvent:
                time_event = False
                self.t_cur = nextOutputPoint
            else:
                time_event = True             
                self.t_cur = nextTimeEvent                  

   
            try:
                #Integrator step                
                self.y_cur, self.yd_cur = solver.step(self.t_cur)
                self.y_cur = np.array(self.y_cur)
                self.yd_cur = np.array(self.yd_cur)                                
                state_event = False                       
                
            except IDARootException, info:
                self.t_cur = info.t
                self.y_cur = info.y
                self.y_cur = np.array(self.y_cur)
                self.yd_cur = info.ydot
                self.yd_cur = np.array(self.yd_cur)   
                time_event = False             
                state_event = True
                
            
            # Depending on events have been detected do different tasks  
            if time_event or state_event:
                event_info = [state_event, time_event]
                                
                if not self.handle_event(self, event_info):                    
                    break          
                solver.init(self.t_cur, self.y_cur, self.yd_cur)
               
                nextTimeEvent = self.time_events(self.t_cur, self.y_cur) 
                #If no timeEvent happens:
                if nextTimeEvent<=self.t_cur:
                    nextTimeEvent = None
                
            if self.t_cur == nextOutputPoint:           
                #Write output if not happened before:
                if not time_event and not state_event:
                    self.handle_result(nextOutputPoint, self.y_cur)                
                outputStepCounter += 1
                nextOutputPoint = min(self.t0 + outputStepCounter * dOutput, Tend)  
                              
        self.finalize()    

        