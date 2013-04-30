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
Created on 05.04.2012

@author: otter
'''
import numpy
from Internal        import StateSpace
from Internal        import ZerosAndPoles
from Plugins.Algorithms.Simulator.Sundials import SundialsIntegrators


class SignalInfo:
    """
    Handle attributes of input, output and state signals

    Attributes:
       names, units, descriptions

    Functions:
       __init__
       __str__
       getLabels       
       poles
       zeros
       frequencyResponse
       simulate
    """
    def __init__(self, names, units=None, descriptions=None):
        """
        Initialize a SignalInfo object

        Input arguments:
           names       : String list containing the names of the signals.
           units       : Optional string list containing the units of the signals
           descriptions: Optional string list containing the descriptions of the signals
                        
        If not None, the requirement is that len(names) = len(units) = len(descriptions)
        Note, it is not checked whether all elements of names, units, descriptions are strings.                         
        """
        # Check input arguments
        nsig = len(names)   
        if units != None and len(units) != nsig:
            raise ValueError("len(units) (= %d) is not identical to len(names) (= %d)."
                            % (len(units), len(names)) )                  
        if descriptions != None and len(descriptions) != nsig:
            raise ValueError("len(descriptions) (= %d) is not identical to len(names) (= %d)."
                            % (len(descriptions), len(names)) )        

        # Store input arguments
        self.nsig         = nsig   # number of signals         
        self.names        = names
        self.units        = units
        self.descriptions = descriptions


    def __str__(self):
        """
        String representation of a SignalInfo object
        """
        def getStringLengths(s):
            """ Get string lengths of all list elements """
            ns = numpy.zeros(len(s), dtype=int)
            for (i,ss) in enumerate(s):
                ns[i] = len(ss)
            return ns
            
        nNames = min(40, getStringLengths(self.names).max())
        nUnits = min(10, getStringLengths(self.units).max()) 
        
        s = "[\n"
        for (i,name) in enumerate(self.names):
            s += "   {:<{width}}".format(name,width=nNames)            
            if self.units != None or self.descriptions != None:
                s += " # "
                if self.units != None:
                    s += "[{:<{width}}] ".format(self.units[i], width=nUnits)
                if self.descriptions != None:
                    s += self.descriptions[i]
            s += "\n"
        s += "  ]\n"            
        return s


class LTI:
    """
    Linear Time Invariant (LTI) system described either as state space system

         der(x) = A*x + B*u
              y = C*x + D*u

    or as transfer function matrix
    
         xxx
     
    Attributes:
       info, 
       info_u, info_y, info_x,
       nu, ny, nx,
       ss, zpk, tf

    Functions:
       __init__
       __str__
       eig
       zeros_ij
       
    """
    def __init__(self, ss=None, zpk=None, info=None, info_u=None, info_y=None, info_x=None):
        
        """
        Initialize an LTI object

        Either argument "ss" or "zpk" must be defined. All other arguments are optional
        
        Input arguments:
           ss    : LTI object defined by state space system as tuple (A,B,C,D).
           zpk   : LTI object defined by a matrix of transfer functions zpk_ij
                   where one element of the matrix is a tuple (k, zeros, poles).
                   (not yet implemented)
           info  : Optional string describing the object
           info_u: Optional (names, units, descriptions) tuple describing the inputs
           info_y: Optional (names, units, descriptions) tuple describing the outputs
           info_x: Optional (names, units, descriptions) tuple describing the states (only if ss != None)
        """        
        # Check inputs
        if info_x != None:
            self.info_x = SignalInfo(*info_x)
        else:
            self.info_x = None
                    
        if ss == None and zpk == None:
            raise ValueError("one of ss or zpk must be not None")
        elif ss != None:
            self.ss = StateSpace.StateSpace(*ss)
            self.nu = self.ss.nu
            self.ny = self.ss.ny
            if info_x != None and self.ss.nx != self.info_x.nsig:
                raise ValueError("The number of states of argument ss is not identical\n" +
                                 "to the number of signals of argument info_x")
            self.nx = self.ss.nx
            self.zpk = None            
        else:
            self.zpk = ZerosAndPoles.ZerosAndPoles(zpk)
            self.nu = self.zpk.nu
            self.ny = self.zpk.ny
            self.ss = None            
        self.info = info
        
        if info_u != None:
            self.info_u = SignalInfo(*info_u)
        else:
            self.info_u = None
            
        if info_y != None:
            self.info_y = SignalInfo(*info_y)
        else:
            self.info_y = None
       
        # Check the dimensions
        if info_u != None and self.nu != self.info_u.nsig:
            raise ValueError("The number of inputs of argument ss is not identical\n" +
                             "to the number of signals of argument info_u")       
        if info_y != None and self.ny != self.info_y.nsig:
            raise ValueError("The number of output of argument ss is not identical\n" +
                             "to the number of signals of argument info_y")


    def __str__(self):
        """
        String representation of an LTI object
        """
        if self.info != None:
            s = '  info = "' + str(self.info) + '"\n'
        else:
            s = ""

        # Print dimensions
        s += "  nu = " + str(self.nu) + ", ny = " + str(self.ny)
        if self.ss != None:  s += ", nx = " + str(self.nx)
       
        # Print names, units, descriptions of all signals
        if self.info_u != None:
            s += "\n  info_u = " + str(self.info_u)
        if self.info_y != None:
            s += "  info_y = " + str(self.info_y)
        if self.info_x != None:
            s += "  info_x = " + str(self.info_x)            

        # Print system description
        if self.ss != None:
            s += str(self.ss)
        else:
            s += str(self.zpk)                        
        return s
    
    
    def getLabels(self, u_indices=None, y_indices=None):
        """
        Return label matrix for plotting
        
        Input arguments:
           u_indices: If none, the labels of all inputs are constructed.
                      Otherwise, u_indices are the indices of the inputs for which
                      the labels shall be constructed. For example indices_u=(0,3,4)
                      means to return the labels for u[0], u[3], u[4].
           y_indices: If none, the labels of all outputs are constructed.
                      Otherwise, y_indices are the indices of the outputs for which
                      the labels shall be constructed. For example indices_y=(0,3,4)
                      means to return the labels for y[0], y[3], y[4].
        
        Output arguments
           (u_names, u_units, y_names, y_units)
                      If units are not defined u_units and/or y_units are returned as None.  
                      u_names and y_names are always returned as vector of strings. 
                      If no names are defined, default names are constructed (e.g. "u[0]"). 
        """
        # Normalize indices
        if u_indices == None:
            ui = range(0,self.nu)
        else:
            ui = u_indices
        if y_indices == None:
            yi = range(0,self.ny)
        else:
            yi = y_indices
            
        # Utility function
        def getInfo(info, indices, defaultName):
            if info == None:
                names = [ "{}[{}]".format(defaultName, i) for i in indices ]
                units = None
            else:
                names = [ info.names[i] for i in indices ]
                units = info.units
                if info.units == None:
                    units = None
                else:
                    units = [ info.units[i] for i in indices ]
            return (names, units)
        
        # Generate u names/units
        (u_names, u_units) = getInfo(self.info_u, ui, "u")
        (y_names, y_units) = getInfo(self.info_y, yi, "y")                
        return (u_names, u_units, y_names, y_units)


    def eig(self, left=False, right=False):
        """
        Return the eigen values and optionally the left and/or right eigen vectors
        """
        return self.ss.eig(left=left,right=right)


    def zeros_ij(self, ui=0, yj=0):
        """
        Return the invariant zeros from input u[ui] to output y[yj]
        """
        return self.ss.zeros_ij(ui=ui, yj=yj)

                
    def frequencyResponse(self, n=200, f_range=None, f_logspace=True, u_indices=None, y_indices=None):
        """
        Compute frequency response of lti system from selected inputs to selected outputs
        
        Input arguments:
           n        : Number of result intervals (default = 200)
                      The result will have n+1 frequency points per transfer function
           f_range  : Frequency range as tuple (f_min, f_max) in [Hz]
                      If f_range=None, the range is automatically selected (default). 
                      Otherwise, the provided range is used.
           f_logspace: = True , if frequency values are logarithmically spaced (default) 
                       = False, if frequency values are linearly spaced
           u_indices: If none, the frequency response is computed from all inputs.
                      Otherwise, u_indices are the indices of the inputs for which
                      the frequency response shall be computed. For example indices_u=(0,3,4)
                      means to compute the frequency responses from u[0], u[3], u[4] to the select outputs.
           y_indices: If none, the frequency response is computed to all outputs.
                      Otherwise, y_indices are the indices of the outputs for which
                      the frequency response shall be computed. For example indices_y=(0,3,4)
                      means to compute the frequency responses from selected inputs to 
                      the outputs y[0], y[3], y[4].
           
        Output arguments (f,Y): 
           Tuple of the frequency vector f and the response matrix Y(s) with s=0+f*1j
           f: The float numpy vector of frequency points in [Hz] in logarithmic scale.
           Y: The complex numpy matrix of response values Y[i,j](s).
              For example if u_indices=(0,3) and y_indices=(4), then 
                 Y[0,0]: response from u[0] -> y[4]
                 Y[0,1]: response from u[3] -> y[4]
        """
        if self.zpk != None:
            # zpk given or ss already transformed to zpk
            return self.zpk.frequencyResponse(n=n, f_range=f_range, f_logspace=f_logspace, 
                                              u_indices=u_indices, y_indices=y_indices)
        # Transform to zpk matrix
        self.zpk = self.ss.to_zpk()
        return self.zpk.frequencyResponse(n=n, f_range=f_range, f_logspace=f_logspace, 
                                          u_indices=u_indices, y_indices=y_indices) 

    
    def timeResponse(self, tstart=0.0, tstop=1.0, nint=500, x0=None, Ut=None, tol=1e-4):
        """
        Compute the time response of an lti system for given inputs
        
        Algorithm:
           Using the variable step, variable order solver VODE 
           with discretization method BDF
           (so that stiff systems can be efficiently simulated).
           
        Input arguments
           tstart: Start time
           tstop : Stop time
           nint  : Number of time intervals of the result
           x0    : Initial state
           Ut    : (t,U) tuple of time and U(t) matrix
           tol   : Relative tolerance   
        
        Output arguments
           (t,Y) : Tuple of time vector t (= numpy.linspace(tstart,tstop,nint+1))
                   and of Y[i,j] result matrix, where the value of y[j] at time 
                   instant t[i] is stored at Y[i,j]
        """
        if self.ss == None:
            raise ValueError("Currently timeResponse is only available for state space (ss) systems.")

        # Create arrays for the result and for utility vectors
        nt = nint + 1  # Number of time steps
        t  = numpy.linspace(tstart, tstop, nt)
        Y  = numpy.zeros( (nt,self.ny) )
        if x0 == None:
            xt = numpy.zeros( self.nx )
        else:
            xt = x0
        
        # Define shortcuts
        A = self.ss.A
        B = self.ss.B
        C = self.ss.C
        D = self.ss.D
        dot = numpy.dot

        # Integrate the lti system                            
                       
        # Define utility function used in the integrator
        def f(t, x):
            """
            Define differential equation to be simulated
               der(x) = A*x + B*u
            """
            return dot(A,x) # + numpy.dot(B,u)    

        tout = []
        Yout = []
        def handle_result(t, x):
            """
            Function called after every successful step and after an event
            
            Input arguments
                t: Actual time
                x : State vector               
            """            
            tout.append(t)
            Yout.append(dot(C, x)) #[i,:]
            
            print "obtained result at t=",t," with y=", Yout[-1]
              
        #We have no state events, so add a constant switch function:
        def state_events(t, x):            
            return numpy.ones(1)
            
        def time_events(t, x):    
            return self.nextTimeEvent
        
        def completed_step(solver):           
            return False   
                   
        def finalize():     
            pass                       
                   
        def handle_event(solver, event_info=None):   

            #Get the next time event 
            self.nextTimeEvent = next(x[1] for x in enumerate(self.timeEvents) if x[1] > solver.t_cur)

            # Results at events are not handled by Cvode,
            # so we handle it here before the event updates
            self.handle_result(solver, solver.t_cur, solver.y_cur)
            return True 
            
                   
        simulator = SundialsIntegrators.SundialsCVode()
        
        simulator.t0 = tstart           
        simulator.y0 = x0            
        simulator.atol = tol
        simulator.rtol = tol
        
        simulator.handle_result = handle_result             
        simulator.rhs = f        
        self.state_events = state_events
        self.handle_event = handle_event
        self.time_events = time_events
        self.finalize = finalize
        self.completed_step = completed_step
        
        if Ut <> None:
            self.timeEvents = [Ut[x,0] for x in numpy.arange(Ut[:,0].shape[0]-1) if Ut[x,0] == Ut[x+1,0]]
            if not self.timeEvents:
                self.nextTimeEvent = 1e10
            else:
                self.nextTimeEvent = self.timeEvents[0]  
        else:
            self.nextTimeEvent = 1e10   
                  
        simulator.simulate(tstop, nint, None)   #select gridWidth = None to work with number of intervals nint

        #sim = ode(f).set_integrator("vode", method="bdf", rtol=tol)
        #sim.set_initial_value(xt,tstart)
        #for (i,tt) in enumerate(t):
        #    if i > 0: sim.integrate(tt)
        #    # Store y = C*x + B*u
        #    Y[i,:] = dot(C,sim.y)            
        
        
        return (numpy.array(tout), numpy.array(Yout))




        
    
            
                   
if __name__ == "__main__":
    # Test SignalInfo
    info = SignalInfo(["u1", "u21", "u311"],
                      ["m", "kg", "W/s"],
                      ["first input", "second input", "third input"])
    print("info =" + str(info))

    # Generate and print an LTI system without signal information
    lti1 = LTI( ([[1,2],[3,4]], [1,3], [3,4], [4]) )
    print("lti1 =\n" + str(lti1))
    
    # Generate and print an LTI system with signal information
    lti2 = LTI( ([[1,2,3],[4,5,6],[7,8,9]],
                 [[11,12],[21,22],[31,32]],
                 [[11,12,13],[21,22,23]],
                 ),
                 info = "Linearized system of a drive train",
                 info_u = (["u1", "u2"], ["N", "Nm"] , ["Force acting on flange_a", "Torque acting on flange_b"]),
                 info_y = (["y1", "y2"], ["m", "rad"], ["Position of mass", "Angle of inertia"]),
                 info_x = (["x1", "x2", "x3"], ["V", "A", "W"], ["Voltage of source", "Current of source", "Active power"])
              )
    print("lti2 =\n" + str(lti2))
  
    # Generate LTI SISO system
    lti3 = LTI( ([[1, 2, 3],
                  [4,-5,-6],
                  [7, 8, 5]], numpy.ones((3,1)), numpy.ones((1,3)), [[0]]))

    # Print eigen values
    poles = lti3.eig()
    print("poles = \n" + str(poles))
    
    # Print zeros
    zeros = lti3.zeros_ij()
    print("zeros = \n" + str(zeros))
    
    # Perform a time response
    T = 0.1
    lti4 = LTI( ([[-1/T]],None,[[1]],None) )
    print("lti4 = " + str(lti4))
    (t,y) = lti4.timeResponse(nint=10,x0=[1])
    print("t={}\ny={}\n".format(t,y))
    
    
    
    
    
