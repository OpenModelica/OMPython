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

import scipy.linalg
import numpy.linalg
import warnings
import ZerosAndPoles

class StateSpace:
    """
    State Space representation of a Linear Time Invariant (LTI) system

         der(x) = A*x + B*u
              y = C*x + D*u

    Attributes:
       A, B, C, D,

    Functions:
       __init__
       __str__
       eig
       zeros
       evaluate_at_s
       to_zpk
    """
    def __init__(self, A, B=None, C=None, D=None):
        """
        Initialize a StateSpace object

        Input arguments:
           A: A matrix with shape (nx,nx).
           B: B matrix with shape (nx,nu). If None, nu=0.
           C: C matrix with shape (ny,nx). If None, ny=0.
           D: D matrix with shape (ny,nu). If None, D is zero matrix.
        """
        # Define defaults for internal variables
        self.nu = 0  # number of inputs
        self.ny = 0  # number of outputs
        self.nx = 0  # number of states
        self.A  = None
        self.B  = None
        self.C  = None
        self.D  = None
        self.p  = None  # Eigenvalues of the system
        self.zpk = None # zpk matrix representation

        # Store and check A
        self.A = numpy.array(A, dtype=numpy.float64, ndmin=2)
        if len(self.A.shape) != 2:
            raise ValueError("A (shape=%s) must have 2 dimensions" % self.A.shape)
        self.nx = self.A.shape[0]
        if self.A.shape[1] != self.nx:
            raise ValueError("A must be square")

        # Store and check B
        if B != None:
            self.B = numpy.array(B, dtype=numpy.float64)
            if len(self.B.shape) < 1 or len(self.B.shape) > 2:
                raise ValueError("B (shape=%s) must have either 1 or 2 dimensions" % B.shape)
            if len(self.B.shape) == 1:
                self.B = numpy.transpose( numpy.array(self.B, dtype=numpy.float64, ndmin=2) )
            if self.B.shape[0] != self.nx:
                raise ValueError("B (shape=%s) must have the same row size as A (shape=%s)" % (self.B.shape, self.A.shape) )
            self.nu = self.B.shape[1]

        # Store and check C
        if C != None:
            self.C = numpy.array(C, dtype=numpy.float64, ndmin=2)
            if len(self.C.shape) > 2:
                raise ValueError("C (shape=%s) must have either 1 or 2 dimensions" % C.shape)
            if self.C.shape[1] != self.nx:
                raise ValueError("C must have the same column size as A")
            self.ny = self.C.shape[0]

        # Store and check D
        if D != None:
            self.D = numpy.array(D, dtype=numpy.float64, ndmin=2)
            if self.D.shape[0] != self.ny:
                raise ValueError("D must have the same row size as C")
            if self.D.shape[1] != self.nu:
                raise ValueError("D must have the same column size as B")
        else:
            if self.ny > 0 and self.nu > 0:
                self.D = numpy.zeros((self.ny, self.nu), order="F")


    def __str__(self):
        """
        String representation of a StateSpace object
        """
        s = "\n"
        # s += "nu = " + str(self.nu) + ", ny = " + str(self.ny) + ", nx = " + str(self.nx) + "\n"
        s += "  A =\n" + str(self.A) + "\n"
        s += "  B =\n" + str(self.B) + "\n"
        s += "  C =\n" + str(self.C) + "\n"
        s += "  D =\n" + str(self.D) + "\n"
        return s


    def eig(self, left=False, right=False):
        """
        Return the eigen values and optionally the left and/or right eigen vectors
        """
        if self.p == None and left==False and right==False:
            self.p = scipy.linalg.eig(self.A, left=left, right=right)
            return self.p
        else:
            return scipy.linalg.eig(self.A, left=left, right=right)


    def zeros_ij(self, ui=0, yj=0):
        """
        Return the invariant zeros from input u[ui] to output y[yj]
        """
        # Check the input arguments
        if ui < 0 or ui >= self.nu:
            raise ValueError("Argument ui (={}) must be in the range 0 <= ui < {}".format(ui, self.nu))
        if yj < 0 or yj >= self.ny:
            raise ValueError("Argument yj (={}) must be in the range 0 <= yj < {}".format(yj, self.ny))

        # The zeros of a SISO system are the generalized eigenvalues of
        #   |I 0|     | A  B|
        #   |   |*s - |     | = Bgen*s - Agen
        #   |0 0|     | C  D|
        Bgen = numpy.vstack( (numpy.hstack((numpy.eye(self.nx),numpy.zeros((self.nx,1)))),
                              numpy.zeros((1,self.nx+1)) ))
        Agen = numpy.vstack( (numpy.hstack((self.A, self.B[:,ui:ui+1])),
                              numpy.hstack((self.C[yj:yj+1,:], self.D[yj:yj+1,ui:ui+1])) ))

        # When calculating the zeros, a warning is printed for zeros at infinity
        # since a divison by zero occurs resulting in a zero of "nan+nanj".
        # The following context suppresses this warning
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            z = scipy.linalg.eigvals(Agen, Bgen)

        # Remove all zeros at infinity
        return z[ numpy.isfinite(z) ]


    def evaluate_at_s(self, s_k):
        """
        Evaluate a StateSpace system at a given float or complex number s_k

        The transfer function from the inputs u to the outputs y is
        (A, B, C, D are self.A,.B,.C.,D and I is the identity matrix):

            y(s) = (C*inv(s*I - A)*B + D)*u(s)

        Function "evaluate_at_s" returns

            K = C*inv(s_k*I - A)*B + D

        K is returned as a numpy (ny,nu) float or complex array
        (depending on whether s_k is float or complex)

        If the given s_k is an eigenvalue of A (or is close to such an eigenvalue),
        then the inverse does not exist, and there are either infinitely many or no
        solutions. In such a case an exception is raised.

        Algorithm:
           solve the linear system
               (s_k*I - A)*X = B

           for X and then compute
               K = C*X + D

           If s_k is float, a linear system with real coefficients is solved.
           If s_k is complex, a linear system with complex coefficients is solved.
        """
        if self.nu == 0 or self.ny == 0:
            raise ValueError("evaluate_at_s requires at least one input and one output of the StateSpace system\n" +
                             "but nu = %s, ny = %d" % (self.nu, self.ny))
        elif self.nx == 0:
            return self.D
        else:
            K = self.D + numpy.dot(self.C, numpy.linalg.solve(s_k*numpy.eye(self.nx) - self.A, self.B))
            return K


    def to_zpk(self):
        """
        Transform StateSpace object to a matrix of SISO ZerosAndPoles objects
        """
        # Check whether already computed
        if self.zpk != None: return self.zpk
        
        # Compute eigenvalues
        p = self.eig()
        
        # Generate a matrix of zpk systems with k=1 each
        ZPK = ZerosAndPoles.ZerosAndPolesSISO
        zpk = ZerosAndPoles.ZerosAndPoles( [[ZPK( (1.0, self.zeros_ij(i,j), p) ) 
                                             for i in xrange(0,self.nu)]
                                             for j in xrange(0,self.ny)] )
        
        # Select a real "s_k" that is neither an eigenvalue nor a zero.
        re_max = p.real.max()
        for i in xrange(0,self.nu):
            for j in xrange(0,self.ny):
                re_max = max( re_max, zpk[j,i].z.real.max() )
        s_k = max(0.0, re_max + 1.0)
        
        # Compute gains of zpk and of ss objects and fix gain of zpk objects
        K1 = self.evaluate_at_s(s_k)
        for i in xrange(0,self.nu):
            for j in xrange(0,self.ny):
                k2 = zpk[j,i].evaluate_at_s(s_k).real
                (zpk[j,i]).set_k( float(K1[j,i])/k2 )            
        self.zpk = zpk
        return zpk
        

if __name__ == "__main__":
    ss1 = StateSpace([[1,2],[3,4]], [1,3], [3,4], [4])
    print("ss1 =\n" + str(ss1))

    ss2 = StateSpace(A = [[1,2,3],[4,5,6],[7,8,9]],
                    B = [[11,12],[21,22],[31,32]],
                    C = [[11,12,13],[21,22,23],[31,32,33]])
    print("ss2 =\n" + str(ss2))

    # The data of a StateSpace object is defined as read-only
    nx1 = ss1.nx
    A   = ss1.A
    # ss1.nx = 3    # Raises an exceptions, since attribute is defined as read only


    print("\nCalculate eigen values and right eigen vectors:")
    ss3 = StateSpace([[1, 2, 3],
                      [4,-5,-6],
                      [7, 8, 5]])
    print("ss3.eig() = " + str(ss3.eig()))
    print("ss3.eig(right=True) = " + str(ss3.eig(right=True)))

    print("\nCalculate invariant zeros:")
    print("ss1.zeros_ij() = " + str(ss1.zeros_ij()))
    ss4 = StateSpace([[1, 2, 3],
                      [4,-5,-6],
                      [7, 8, 5]], B=numpy.ones((3,1)),C=numpy.ones((1,3)), D=[[0]])
    z = ss4.zeros_ij()
    print("ss4.zeros_ij() = " + str(z))

    # Check evaluate_at_s
    k = ss4.evaluate_at_s(4.0)
    print("ss4 = \n" + str(ss4))
    print("k = " + str(k))

    # Check transformation to zpk
    zpk4 = ss4.to_zpk()
    print("zpk4 =" + str(zpk4))
   
    # Check transformation to zpk
    zpk2 = ss2.to_zpk()
    print("zpk2 =" + str(zpk2))


