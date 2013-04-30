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
Created on 08.04.2012

@author: otter
'''

import numpy
import math
import sys

def to_Hz(w):
    """ 
    Transform rad/s to Hz 
    
    Input arguments:
       w: [rad/s] (scalar or numpy array)
       
    Return arguments:       
       f: [Hz] (scalar or numpy array)
    """
    return w/(2*numpy.pi)


def from_Hz(f):
    """ 
    Transform Hz to rad/s 
 
    Input arguments:       
       f: [Hz] (scalar or numpy array)
          
    Return arguments:
       w: [rad/s] (scalar or numpy array)
    """
    return 2*numpy.pi*f


def to_deg(angle_rad):
    """ 
    Transform angle from rad to deg 
    
    Input arguments:
       angle_rad: [rad] Angle in rad (scalar or numpy array)
       
    Return arguments:       
       angle_deg: [deg] Angle in deg (scalar or numpy array)
    """
    return (180.0/numpy.pi)*angle_rad


def from_deg(angle_deg):
    """ 
    Transform angle from deg to rad 
    
    Input arguments:
       angle_deg: [deg] Angle in deg (scalar or numpy array)    
       
    Return arguments:       
       angle_rad: [rad] Angle in rad (scalar or numpy array)
    """
    return (numpy.pi/180.0)*angle_deg


def continuousAngle(c):
    """
    Return the angles of a complex vector, so that it is not discontinuous
    
    Input arguments:
       c: 1d numpy array of complex numbers 
       
    Output arguments:
       phi: 1d numpy array of float numbers with the same size as c, where basically
              phi[i] = numpy.angle(c[i])
            but phi[i] is modified so that from the infinite solutions of the angle
            always phi[i] is selected which is closest to phi[i-1].
    """
    c_phi = numpy.angle(c)
    c_old = 0.0
    pi    = numpy.pi
    pi2   = 2*numpy.pi
    for (i,phi) in enumerate(c_phi):
        aux = pi2*math.floor( (abs(phi-c_old)+pi) / pi2)
        if c_old > aux:
            c_phi[i] = phi+aux
        else:
            c_phi[i] = phi-aux
        c_old = c_phi[i]
    return c_phi


def frequencyRange(zeros, poles, f_range=None):
    """
    Compute useful frequency range
    
    Input arguments:
       zeros   : Vector of complex zeros
       poles   : Vector of complex poles
       f_range : Frequency range as tuple (f_min, f_max) in [Hz]
                 If f_range=None, the range is automatically selected (default) 
                 Otherwise, the provided range is used

    Output arguments:
       (f_min, f_max): Useful minimal and maximal frequency range in [Hz]
    """
    if f_range != None:
        if len(f_range) != 2:
            raise ValueError("Argument f_range must have two elements")
        if f_range[0] >= f_range[1]:
            raise ValueError("Argument f_range=(f_min,f_max) has f_min >= f_max")        
        return f_range
    
    # f_range == None: Determine frequency range from zeros and poles
    eps   = 1.0e-6       
    z_abs = abs(zeros)
    z_abs = z_abs[ z_abs > eps ]
    p_abs = abs(poles)
    p_abs = p_abs[ p_abs > eps ]
    if len(z_abs) > 0:
        if len(p_abs) > 0:
            w_min = max(eps, min(z_abs.min(), p_abs.min()))
            w_max = max(z_abs.max(), p_abs.max())
        else:
            w_min = max(eps, min(z_abs.min()))
            w_max = z_abs.max()
    else:
        if len(p_abs) > 0:
            w_min = max(eps, p_abs.min())
            w_max = p_abs.max()
        else:
            w_min = from_Hz(1.0)
            w_max = from_Hz(1.0)
                        
    f_min = to_Hz( w_min/10.0 )
    f_max = to_Hz( w_max*10.0 )

    return (f_min, f_max)


def normalizeIndices(nu, ny, u_indices=None, y_indices=None):
    """
    Normalize the indices
    """
    if u_indices == None:
        ui = range(0,nu)
    else:
        ui = u_indices
        
    if y_indices == None:
        yi = range(0,ny)
    else:
        yi = y_indices
    
    return (ui, yi)


def getFloatVector(A, Aname, copy=True):
    """
    Transform input argument to a 1-dim. numpy array
    
    Input arguments:
      A    : Scalar or vector like
      Aname: Name of A as string (used in error messages)
      copy : = True (default): A is always copied
             = False: If possible, A is not copied
      
    Output arguments:
      A2: One-dimensional numpy array of type float64
          If A is float  like, A2 is a numpy array [1]
          If A is vector like, A2 is a numpy array [:]
    """
    # Transform to float numpy array
    A2 = numpy.array(A,dtype=numpy.float64, copy=copy)
    
    # Reshape array if necessary
    s = A2.shape
    if len(s) == 0:
        # scalar
        A2 = numpy.array(A2,ndmin=1,copy=False)
    elif len(s) > 1:
        # more than 1 dimensions, error
        raise ValueError("Array {} has more than 1 dimension".format(Aname))
    return A2


def getFloatMatrix(A, Aname, copy=True):
    """
    Transform input argument to a 2-dim. numpy array
    
    Input arguments:
      A    : Scalar, vector or matrix like
      Aname: Name of A as string (used in error messages)
      copy : = True (default): A is always copied
             = False: If possible, A is not copied
      
    Output arguments:
      A2: Two-dimensional numpy array of type float64
          If A is float  like, A2 is a numpy array [1,1]
          If A is vector like, A2 is a numpy array [:,1] (column matrix)
          If A is matrix like, A2 is a numpy array of the same shape
    """
    # Transform to float numpy array
    A2 = numpy.array(A,dtype=numpy.float64, copy=copy)
    
    # Reshape array if necessary
    s = A2.shape
    if len(s) == 0:
        # scalar
        A2 = numpy.array(A2,ndmin=2,copy=False)
    elif len(s) == 1:
        # vector
        A2 = numpy.array(A2,ndmin=2,copy=False).T
    elif len(s) > 2:
        # more than 2 dimensions, error
        raise ValueError("Array {} has more than 2 dimensions".format(Aname))
    return A2    
    
    

        
if __name__ == "__main__":
    s = getFloatMatrix(2, "s")
    print("s = {}".format(s))
    v = getFloatMatrix([1,2,3], "v")
    print("v =\n{}".format(v))
    m = getFloatMatrix([[2,3],[4,5],[6,7]], "m")
    print("m =\n{}".format(m))
        