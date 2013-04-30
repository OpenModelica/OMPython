''' 
Copyright (C) 2011-2012 German Aerospace Center DLR
(Deutsches Zentrum fuer Luft- und Raumfahrt e.V.), 
Institute of System Dynamics and Control
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


import zipfile
import re
import ctypes
import tempfile
import platform
import numpy

import FMUError
from FMIDescription import FMIDescription


''' Declaration of file-type correspondents between Modelica/C and Python
    The mapping is done according to file: fmiModelTypes.h
'''
fmiFalse                 = '\x00'
fmiTrue                  = '\x01'
fmiReal                  = ctypes.c_double
fmiInteger               = ctypes.c_int
fmiBoolean               = ctypes.c_char
fmiString                = ctypes.c_char_p
fmiRealVector            = ctypes.POINTER(fmiReal)
fmiIntegerVector         = ctypes.POINTER(fmiInteger)
fmiBooleanVector         = ctypes.POINTER(fmiBoolean)
fmiStringVector          = ctypes.POINTER(fmiString)
fmiBooleanPtr            = ctypes.c_char_p
fmiComponent             = ctypes.c_void_p
fmiStatus                = ctypes.c_int
fmiValueReference        = ctypes.c_uint
fmiValueReferenceVector  = ctypes.POINTER(fmiValueReference)


def createfmiRealVector(n):
    return (numpy.ndarray(n, numpy.float))


def createfmiIntegerVector(n):
    return (numpy.ndarray(n, numpy.int))


def createfmiBooleanVector(n):
    return (numpy.ndarray(n, numpy.bool))


def createfmiStringVector(n):
    return (fmiString * n)()


def createfmiReferenceVector(n):
    return (numpy.ndarray(n, numpy.uint32))


class fmiEventInfo(ctypes.Structure):
    _fields_ = [('iterationConverged', fmiBoolean),
                ('stateValueReferencesChanged', fmiBoolean),
                ('stateValuesChanged', fmiBoolean),
                ('terminateSimulation', fmiBoolean),
                ('upcomingTimeEvent', fmiBoolean),
                ('nextEventTime', fmiReal)]
''' end of file-type correspondents '''


class FMUInterface:
    ''' This class encapsulates the FMU C-Interface
        all fmi* functions are a public interface to the FMU-functions
        not implemented: type checks and automatic conversions for fmi* functions
    '''
    def __init__(self, fileName, parent=None, loggingOn=True):
        ''' Load an FMU-File and start a new instance
            @param fileName: complete path and name of FMU-file (.fmu)
            @type fileName: string
        '''
        self._loggingOn = loggingOn

        ''' Open the given fmu-file (read only)'''
        try:
            self._file = zipfile.ZipFile(fileName,  'r')
        except BaseException as e:
            raise FMUError.FMUError('Error when reading zip-file.\n' + str(e) + '\n')

        ''' C requires the unique identification of every FMU instance. Python may just use class intances.
            Still the C functions require an ID. Python associates an ID with every instance of an object.
            We just use this ID for communication with the C-Functions.
        '''
        self.instanceID = str(id(self))
        self.log = []

        ''' Read FMI description file (directly from zip-file)'''
        try:
            xmlFileName = self._file.open('modelDescription.xml')
        except BaseException as e:
            raise FMUError.FMUError('Error when reading modelDescription.xml\n' + str(e) + '\n')
        self.description = FMIDescription(xmlFileName, self)

        ''' Just a little sanity check - standard definition says file name and FMU-name have to be the same '''
        if re.match(r'.*/(.*?).fmu$', fileName).group(1) != self.description.modelIdentifier:
            raise FMUError.FMUError('FMU file corrupted!\nFile name and model identifier differ: ' + re.match(r'.*/(.*?).fmu$', fileName).group(1) + ' vs. ' + self.description.modelIdentifier + '\n')

        self._InstantiateModel()
        self._createCInterface()

    def _assembleBinaryName(self, modelName):
        ''' Creates the path within the fmu-file for the binary according to current architecture
            @param modelName: name of model
        '''
        binaryName = 'binaries/'
        if platform.system() == 'Linux':
            binaryName += 'linux'
        elif platform.system() == 'Windows':
            binaryName += 'win'
        else:
            raise FMUError.FMUError('Unable to detect system architecture or architecture not supported.\n')
        if platform.architecture()[0] == '32bit':
            binaryName += '32/'
        elif platform.architecture()[0] == '64bit':
            binaryName += '64/'
        else:
            raise FMUError.FMUError('Unable to detect system architecture or architecture not supported.\n')
        binaryName += self.description.modelIdentifier
        if platform.system() == 'Linux':
            binaryName += '.so'
        elif platform.system() == 'Windows':
            binaryName += '.dll'
        return binaryName

    def _InstantiateModel(self):
        ''' unpacks the model binary and loads it into memory
        '''
        ''' create an temporary file (thereby file creation, deletion, access etc is handled automatically) and
            extracts the library from the .fmu-file there
        '''
        self._binaryName = self._assembleBinaryName(self.description.modelIdentifier)
        self._tmpfile = tempfile.NamedTemporaryFile(suffix='.dll' if platform.system() == 'Windows' else '.so', delete=False)
        try:
            binFile = self._file.read(self._binaryName)
        except BaseException as e:
            raise FMUError.FMUError("Error when reading binary file from FMU.\n" + str(e) + '\n')
        self._tmpfile.file.write(binFile)
        self._tmpfile.file.close()

        ''' C-interface for system functions '''
        Logger         = ctypes.CFUNCTYPE(None, fmiComponent, fmiString, fmiStatus, fmiString, fmiString)
        AllocateMemory = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint)
        FreeMemory     = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

        def _Logger(c, instanceName, status, category, message):
            if self._loggingOn:
                print(message)
            #self.log.append( (c, instanceName, status, category, message) )

        class _fmiCallbackFunctions(ctypes.Structure):
            _fields_ = [('logger', Logger), ('allocateMemory', AllocateMemory), ('freeMemory', FreeMemory)]
        ''' mapping of memory management functions for FMU to operating system functions, depending on OS.
            For Linux it refers to the std-C library - this should always be present
        '''
        if platform.system() == 'Linux':
            self._fmiCallbackFunctions = _fmiCallbackFunctions(
                                     logger=Logger(_Logger),
                                     allocateMemory=AllocateMemory(ctypes.cdll.LoadLibrary('libc.so.6').calloc),
                                     freeMemory=FreeMemory(ctypes.cdll.LoadLibrary('libc.so.6').free))
        elif platform.system() == 'Windows':
            self._fmiCallbackFunctions = _fmiCallbackFunctions(
                                     logger=Logger(_Logger),
                                     allocateMemory=AllocateMemory(ctypes.cdll.msvcrt.calloc),
                                     freeMemory=FreeMemory(ctypes.cdll.msvcrt.free))

        ''' Load instance of library into memory '''
        try:
            self._libraryHandle = ctypes.cdll.LoadLibrary(self._tmpfile.name)._handle
            self._library = ctypes.CDLL(self._tmpfile.name, handle=self._libraryHandle)
        except BaseException as e:
            raise FMUError.FMUError('Error when loading binary from FMU.\n' + str(e) + '\n')

        InstantiateModel = getattr(self._library, self.description.modelIdentifier + '_fmiInstantiateModel')
        InstantiateModel.argtypes = [fmiString, fmiString, _fmiCallbackFunctions, fmiBoolean]
        InstantiateModel.restype = fmiComponent
        self._modelInstancePtr = InstantiateModel(self.instanceID, self.description.guid, self._fmiCallbackFunctions, fmiTrue if self._loggingOn else fmiFalse)
        if self._modelInstancePtr == None:
            raise FMUError.FMUError('Instantiation of FMU failed.\n')

    def free(self):
        ''' Call FMU destructor before being destructed. Just cleaning up. '''
        if hasattr(self, '_library'):
            FreeModelInstance = getattr(self._library, self.description.modelIdentifier + '_fmiFreeModelInstance')
            FreeModelInstance.argtypes = [fmiComponent]
            FreeModelInstance.restype = None
            FreeModelInstance(self._modelInstancePtr)
            self._tmpfile.close()

    def _createCInterface(self):
        ''' Create interfaces to C-function calls.
            The functions are created locally, exposed by a public afterwards, to simplify later customizations
            for error handling etc.
            The mapping is done according to file: fmiModelFunctions.h
        '''
        self._fmiGetModelTypesPlatform = getattr(self._library, self.description.modelIdentifier + '_fmiGetModelTypesPlatform')
        self._fmiGetModelTypesPlatform.argtypes = None
        self._fmiGetModelTypesPlatform.restype = fmiString

        self._fmiGetVersion = getattr(self._library, self.description.modelIdentifier + '_fmiGetVersion')
        self._fmiGetVersion.argtypes = None
        self._fmiGetVersion.restype = fmiString

        self._fmiSetDebugLogging = getattr(self._library, self.description.modelIdentifier + '_fmiSetDebugLogging')
        self._fmiSetDebugLogging.argtypes = [fmiComponent, fmiBoolean]
        self._fmiSetDebugLogging.restype = fmiStatus

        self._fmiSetTime = getattr(self._library, self.description.modelIdentifier + '_fmiSetTime')
        self._fmiSetTime.argtypes = [fmiComponent, fmiReal]
        self._fmiSetTime.restype = fmiStatus

        self._fmiSetContinuousStates = getattr(self._library, self.description.modelIdentifier + '_fmiSetContinuousStates')
        self._fmiSetContinuousStates.argtypes = [fmiComponent, fmiRealVector, ctypes.c_uint]
        self._fmiSetContinuousStates.restype = fmiStatus

        self._fmiCompletedIntegratorStep = getattr(self._library, self.description.modelIdentifier + '_fmiCompletedIntegratorStep')
        self._fmiCompletedIntegratorStep.argtypes = [fmiComponent, fmiBooleanPtr]
        self._fmiCompletedIntegratorStep.restype = fmiStatus

        self._fmiSetReal = getattr(self._library, self.description.modelIdentifier + '_fmiSetReal')
        self._fmiSetReal.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_uint, fmiRealVector]
        self._fmiSetReal.restype = fmiStatus

        self._fmiSetInteger = getattr(self._library, self.description.modelIdentifier + '_fmiSetInteger')
        self._fmiSetInteger.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_uint, fmiIntegerVector]
        self._fmiSetInteger.restype = fmiStatus

        self._fmiSetBoolean = getattr(self._library, self.description.modelIdentifier + '_fmiSetBoolean')
        self._fmiSetBoolean.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_uint, fmiBooleanVector]
        self._fmiSetBoolean.restype = fmiStatus

        self._fmiSetString = getattr(self._library, self.description.modelIdentifier + '_fmiSetString')
        self._fmiSetString.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_uint, fmiStringVector]
        self._fmiSetString.restype = fmiStatus

        self._fmiInitialize = getattr(self._library, self.description.modelIdentifier + '_fmiInitialize')
        self._fmiInitialize.argtypes = [fmiComponent, fmiBoolean, fmiReal, ctypes.POINTER(fmiEventInfo)]
        self._fmiInitialize.restype = fmiStatus

        self._fmiGetDerivatives = getattr(self._library, self.description.modelIdentifier + '_fmiGetDerivatives')
        self._fmiGetDerivatives.argtypes = [fmiComponent, fmiRealVector, ctypes.c_uint]
        self._fmiGetDerivatives.restype = fmiStatus

        self._fmiGetEventIndicators = getattr(self._library, self.description.modelIdentifier + '_fmiGetEventIndicators')
        self._fmiGetEventIndicators.argtypes = [fmiComponent, fmiRealVector, ctypes.c_uint]
        self._fmiGetEventIndicators.restype = fmiStatus

        self._fmiGetReal = getattr(self._library, self.description.modelIdentifier + '_fmiGetReal')
        self._fmiGetReal.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_uint, fmiRealVector]
        self._fmiGetReal.restype = fmiStatus

        self._fmiGetInteger = getattr(self._library, self.description.modelIdentifier + '_fmiGetInteger')
        self._fmiGetInteger.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_uint, fmiIntegerVector]
        self._fmiGetInteger.restype = fmiStatus

        self._fmiGetBoolean = getattr(self._library, self.description.modelIdentifier + '_fmiGetBoolean')
        self._fmiGetBoolean.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_uint, fmiBooleanVector]
        self._fmiGetBoolean.restype = fmiStatus

        self._fmiGetString = getattr(self._library, self.description.modelIdentifier + '_fmiGetString')
        self._fmiGetString.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_uint, fmiStringVector]
        self._fmiGetString.restype = fmiStatus

        self._fmiEventUpdate = getattr(self._library, self.description.modelIdentifier + '_fmiEventUpdate')
        self._fmiEventUpdate.argtypes = [fmiComponent, fmiBoolean, ctypes.POINTER(fmiEventInfo)]
        self._fmiEventUpdate.restype = fmiStatus

        self._fmiGetContinuousStates = getattr(self._library, self.description.modelIdentifier + '_fmiGetContinuousStates')
        self._fmiGetContinuousStates.argtypes = [fmiComponent, fmiRealVector, ctypes.c_uint]
        self._fmiGetContinuousStates.restype = fmiStatus

        self._fmiGetNominalContinuousStates = getattr(self._library, self.description.modelIdentifier + '_fmiGetNominalContinuousStates')
        self._fmiGetNominalContinuousStates.argtypes = [fmiComponent, fmiRealVector, ctypes.c_uint]
        self._fmiGetNominalContinuousStates.restype = fmiStatus

        self._fmiGetStateValueReferences = getattr(self._library, self.description.modelIdentifier + '_fmiGetStateValueReferences')
        self._fmiGetStateValueReferences.argtypes = [fmiComponent, fmiValueReferenceVector, ctypes.c_uint]
        self._fmiGetStateValueReferences.restype = fmiStatus

        self._fmiTerminate = getattr(self._library, self.description.modelIdentifier + '_fmiTerminate')
        self._fmiTerminate.argtypes = [fmiComponent]
        self._fmiTerminate.restype = fmiStatus

    def fmiGetModelTypesPlatform(self):
        return self._fmiGetModelTypesPlatform(self._modelInstancePtr)

    def fmiGetVersion(self):
        return self._fmiGetVersion(self._modelInstancePtr)

    def fmiSetDebugLogging(self, onOff):
        return self._fmiSetDebugLogging(self._modelInstancePtr, fmiTrue if onOff else fmiFalse)

    def fmiSetTime(self, time):
        return self._fmiSetTime(self._modelInstancePtr, time)

    def fmiSetContinuousStates(self, vector):
        if len(vector) != self.description.numberOfContinuousStates:
            raise IndexError('length of vector not corresponding to length  of models continuous states vector')
        return self._fmiSetContinuousStates(self._modelInstancePtr, vector.ctypes.data_as(fmiRealVector), len(vector))

    def fmiCompletedIntegratorStep(self):
        callEventUpdate = fmiBoolean()
        self._fmiCompletedIntegratorStep(self._modelInstancePtr, ctypes.byref(callEventUpdate))
        return callEventUpdate

    def fmiSetReal(self, valueReference, value):
        if len(valueReference) != len(value):
            raise IndexError('length of valueReference not corresponding to length of value')
        return self._fmiSetReal(self._modelInstancePtr, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiRealVector))

    def fmiSetInteger(self, valueReference, value):
        if len(valueReference) != len(value):
            raise IndexError('length of valueReference not corresponding to length of value')
        return self._fmiSetInteger(self._modelInstancePtr, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiIntegerVector))

    def fmiSetBoolean(self, valueReference, value):
        if len(valueReference) != len(value):
            raise IndexError('length of valueReference not corresponding to length of value')
        return self._fmiSetBoolean(self._modelInstancePtr, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiBooleanVector))

    def fmiSetString(self, valueReference, value):
        if len(valueReference) != len(value):
            raise IndexError('length of valueReference not corresponding to length of value')
        return self._fmiSetString(self._modelInstancePtr, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiStringVector))

    def fmiInitialize(self, toleranceControlled=False, relativeTolerance=0):
        eventInfo = fmiEventInfo()
        status = self._fmiInitialize(self._modelInstancePtr, fmiTrue if toleranceControlled else fmiFalse, relativeTolerance, eventInfo)
        return (eventInfo, status)

    def fmiGetDerivatives(self):
        ret = createfmiRealVector(self.description.numberOfContinuousStates)
        self._fmiGetDerivatives(self._modelInstancePtr, ret.ctypes.data_as(fmiRealVector), self.description.numberOfContinuousStates)
        return ret

    def fmiGetEventIndicators(self):
        ret = createfmiRealVector(self.description.numberOfEventIndicators)
        self._fmiGetEventIndicators(self._modelInstancePtr, ret.ctypes.data_as(fmiRealVector), self.description.numberOfEventIndicators)
        return ret

    def fmiGetReal(self, valueReference):
        value = createfmiRealVector(len(valueReference))
        self._fmiGetReal(self._modelInstancePtr, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiRealVector))
        return value

    def fmiGetInteger(self, valueReference):
        value = createfmiIntegerVector(len(valueReference))
        self._fmiGetInteger(self._modelInstancePtr, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiIntegerVector))
        return value

    def fmiGetBoolean(self, valueReference):
        value = createfmiBooleanVector(len(valueReference))
        self._fmiGetBoolean(self._modelInstancePtr, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value.ctypes.data_as(fmiBooleanVector))
        return value

    def fmiGetString(self, valueReference):
        value = createfmiStringVector(len(valueReference))
        self._fmiGetString(self._modelInstancePtr, valueReference.ctypes.data_as(fmiValueReferenceVector), len(valueReference), value)
        return value

    def fmiEventUpdate(self, intermediateResults=False):
        eventInfo = fmiEventInfo()
        self._fmiEventUpdate(self._modelInstancePtr, fmiTrue if intermediateResults else fmiFalse, eventInfo)
        return eventInfo

    def fmiGetContinuousStates(self):
        value = createfmiRealVector(self.description.numberOfContinuousStates)
        self._fmiGetContinuousStates(self._modelInstancePtr, value.ctypes.data_as(fmiRealVector), self.description.numberOfContinuousStates)
        return value

    def fmiGetNominalContinuousStates(self):
        value = createfmiRealVector(self.description.numberOfContinuousStates)
        self._fmiGetNominalContinuousStates(self._modelInstancePtr, value.ctypes.data_as(fmiRealVector), self.description.numberOfContinuousStates)
        return value

    def fmiGetStateValueReferences(self):
        value = createfmiReferenceVector(self.description.numberOfContinuousStates)
        self._fmiGetStateValueReferences(self._modelInstancePtr, value.ctypes.data_as(fmiValueReferenceVector), self.description.numberOfContinuousStates)
        return value

    def fmiTerminate(self):
        self._fmiTerminate(self._modelInstancePtr)

'''
if __name__ == '__main__':
    fmui = FMUInterface('./Capacitor.fmu')
    print fmui.description.scalarVariables['der(u)'].type
    print fmui.fmiInitialize(fmiTrue, 0.1)

    print fmui.fmiGetDerivatives()
'''
