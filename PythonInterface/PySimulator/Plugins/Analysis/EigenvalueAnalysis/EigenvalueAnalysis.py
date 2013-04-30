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
Contact: Stefan Hartweg (stefan.hartweg@dlr.de)

This Plugin adds functionality to the simulator by providing functions for both calculation
of eigenvalues, frequencies, damping ... as well as a visualization of these.    
Uses the LinearSystemAnalysis Plugin!
     
'''
from Plugins.Analysis import LinearSystemAnalysis
from Plugins.Analysis.EigenvalueAnalysis.scatterInspector import \
    myScatterInspectorOverlay
from Plugins.Analysis.LinearSystemAnalysis.LinearSystemAnalysis import \
    linearizeAndShowABCD
from PySide import QtGui, QtCore
from chaco.api import add_default_axes, add_default_grids
from chaco.array_plot_data import ArrayPlotData
from chaco.axis import PlotAxis
from chaco.data_label import DataLabel
from chaco.plot import Plot
from chaco.scatter_inspector_overlay import ScatterInspectorOverlay
from chaco.tools.api import ZoomTool
from chaco.tools.data_label_tool import DataLabelTool
from chaco.tools.image_inspector_tool import ImageInspectorOverlay, \
    ImageInspectorTool
from chaco.tools.pan_tool import \
    PanTool # there is some bug in in the default Pantools handling of the event "left_up"...
from chaco.tools.scatter_inspector import ScatterInspector
from chaco.tools.select_tool import SelectTool

from numpy import linspace, sin, random
from numpy.core.function_base import linspace
from numpy.ma.core import abs
from traits.api import Any, Bool, Int, Float, Str, Range, Button, HasTraits, \
    DelegatesTo, Instance, Enum, Event, Trait, Tuple, Callable, List, \
    on_trait_change
import IntegratorControl
import Plugins.Analysis.LinearSystemAnalysis as LinearSystemAnalysis
import PySimulator
import h5py
import numpy
import numpy
import numpy as np
import os
import os
import threading
import types


def getModelCallbacks():
    ''' Registers model callbacks with main application
        return a list of lists, one list for each callback, each sublist
        containing a name for the function and a function pointer
    '''
    return [["Plot Eigenvalues", plotEigenvalues],["Animate Eigenvectors/States", animateEigenvectors]]


def plotEigenvalues(model):
    ''' This function calculates the linearization of model as well as additional information
        (eigenvalues, damping ...) if this was not done before.
        It opens a new plotting tab and displays this information
    '''
    #Check if already linearized, do so otherwise:
    try:
        data = model.pluginData["EigenvalueAnalysis"]
    except:
        print "Performing linearization"
        data = EigenvalueAnalysis()        
        data._performLinearization(model)
        model.pluginData["EigenvalueAnalysis"] = data        


    #Open new plotting tab:
    parent = QtGui.QApplication.activeWindow()
    widgetContainer = parent._newPlotContainer()
    widget = widgetContainer.activeWidget

    #Plot the data:
    x = numpy.real(data.eigenvalues[:])
    y = numpy.imag(data.eigenvalues[:])
    plotdata = ArrayPlotData(x = x, y = y, border_visible=True, overlay_border=True)
    plot = Plot(plotdata, title="Eigenvalues of %s" % data.modelName)
    scatter = plot.plot(("x", "y"), type="scatter", color="blue")[0]

    # Attach some tools to the plot
    plot.tools.append(PanTool(plot))
    plot.overlays.append(ZoomTool(plot))
    
    #Add axis titles:
    x_axis = PlotAxis(orientation="bottom")
    x_axis.mapper = plot.index_mapper
    x_axis.title = "real part"
    plot.underlays.append(x_axis)
    y_axis = PlotAxis(orientation="left")
    y_axis.mapper = plot.value_mapper
    y_axis.title = "imag. part"
    plot.underlays.append(y_axis)    

    # Attach the inspector and its overlay
    scatter.tools.append(ScatterInspector(scatter))
    overlay = myScatterInspectorOverlay(scatter,
                    hover_color="red",
                    hover_marker_size=6,
                    selection_marker_size=6,
                    selection_color="yellow",
                    selection_outline_color="purple",
                    selection_line_width=3,
                    stateNames = data.StateNames,
                    eigenVectors = data.eigenvectors,
                    frequencies = data.frequencies,
                    damping = data.damping,
                    observability = data.observability,
                    controllability = data.controllability  )
    scatter.overlays.append(overlay)
    #Activate Plot:
    widget.setPlot(plot)
    widgetContainer.activeWidget = widget  
    pass



def animateEigenvectors(model):
    ''' This function calculates the linearization of model as well as additional information
        (eigenvalues, damping ...) if this was not done before.
        It then opens a SimVis window with the model's animation and a gui to control the animation.
    '''    
    #Check if already linearized, do so otherwise:
    try:
        data = model.pluginData["EigenvalueAnalysis"]
    except:
        print "Performing linearization"
        data = EigenvalueAnalysis()        
        data._performLinearization(model)
        model.pluginData["EigenvalueAnalysis"] = data  
            
    model.interface.fmiTerminate()
    #Get state names:
    StateNames = data.StateNames #model.getStateNames()
    #open animation window:
    parent = QtGui.QApplication.activeWindow()
    animation = evAnimationControl(parent,  data) #self.QMainWindow
    animation.show()       
    animation.simulate(model)
    
       
        
class EigenvalueAnalysis(object):
    '''
    This class calls the linearization routine from the LinearSystemAnalysis plugin and 
    performs additional calculation, see the _performLinearization method
    Use it by 
        data = EigenvalueAnalysis()        
        data._performLinearization(model)
    '''
    def __init__(self):
        self.x0 = numpy.empty(0)
        self.n = 0
        self.J = numpy.empty((0,0))
        self.eigenvalues = numpy.empty(0)
        self.eigenvectors= numpy.empty((0,0))
        self.StateNames = {}
        
    
    
    def _performLinearization (self, model):    
        '''Performs simulation and stores results.
        '''
        
        parent = QtGui.QApplication.activeWindow()
        self.modelName = str(parent.nvb.currentModelItem.text(0)) #str convert QString to str
        self.model = parent.models[self.modelName]
        
        self.t = 0
        model.initialize(self.t, 1e-4) 
        self.x0 = numpy.array(model.interface.fmiGetContinuousStates())
        self.n = numpy.size(self.x0, 0)
        self.StateNames = model.getStateNames()
           
        #Use on of this possibilies to obtain the linear system A,B,C,D
        
        '''
        #Version 1: Load linearized system from file:
        import scipy.io
        mat = scipy.io.loadmat('D:\\hart_st\\rm-software\\fmuEnvironment\\trunk\\fmuEnvironment\\PySimulatorDevelopment\\PySimulator\\Examples\\neueModelle\\dslin.mat')
        nx = mat['nx'][0]
        ABCD = mat['ABCD']               
        A = ABCD[0:nx,0:nx]
        self.J = A
        B = ABCD[0:nx,nx+1:-1]
        C = ABCD[nx+1:-1,0:nx]
        D = ABCD[nx+1:-1,nx+1:-1]        
        '''
        
        #Version 1: Linearized system by the linear system analysis plugin
        linearizeAndShowABCD(model)
        self.J = model.pluginData["LinearSystemAnalysis"].A
        #Original:
        A = model.pluginData["LinearSystemAnalysis"].A 
        B = model.pluginData["LinearSystemAnalysis"].B
        C = model.pluginData["LinearSystemAnalysis"].C 
        D = model.pluginData["LinearSystemAnalysis"].D
        
        
        
        
                          
        print "Linearization: Calculate eigenvalues"
        if self.J.shape[0] > 1:
            Diag, V = numpy.linalg.eig(self.J)
        else:
            Diag = self.J
            V = 1
        
        self.eigenvalues = numpy.array(Diag)
        self.eigenvectors = numpy.array(V)  
        
        #Calculate additional information
        x = numpy.real(self.eigenvalues[:])
        y = numpy.imag(self.eigenvalues[:])     
   
        self.frequencies = numpy.abs(y) / (2*numpy.pi)
        self.damping = numpy.zeros(self.n)
        self.observability = numpy.zeros(self.n) == numpy.ones(self.n)  #init with false
        self.controllability = numpy.zeros(self.n) == numpy.ones(self.n)
        for i in range(len(self.eigenvalues)):
            if abs(y[i])>1e-8:
                self.damping[i] = -x[i]/abs(y[i])/ numpy.sqrt(1 + abs(x[i]/y[i]))
            else:
                self.damping[i] = -x[i]
        
            #Checking observability:
            if C.size == 0:
                self.observability[i] = False
            else:
                if np.linalg.matrix_rank( np.vstack((self.eigenvalues[i]*np.identity(self.n) - A, C))) == self.n:
                    self.observability[i] = True
                    
            #Checking controllability:
            if B.size == 0:
                self.controllability[i] = False
            else:            
                if np.linalg.matrix_rank( np.hstack((self.eigenvalues[i]*np.identity(self.n) - A, B))) == self.n:
                    self.controllability[i] = True               
        print "Linearization: Finished"

class evAnimationControl(QtGui.QDialog):
        '''An additional gui window which has elements to control the eigenvector animation.
        Used by function animateEigenvectors'''
    
        def __init__(self, parent = None, data = None):
            
            self.model = data.model
            self.data = data #EigenvalueAnalysis.EigenvalueAnalysis object which holds all information
            
            #Calculate additional information
            x= numpy.real(self.data.eigenvalues[:])
            y= numpy.imag(self.data.eigenvalues[:])            
            self.damping = self.data.damping# numpy.array(-x/abs(y)/ numpy.sqrt(1 + abs(x/y)))
            self.frequency = self.data.frequencies #numpy.array(abs(y) / (2*numpy.pi))
                        
            QtGui.QDialog.__init__(self, parent)
            _mainGrid = QtGui.QGridLayout(self)
            
            #Block 1 - Animation
            _aniControl= QtGui.QGroupBox("Animation Control", self)
            _mainGrid.addWidget(_aniControl, 1, 0)
            _aniControlLayout = QtGui.QGridLayout(self) #Fehlermeldung!
            _aniControl.setLayout(_aniControlLayout)
            self.animateEigenvectors = QtGui.QRadioButton("Animate Modes", self)
            self.animateEigenvectors.setChecked(True)
            self.animateStates = QtGui.QRadioButton("Animate states      ", self)
            self.lastEigenvector = QtGui.QPushButton('<')
            self.eigenvectorNumber = QtGui.QLabel("1", self)
            self.maxEigenvectorNumber = QtGui.QLabel("of "+'%.2s'%self.data.n, self)    #QString.number(EV.n)        
            self.nextEigenvector = QtGui.QPushButton('>')                 
            self.stopSimulate = QtGui.QPushButton('Stop')            
            _aniControlLayout.addWidget(self.animateEigenvectors, 0, 0)
            _aniControlLayout.addWidget(self.animateStates, 0, 3)
            _aniControlLayout.addWidget(self.lastEigenvector, 1, 0)
            _aniControlLayout.addWidget(self.eigenvectorNumber, 1, 1)          
            _aniControlLayout.addWidget(self.maxEigenvectorNumber, 1, 2)  
            _aniControlLayout.addWidget(self.nextEigenvector, 1, 3)           
            #_aniControlLayout.addWidget(self.stopSimulate, 2, 0, Qt.Qt.AlignHCenter, 4)
            _aniControlLayout.addWidget(self.stopSimulate, 2, 0)

            #Block 2 - Scaling          
            _scalingGroupBox = QtGui.QGroupBox("Scaling", self)
            _mainGrid.addWidget(_scalingGroupBox, 2, 0)
            _scalingGroupBoxLayout = QtGui.QGridLayout()
            _scalingGroupBox.setLayout(_scalingGroupBoxLayout)      
                
            self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, parent)
            self.slider.setRange(0, 40)#, 0.01         
            self.slider.setSingleStep(0.01)
            self.slider.setPageStep(10 * 0.01)
            self.slider.setTickInterval( 0.01)
            self.slider.setTickPosition(QtGui.QSlider.TicksRight)  
            self.slider.setValue(self.slider.maximum()*1.0/2)
            self.sliderLabel = QtGui.QLabel('1', self)
            _scalingGroupBoxLayout.addWidget(self.slider, 0, 0)
            _scalingGroupBoxLayout.addWidget(self.sliderLabel, 1, 0, QtCore.Qt.AlignHCenter) 
        
            #Block 3 - Feedback:
            _feedback = QtGui.QGroupBox("Eigenvalue/state information", self)
            _mainGrid.addWidget(_feedback, 3, 0)
            _feedbackLayout = QtGui.QGridLayout()
            _feedback.setLayout(_feedbackLayout)

            self.frequencyLabel = QtGui.QLabel("frequency:" + str( self.frequency[0]) + " Hz", self) 
            self.dampingLabel = QtGui.QLabel("damping:" + str( self.damping[0]) + " (Lehr)", self)      
            _feedbackLayout.addWidget(self.frequencyLabel, 0, 0)
            _feedbackLayout.addWidget(self.dampingLabel, 1, 0)            
     
            #Connect gui elements with functions
            self.lastEigenvector.clicked.connect(self._lastEigenvector)    
            self.nextEigenvector.clicked.connect(self._nextEigenvector)           
            self.stopSimulate.clicked.connect(self._stopSimulate)  
            self.slider.setTracking(True)
            self.slider.valueChanged.connect(self.setSliderLabel)#[double].
            #self.slider.connect(self.slider, Qt.SIGNAL('valueChanged(double)'), self.setSliderLabel)
            self.animateStates.toggled.connect(self.setSimulateStates)#self.animateStates.connect(self.animateStates, Qt.SIGNAL('toggled(bool)'), self.setSimulateStates)
            #self.animateEigenvectors.connect(self.animateEigenvectors, Qt.SIGNAL('toggled(bool)'), self.setSimulateStates)
             

             
        def setSliderLabel(self, value):
            '''Calculates a return value from the slider value(which ranges from 0 to 4)'''
            value  = 10.0**(value*1.0/10 - 2)
            self.sliderLabel.setText('%.4s' % value)
            self.simThread.guiScaling = value
            
        def setSimulateStates(self, value):
            '''The radio button simulateStates was checked/unchecked, so change feedback'''
            self.simThread.animateStates = self.animateStates.isChecked()
            #refresh additional output:
            self._actualizeFeedback()  
                       
        def _lastEigenvector(self):    
            '''if the "<" button was pressed, change self.simThread.eigenVectorNr and feedback'''
            eigenVectorNr = self.eigenvectorNumber.text()
            intNr = int(eigenVectorNr)#.toInt()               
            if intNr > 1:
                newIdx = intNr-1                    
                self.eigenvectorNumber.setNum(newIdx)      
                self.simThread.eigenVectorNr = intNr-1     
                #refresh additional output:                
                self._actualizeFeedback()                

        def _nextEigenvector(self):    
            '''if the ">" button was pressed, change self.simThread.eigenVectorNr and feedback'''
            eigenVectorNr = self.eigenvectorNumber.text()
            #intNr = eigenVectorNr.toInt()      
            intNr = int(eigenVectorNr)
            if intNr < self.data.n:
                newIdx = intNr+1                      
                self.eigenvectorNumber.setNum(newIdx)
                self.simThread.eigenVectorNr = intNr+1
                self._actualizeFeedback()  
         
         
        def _actualizeFeedback(self):
            '''Fills the feedback labels with information'''      
            eigenVectorNr = self.eigenvectorNumber.text()
            intNr = int(eigenVectorNr)#.toInt()   
            if not self.animateStates.isChecked():
                self.frequencyLabel.setText("frequency:" + str(self.frequency[intNr-1]) + " Hz")                
                if self.damping[intNr-1]>0:                 
                    self.dampingLabel.setText("damping:" + str(self.damping[intNr-1])+ " ")
                else:
                    self.dampingLabel.setText("exitation:" + str(-self.damping[intNr-1]) + " ")                                    
            else:
                self.frequencyLabel.setText("Shown state is:")    
                self.dampingLabel.setText( self.data.StateNames[intNr-1])
              
                    
        def simulate(self, model ):    
            '''Start a new simulation thread'''
            self.simThread = simulationThread() 
            self.simThread.stopRequest = False   
            self.simThread.closeGui = self._stopSimulate      
            self.simThread.x0 = self.data.x0     
            self.simThread.model = model 
            self.simThread.eigenvectors = self.data.eigenvectors 
            self.simThread.eigenVectorNr = 1 #the vector which is plotted                    s
            self.simThread.start()
            
        def _stopSimulate(self ):                  
            self.simThread.stopRequest = True    
            self.close()  


class simulationThread(threading.Thread):
        '''This class shows an specific eigenvector or state by manipulating a model's states
            Needs x0, model, eigenvectors, eigenVectorNr(starting with 1), guiScaling as parameters before calling run()
        '''
        
        guiScaling = 1 #is changed by the gui
        animateStates = False #is changed by the gui
                          
        def run(self):  #, x0, model
            import time
            
            x0 = self.x0
            steadyState = self.x0
            model = self.model

            model.interface.fmiSetTime(0) # fmiSetTime(t)
            model._setDefaultStartValues()

            try:
                #Alternative: Set VisUpdateInterval to 1e-8 if time events are happening:
                #model.setValue("updateVisualization.VisUpdateInterval",0.01*1e-6)      
                model.setValue("updateVisualization.VisUpdateInterval",1)     
                #Open a new simulation window       
                model.setValue("updateVisualization.tcpPort", 12345)
            except (KeyError):
                print 'Animation of eigenvectors needs DLR Simvis software! \n\
                        The model however was not exported with ModelicaServices.target = DymolaAndDLRVisualization\n\
                        or the Visualization.updateVisualization object was not at the top-level of the model.\n\
                        Re-export your model with this settings.'
                self.stopRequest = True
                self.closeGui() #Close the evAnimationControl
                pass
                
            model.interface.fmiInitialize('\x01', 1e-4)   #'\x01'=FMITRue
            
            startTime = time.time()
            
            animationCounter = 0
            while not self.stopRequest:
                x=numpy.zeros(2)
                #scaling factor for the eigenvector so that the maximum entry is 1
                scaling = numpy.max(abs(numpy.real(self.eigenvectors[:,self.eigenVectorNr-1])) , 0)
                if not self.animateStates:
                    x = x0 + self.guiScaling * 1/scaling * numpy.real(self.eigenvectors[:,self.eigenVectorNr-1]) * numpy.sin(6.2832*time.time())
                else:
                    x = x0.copy()
                    #x[self.eigenVectorNr-1] =x[self.eigenVectorNr-1] + self.guiScaling * numpy.sin(6.2832 *time.time())
                    x[self.eigenVectorNr-1] = 0*x[self.eigenVectorNr-1] + self.guiScaling
                
                model.interface.fmiSetContinuousStates(x)
                model.interface.fmiEventUpdate()
                #advance time to get some output in SimVis
                model.interface.fmiSetTime(animationCounter)#((time.time()-startTime) + 1)#(animationCounter * 1e-6 )
                time.sleep(0.1) #Let the animation have time to calculate    
                animationCounter = animationCounter+1        

            model.interface.fmiTerminate()    
