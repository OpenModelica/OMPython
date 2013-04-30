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

"""
     Algorithms for the signal processing plug-in
"""
import scipy.integrate
import scipy.interpolate
import math
import numpy
import numpy.fft

def arithmeticMean(t,y):
    """
    Compute arithmetic mean of time series y(t) with trapezoidal integration
    
    Inputs:
       t: Vector of time points
       y: Vector of signal values
    
    Outputs:
       result: Arithmetic mean of y (= Integral(y*dt)/(tEnd-tStart)) 
    """
    if y.size == 1:
        result = y[0]
    else:
        result = scipy.integrate.trapz(y,t)/(t[-1] - t[0])
    return result


def rectifiedMean(t,y):
    """
    Compute rectified mean of time series y(t) with trapezoidal integration
    
    Inputs:
       t: Vector of time points
       y: Vector of signal values
    
    Outputs:
       result: Rectified mean of y (= Integral(abs(y)*dt)/(tEnd-tStart)) 
    """
    if y.size == 1:
        result = abs(y[0])
    else:
        result = scipy.integrate.trapz(abs(y),t)/(t[-1] - t[0])
    return result


def rootMeanSquare(t,y):
    """
    Compute root mean square of time series y(t) with trapezoidal integration
    
    Inputs:
       t: Vector of time points
       y: Vector of signal values
    
    Outputs:
       result: Root mean square of y (= sqrt( Integral(y^2*dt)/(tEnd-tStart)) ) 
    """
    if y.size == 1:
        result = y[0]
    else:
        result = math.sqrt( scipy.integrate.trapz(y*y,t)/(t[-1] - t[0]) )
    return result


def fft(t,y,N):
    """
    Compute fft of time series y(t)
    
    Inputs:
       t: Vector of time points (need not to be equidistant)
       y: Vector of signal values
       N: Number of points of the FFT
          (most efficient for a multiple of the numbers 2,3,4,5) 
         
    Outputs:
       (f,A): Frequency f in [Hz] and amplitude A = A(f) in [unit of y]
              (f.size = A.size = N//2 + 1; mean value of y removed from A)
    """
    # Compute sample time Ts and sample frequency fs

    Ts = (t[-1] - t[0]) / (N-1)
    fs = 1.0/Ts
    
    # Compute number of frequency points nf and frequency f
    nf = N//2 + 1
    f  = (fs/N)*numpy.linspace(0,nf-1,nf)   # highest frequency f[-1] = fs/2
    print("T=" + str(t[-1]) + ", N="+str(N)+", Ts="+str(Ts)+", fs="+str(fs)+", nf="+str(nf))
   
    # Compute mean value yMean and subtract it from y
    yMean = arithmeticMean(t,y)
    yy    = y - yMean
    
    # Compute vectors te and ye, so that te consists of N equidistant time points
    # Here: simplest possibility by linear interpolation (would be better to use a low pass filter)
    fc = scipy.interpolate.interp1d(t, yy)
    te = t[0] + numpy.linspace(0,N-1,N)*Ts
    #set last value to exactly t to avoid extrapolation(some numerical issue):
    te[-1] = t[-1]
    ye = fc(te)
    
    # Compute normalized fft of real sequence ye
    #original: ye_fft = numpy.fft.rfft(ye) / nf
    ye_fft = numpy.fft.rfft(ye) / nf
    A      = abs(ye_fft)
    return (f,A)

if __name__ == "__main__":
    # Test fft
    f1 = 5.0      # Frequency of signal 1 in [Hz]
    A1 = 1.0      # Amplitude of signal 1
    f2 = 20.0     # Frequency of signal 2 in [Hz]
    A2 = 0.2      # Amplitude of signal 2
    N1 = 10       # Number of periods of f1
    T  = N1/f1    # Time range
    np = 10000    # Number of discretization points
    t  = numpy.linspace(0,T,num=np)    # Time points 0 ... T
    c1 = 2*numpy.pi*f1
    c2 = 2*numpy.pi*f2
    y  = A1*numpy.sin(c1*t) + A2*numpy.sin(c2*t)    
    
    # Plot time signals
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(t, y)
    plt.grid(True, which="both")
    plt.xlabel("time [s]")
    plt.ylabel("y(t)")    
    
    # Compute fft
    n = 2*N1*(f2//f1)
    n = 10*n
    n = 160
    k = f1*n*T/(n-1)   
    print("n=" + str(n) + ", k=" + str(k))    
    (f,A) = fft(t,y,n)
    
    # Determine distance df between two frequency points
    df = (f[-1] - f[0])/(len(f)-1)
    print("1/fmax = " + str(1/f[-1]) + ", len(f) = " + str(len(f))+
          ", T = " + str(T))
    wf = 0.8*df/2
    print("fmax = " + str(f[-1]) + ", df = " + str(df) + ", df2 = " + str(1/T))    
    print("nf = " + str(len(f)))
    plt.figure()
    #plt.plot(f,A)
    plt.bar(f-wf/2, A, width=wf)
    plt.grid(True, which="both")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Amplitude") 
    #plt.show()    
      
    # Second Test fft
    f1 = 10.0     # Frequency of signal 1 in [Hz]
    A1 = 10.0     # Amplitude of signal 1
    f2 = 30.0     # Frequency of signal 2 in [Hz]
    A2 = 20.0     # Amplitude of signal 2
    N1 = 10       # Number of periods of f1
    T  = N1/f1    # Time range
    np = 20000    # Number of discretization points
    t  = numpy.linspace(0,T,num=np)    # Time points 0 ... T
    c1 = 2*numpy.pi*f1
    c2 = 2*numpy.pi*f2
    y2 = 100 + A1*numpy.sin(c1*t) + A2*numpy.sin(c2*t)    
    
    # Plot time signals
    plt.figure()   
    plt.plot(t, y2)
    plt.grid(True, which="both")
    plt.xlabel("time [s]")
    plt.ylabel("y2(t)")    
    
    # Compute fft
    n = 10000
    (f,A) = fft(t,y2,n)
    
    # Plot fft
    df = (f[-1] - f[0])/(len(f)-1)
    wf = 0.8*df/2
    plt.figure()
    #plt.plot(f,A)
    plt.bar(f-wf/2, A, width=wf)
    plt.grid(True, which="both")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Amplitude") 
    plt.show()  
    
 