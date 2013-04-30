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


import numpy
'''
import matplotlib
import matplotlib.pyplot as plt
'''
from chaco.array_plot_data import ArrayPlotData
from chaco.axis import PlotAxis
from chaco.data_label import DataLabel
from chaco.plot import Plot
from chaco.tools.api import ZoomTool
from chaco.tools.data_label_tool import DataLabelTool
from chaco.tools.pan_tool import \
    PanTool # there is some bug in in the default Pantools handling of the event "left_up"...


def printData2(widget):
    ''' Example callback function for plot specific actions
        showing how to access data elements
    '''
    for x in widget.plot.data.list_data():
        print "Data entries: ", x, " of type: ", type(widget.plot.data.get_data(x)), " data: ", widget.plot.data.get_data(x)


def plotMin(widget):
    """ Determine minimum of signals in selected widget """
    print widget
    print("plotMin")


def plotMax(widget):
    """ Determine maximum of signals in selected widget"""
    print("plotMax")


def plotArithmeticMean(widget):
    """ Determine arithmetic mean of signals in selected widget """
    print("plotArithmeticMean")


def plotRectifiedMean(widget):
    """ Determine rectified mean of signals in selected widget """
    print("plotRectifiedMean")


def plotRootMeanSquare(widget):
    """ Determine root mean square of signals in selected widget """
    print("plotRootMeanSquare")


def plotFFT(widget):
    """ Determine fft of signals in selected widget """
    print("plotFFT")
    
    model = ""
    for (modelNumber, modelName, variableName), data in widget.getData():
        # print "var:", var, "data: ", data
        minVal = (0, float("inf"))
        maxVal = (0, float("-inf"))
        #for time, value in data:

    #Get data from data array:
    time = numpy.array(list((x for x, _ in data))) #data[0]
    values = numpy.array(list((x for _ , x in data)))
    
    (Tmin, Tmax, N) = getFFTtimeRange(time)
    (timeInRange, valuesInRange) = getValuesInRange(time, values, Tmin, Tmax)
    
    # Compute fft: A=A(f)
    import Algorithms
    (f,A) = Algorithms.fft(timeInRange, valuesInRange, N)


    #Open new plot tab:
    import plotWidget
    window = widget.createNewWindow()
    container = plotWidget.plotContainer(window)
    plotWidget = plotWidget.PlotWidget(container)
    container.setPlotWidget(plotWidget)

    # Create the plot
    plotdata = ArrayPlotData(x = f, y = A, border_visible=True, overlay_border=True)
    plot = Plot(plotdata, title="FFT")  #Plot(plotdata, title="FFT")
    barPlot = plot.plot(("x", "y"), type="bar",bar_width=0.1, color="blue")[0]   
    #scatterPlot = plot.plot(("x", "y"), type="scatter", color="blue")[0]  
    
    # Attach some tools to the plot
    plot.tools.append(PanTool(plot))
    plot.overlays.append(ZoomTool(plot))  
       
    #Activate Plot:
    plotWidget.setPlot(plot)   
    container.setPlotWidget(plotWidget)       

    layout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
    layout.addWidget(container)
    window.setLayout(layout)
    window.show()
    
def plotFFTPlusTHD(widget):
    """ Determine fft of signals in selected widget and 
        calculate Total harmonic disturbance"""
    print("plotFFT and Total Harmonic Disturbance")
    
    model = ""
    for (modelNumber, modelName, variableName), data in widget.getData():
        # print "var:", var, "data: ", data
        minVal = (0, float("inf"))
        maxVal = (0, float("-inf"))
        #for time, value in data:

    #Get data from data array:
    time = numpy.array(list((x for x, _ in data))) #data[0]
    values = numpy.array(list((x for _ , x in data)))
    unit = ""
    
    (Tmin, Tmax, N) = getFFTtimeRange(time)
    (timeInRange, valuesInRange) = getValuesInRange(time, values, Tmin, Tmax)
    
    # Compute fft: A=A(f)
    import Algorithms
    (f,A) = Algorithms.fft(timeInRange, valuesInRange, N)
   
   
   
   
   
    #******* START THD CALCULATION    *************
    #Estimate fundamental frequency:
    maxindex = A.argmax()
    estimation = f[maxindex]
    
    def getExFreq(estimation):
        return estimation
        """
        Inquire im measured fundamental frequency is correct:
        """ 
        
        '''
        import guidata
        guidata.qapplication()
        import guidata.dataset.dataitems as di
        import guidata.dataset.datatypes as dt
    
        
        class Processing(dt.DataSet):
            """ Fundamental Frequency """
            correctedFreq    = di.FloatItem("fundamental frequency [Hz]", default=estimation)
        param = Processing()
        okPressed = param.edit()
        if okPressed:
            return param.correctedFreq
        else:  # Cancel button pressed
            return estimation
        '''
    #Ask for a better fundamental frequency
    exFreq = max(0, min(f.max(), getExFreq(estimation)))
    
    #Check if we have at least one harmonic:
    if exFreq>0.5*f.max():
        print "THD calculation not possible, extend frequency window to at least 2*fundamental frequency"
        THD = 999
    else:
        #Get 5% window around fundamental frequency and calculate power:
        mask = (f>exFreq*0.975) & (f<exFreq*1.025)
        print "Calculating fundamental energy from points: frequency=%s, Amplitude=%s" %(f[mask], A[mask])
        P1 = numpy.vdot(A[mask],A[mask]) #squared amplitude
        PH = 0
        #Sum up the Power of all harmonic frequencies in spectrum:
        noHarmonics = numpy.int(numpy.floor(f.max()/exFreq))
        for i in range(noHarmonics-1):
            mask = (f>(i+2)*exFreq*0.975) & (f<(i+2)*exFreq*1.025)
            PH = PH + (numpy.vdot(A[mask],A[mask]))  #squared amplitude
        THD = PH / P1 *100
    
    #******* END THD CALCULATION    *************
    
    #Open new plot tab:
    import plotWidget
    window = widget.createNewWindow()
    container = plotWidget.plotContainer(window)
    plotWidget = plotWidget.PlotWidget(container)
    container.setPlotWidget(plotWidget)
    
    #Plot data    
    plotdata = ArrayPlotData(x = f, y = A, border_visible=True, overlay_border=True)
    plot = Plot(plotdata, title="FFT")  #Plot(plotdata, title="FFT")
    barPlot = plot.plot(("x", "y"), type="bar",bar_width=0.3, color="blue")[0]   
    
    # Attach some tools to the plot
    plot.tools.append(PanTool(plot))
    plot.overlays.append(ZoomTool(plot))  
       
    #Activate Plot:
    plotWidget.setPlot(plot)   
    if THD != 999:
        thdLabel = DataLabel(component=plotWidget.plot, data_point=(f[A.argmax()], A.max()),
                           label_position="bottom right", padding_bottom=20,
                           marker_color="transparent",
                           marker_size=8,
                           marker="circle",
                           arrow_visible=False,
                           label_format= str('THD = %.4g percent based on %d harmonics of the %.4g Hz frequency' %(THD, noHarmonics,exFreq)))
        plotWidget.plot.overlays.append(thdLabel)       
    container.setPlotWidget(plotWidget)       

    layout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
    layout.addWidget(container)
    window.setLayout(layout)
    window.show()
    

def getPlotCallbacks():
    ''' Return callbacks for plot plugins
    '''
    
    #Add here functionality as soon as it is implemented with chaco:
    '''
    return [["Minimum"         , plotMin           ],
            ["Maximum"         , plotMax           ],
            ["Arithmetic Mean" , plotArithmeticMean],
            ["Rectified Mean"  , plotRectifiedMean ],
            ["Root Mean Square", plotRootMeanSquare],
            ["FFT"             , plotFFT           ],
            ["FFT+Total Harmonic Distortion(THD)", plotFFTPlusTHD           ]]
    '''
    return [["FFT"             , plotFFT           ],
            ["FFT+Total Harmonic Distortion(THD)", plotFFTPlusTHD           ]]
    
def test3(widget):
    pass


def test(model, variable, data, unit):
    print "bla", model, variable, data, unit


def test2(model):
    print "blubb", model

from PySide import QtGui
import os
def saveAsCSV(model, variable, data, unit):
    (fileName, extension) = QtGui.QFileDialog().getSaveFileName(None, 'Save Variable as CSV', os.getcwd(), "Comma Seperated Value (*.csv)")
    if not fileName:
        return
    print "Saving trajectory of {model}.{variable}[{unit}] to {file}".format(model=model.name, variable=variable, unit=unit, file=fileName)
    with open(fileName, "w") as file:
        file.write("TimeStamp; {model}.{variable}[{unit}]\n".format(model=model.name, variable=variable, unit=unit))
        for x in range(data[0].size):
            file.write("{time:>10.10e}; {value:>10.10e}\n".format(time=data[0][x], value=data[1][x]))
        file.flush()
        file.close()


def getVariableCallbacks():
    return [["test", test], ["Save as CSV", saveAsCSV]]


def getModelMenuCallbacks():
    return [["test2", test2]]


def init(QMainWindow, subMenu):
    '''
    The init function is the entry point for every Plug-In.
    It should add at least some menu entries and return the created object.
    '''
    #Change Toolbar:
    subMenu.setTitle("Signal Processing")
    return BrowserContextMenu(QMainWindow, subMenu)


def getTimeRange(time):
    """
    Inquire time range for the desired operation (default: between first and last time instant)
    """
    Tmin_default = time[0]
    Tmax_default = time[-1]
    
    Tmin = Tmin_default
    Tmax = Tmax_default

    '''

    import guidata
    guidata.qapplication()
    import guidata.dataset.datatypes as dt
    import guidata.dataset.dataitems as di

    class Processing(dt.DataSet):
        """ Horizontal range """
        Tmin = di.FloatItem("min [s]", default=Tmin_default)
        Tmax = di.FloatItem("max [s]", default=Tmax_default)

    param = Processing()
    okPressed = param.edit()
    if okPressed:
        Tmin = max(Tmin_default, param.Tmin)
        Tmax = min(Tmax_default, param.Tmax)
    else:  # Cancel button pressed
        Tmin = Tmin_default
        Tmax = Tmax_default
        
    '''
    return (Tmin, Tmax)


def getFFTtimeRange(time):
    """
    Inquire time range for FFT and the number of FFT points
    """
    Tmin_default    = time[0]
    Tmax_default    = time[-1]
    nPoints_default = 512

    Tmin = Tmin_default
    Tmax = Tmax_default
    nPoints = nPoints_default

    '''

    import guidata
    guidata.qapplication()
    import guidata.dataset.datatypes as dt
    import guidata.dataset.dataitems as di

    class Processing(dt.DataSet):
        """ FFT analysis """
        Tmin    = di.FloatItem("min [s]"             , default=Tmin_default)
        Tmax    = di.FloatItem("max [s]"             , default=Tmax_default)
        nPoints = di.FloatItem("number of fft points", default=nPoints_default)
    param = Processing()
    okPressed = param.edit()
    if okPressed:
        Tmin = max(Tmin_default, param.Tmin)
        Tmax = min(Tmax_default, param.Tmax)
        nPoints = min( max(2, param.nPoints), time.size )
    else:  # Cancel button pressed
        Tmin    = Tmin_default
        Tmax    = Tmax_default
        nPoints = nPoints_default
    ''' 
       
    return (Tmin, Tmax, nPoints)


def getValuesInRange(time, values, Tmin, Tmax):
    """
    Extract variable values in the range Tmin .. Tmax

    Inputs:
       time : Vector of time values
       values: Vector of corresponding variable values
       Tmin  : Lower time value
       Tmax  : Upper time value

    Outputs:
       (time2, values2): Tupel of time and variable values as subseet of time and values
                         so that time2[0] = Tmin and times2[-1] = Tmax
    """
    i = numpy.logical_and(time >= Tmin, time <= Tmax)
    time2 = time[i]
    values2 = values[i]
    return (time2, values2)


def plotSignalAndFeature(variable, time, values, unit,
                         featureName, featureTime, featureValue,
                         Tmin, Tmax, aboveLine=True, markFeature=True):
    """
    Plot signal and a feature of the signal

    Inputs:
       variable    : Name of the signal
       time        : time of variable values
       values      : variable values
       unit        : Unit of values as string
       featureName : Name of the feature (e.g. "min")
       featureTime : Value of the time instant where the featureValue shall be displayed
       featureValue: Value of the feature
       Tmin        : Minimum time instant of feature calculation
       Tmax        : Maximum time instant of feature calculation
       aboveLine   : = True : "featureName = featureValue" is displayed above the feature line
                     = False: Is displayed below the feature line
       markFeature : = True : Mark point (featureTime, featureValue) with a circle
                     = False: Do not mark it.
    """
    # new figure
    fig = plt.figure()

    # plot variable and inquire properties of the curve
    line = plt.plot(time, values)
    axes = plt.gca()
    color = line[0].get_color()
    width = 0.5 * line[0].get_linewidth()

    # determine coordinates where to store featureValue
    distText      = 13   # Distance between line and featureValue in [points]
    distInvisible = 20   # Distance between line and invisible point in [points]
    #                      (y-axis limits are forced to contain featureValue)
    if not aboveLine:
        distText      = -distText
        distInvisible = -distInvisible
    textTransform      = matplotlib.transforms.offset_copy(axes.transData, fig=fig, y=distText     , units="points" )
    invisibleTransform = matplotlib.transforms.offset_copy(axes.transData, fig=fig, y=distInvisible, units="points" )
    invisibleOffset    = axes.transData.inverted().transform( invisibleTransform.transform((0,0)) )[1]

    # determine alignment of featureValue
    dT = time[-1] - time[0]
    if featureTime < time[0] + 0.1 * dT:
        align = "left"
    elif featureTime < time[0] + 0.9 * dT:
        align = "center"
    else:
        align = "right"

    # plot featureName and featureValue
    t = [Tmin, Tmax]           # first and last value of time
    v = [featureValue, featureValue]

    # plot horizontal line with vertical bars at the two ends
    lBar = abs(invisibleOffset) / 4
    plt.plot(t, v, color=color, linewidth=width)
    plt.plot([Tmin, Tmin], [featureValue + lBar, featureValue - lBar], color=color, linewidth=width)
    plt.plot([Tmax, Tmax], [featureValue + lBar, featureValue - lBar], color=color, linewidth=width)
    if markFeature:
        plt.plot(featureTime, featureValue, "o")
    plt.plot(featureTime, featureValue + invisibleOffset, "")
    plt.text(featureTime, featureValue, featureName + "=" + ("%0.5g" % featureValue),
             transform=textTransform, horizontalalignment=align, color="0", fontsize="smaller")
    plt.grid()
    plt.xlabel("time [s]")
    if isinstance(unit, str) and unit != "":
        plt.ylabel(variable + " [" + unit + "]")
    else:
        plt.ylabel(variable)
    plt.show()
    if markFeature:
        print(featureName + "(" + variable + ") = " + str(featureValue) + " " + unit + " at "
                                                    + str(featureTime)  + " s "
                                                    + "(first occurrence in " + str(Tmin) + " ... "
                                                                              + str(Tmax) + " s)\n")
    else:
        print(featureName + "(" + variable + ") = " + str(featureValue) + " " + unit
                                                    + " (in range " + str(Tmin) + " ... "
                                                                    + str(Tmax) + " s)\n")


class BrowserContextMenu:
    '''
        This functions adds the entries to the toolbar and links them with the functions
        which are called when the buttons are pressed
    '''
    def __init__(self, QMainWindow, subMenu):

        import os
        self.rootDir = os.path.abspath(os.path.dirname(__file__))

        # Register in context menu (when right-clicking on gui elements):
        QMainWindow.actionOnVariableInTree.append(["Signal Processing", "Minimum"          , self.myMin])
        QMainWindow.actionOnVariableInTree.append(["Signal Processing", "Maximum"          , self.myMax])
        QMainWindow.actionOnVariableInTree.append(["Signal Processing", "Arithmetic mean"  , self.myArithmeticMean])
        QMainWindow.actionOnVariableInTree.append(["Signal Processing", "Rectified mean"   , self.myRectifiedMean])
        QMainWindow.actionOnVariableInTree.append(["Signal Processing", "Root mean square" , self.myRootMeanSquare])
        QMainWindow.actionOnVariableInTree.append(["Signal Processing", "FFT", self.myFFT])

    """ The following functions are accessible only by context menu and not by button.
        Argument list:
        model   : name of model
        variable: variable name
        data    : (time, values, interpolationType) tuple
        unit    : Unit of data as string
    """

    def myMin(self, model, variable, data, unit):
        """ Determine minimum of signal """
        time = data[0]
        values = data[1]
        (Tmin, Tmax) = getTimeRange(time)
        (timeInRange, valuesInRange) = getValuesInRange(time, values, Tmin, Tmax)
        i = valuesInRange.argmin()
        tMin = timeInRange[i]
        vMin = valuesInRange[i]
        plotSignalAndFeature(variable, time, values, unit, "min",
                             tMin, vMin, Tmin, Tmax, aboveLine=False)

    def myMax(self, model, variable, data, unit):
        """ Determine maximum of signal """
        time = data[0]
        values = data[1]
        (Tmin, Tmax) = getTimeRange(time)
        (timeInRange, valuesInRange) = getValuesInRange(time, values, Tmin, Tmax)
        i = valuesInRange.argmax()
        tMax = timeInRange[i]
        vMax = valuesInRange[i]
        plotSignalAndFeature(variable, time, values, unit, "max",
                             tMax, vMax, Tmin, Tmax)

    def myArithmeticMean(self, model, variable, data, unit):
        """ Determine arithmetic mean of signal """
        time = data[0]
        values = data[1]
        (Tmin, Tmax) = getTimeRange(time)
        (timeInRange, valuesInRange) = getValuesInRange(time, values, Tmin, Tmax)
        vMean = Algorithms.arithmeticMean(timeInRange, valuesInRange)
        tMean = timeInRange[0] + (timeInRange[-1] - timeInRange[0]) / 2
        plotSignalAndFeature(variable, time, values, unit, "mean",
                             tMean, vMean, Tmin, Tmax, markFeature=False)

    def myRectifiedMean(self, model, variable, data, unit):
        """ Determine rectified mean of signal """
        time = data[0]
        values = data[1]
        (Tmin, Tmax) = getTimeRange(time)
        (timeInRange, valuesInRange) = getValuesInRange(time, values, Tmin, Tmax)
        vMean = Algorithms.rectifiedMean(timeInRange, valuesInRange)
        tMean = timeInRange[0] + (timeInRange[-1] - timeInRange[0]) / 2
        plotSignalAndFeature(variable, time, values, unit, "rm",
                             tMean, vMean, Tmin, Tmax, markFeature=False)

    def myRootMeanSquare(self, model, variable, data, unit):
        """ Determine root mean square of signal """
        time = data[0]
        values = data[1]
        (Tmin, Tmax) = getTimeRange(time)
        (timeInRange, valuesInRange) = getValuesInRange(time, values, Tmin, Tmax)
        vMean = Algorithms.rootMeanSquare(timeInRange, valuesInRange)
        tMean = timeInRange[0] + (timeInRange[-1] - timeInRange[0]) / 2
        plotSignalAndFeature(variable, time, values, unit, "rms",
                             tMean, vMean, Tmin, Tmax, markFeature=False)

    def myFFT(self, model, variable, data, unit):
        time = data[0]
        values = data[1]
        (Tmin, Tmax, N) = getFFTtimeRange(time)
        (timeInRange, valuesInRange) = getValuesInRange(time, values, Tmin, Tmax)

        # Compute fft: A=A(f)
        (f,A) = Algorithms.fft(timeInRange, valuesInRange, N)

        # Plot A=A(f)
        plt.figure()
        plt.plot(f, A)
        plt.grid()
        plt.xlabel("frequency [Hz]")
        if isinstance(unit, str) and unit != "":
            plt.ylabel("amplitude [" + unit + "]")
        else:
            plt.ylabel("amplitude")
        plt.show()
