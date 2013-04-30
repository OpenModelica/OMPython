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
Plugin for finding the minimum and maximum in a plot
The plugin system at currently very much work in progress!
This is an eleborate example on the ussage of the plugin system.
'''


from chaco.api import DataLabel


def print0r(model):
    ''' Example callback function for model specific actions
        parameter: a model instance
    '''
    print "bla", model


def plotprint0r(widget):
    ''' Example callback function for plot specific actions
        parameter a PlotWidget instance
    '''
    print "blubb", widget


def logX(widget):
    if widget.plot.value_scale == 'log':
        widget.plot.value_scale = 'linear'
    else:
        widget.plot.value_scale = 'log'
    widget.plot.request_redraw()


def logY(widget):
    if widget.plot.index_scale == 'log':
        widget.plot.index_scale = 'linear'
    else:
        widget.plot.index_scale = 'log'
    widget.plot.request_redraw()


def createPlotRow(widget):
    # just for tests, do not use
    widget.parent().addBottom(widget.parent(), None)


def createWindow(widget):
    ''' Example on creating a new plot window in the
        main window MDI-Area
    '''
    import plotWidget
    from PySide import QtGui
    from numpy import linspace
    from scipy.special import jn
    from chaco.api import ArrayPlotData, Plot

    window = widget.createNewWindow()
    container = plotWidget.plotContainer(window)
    plotWidget = plotWidget.PlotWidget(container)
    container.setPlotWidget(plotWidget)

    x = linspace(-2.0, 10.0, 100)
    pd = ArrayPlotData(index=x)
    for i in range(5):
        pd.set_data("y" + str(i), jn(i, x))
    plot = Plot(pd, title=None, padding_left=60, padding_right=5, padding_top=5, padding_bottom=30, border_visible=True)
    plot.plot(("index", "y0", "y1", "y2"), name="j_n, n<3", color="red")
    plotWidget.setPlot(plot)

    layout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
    layout.addWidget(container)
    window.setLayout(layout)
    window.show()


def printData(widget):
    ''' Example callback function for plot specific actions
        showing how to access data elements
    '''
    for x in widget.plot.data.list_data():
        print "Data entries: ", x, " of type: ", type(widget.plot.data.get_data(x)), " data: ", widget.plot.data.get_data(x)

labels = dict()


def removeLabels(var):
    # I think, this is the way it has to be done in the current setup, yet this is really really
    # ugly! I need to find a better solution to this. functools.partial could work...
    widget, model, variable = var
    for var in (y[:y.rfind(".values")].split(":") for y in widget.plot.data.list_data()):
        global labels
        if ":".join(var) in labels:
            widget.plot.overlays.remove(labels[":".join(var)][0])
            widget.plot.overlays.remove(labels[":".join(var)][1])
            widget.plot.request_redraw()


def findMinMax(widget):
    ''' Find the min and max value within all shown plots and display them
    '''
    for (modelNumber, modelName, variableName), data in widget.getData():
        # print "var:", var, "data: ", data
        minVal = (0, float("inf"))
        maxVal = (0, float("-inf"))
        for time, value in data:
            if (not widget.plot.selection) or (time > widget.plot.selection[0] and time < widget.plot.selection[1]):
                if value < minVal[1]:
                    minVal = (time, value)
                if value > maxVal[1]:
                    maxVal = (time, value)
        print "minimum of ", modelNumber, modelName, variableName, " at ", minVal, "maximum at ", maxVal, " in interval: ", widget.plot.selection
        minLabel = DataLabel(component=widget.plot, data_point=minVal,
                           label_position="top", padding_bottom=20,
                           marker_color="transparent",
                           marker_size=8,
                           marker="circle",
                           arrow_visible=False,
                           label_format=str('Min: (%(x)f, %(y)f)'))
        widget.plot.overlays.append(minLabel)
        maxLabel = DataLabel(component=widget.plot, data_point=maxVal,
                           label_position="top", padding_bottom=20,
                           marker_color="transparent",
                           marker_size=8,
                           marker="circle",
                           arrow_visible=False,
                           label_format=str('Max: (%(x)f, %(y)f)'))
        widget.plot.overlays.append(maxLabel)
        labels[":".join((modelNumber, modelName, variableName))] = (minLabel, maxLabel)
        widget.variableRemoved.connect(removeLabels)


def getModelCallbacks():
    ''' Registers model callbacks with main application
        return a list of lists, one list for each callback, each sublist
        containing a name for the function and a function pointer
    '''
    return []
            #["a", print0r],
            #            ["b", print0r]
            #           ]


def getPlotCallbacks():
    ''' see getModelCallbacks
    '''
    return [
            #["a", plotprint0r],
            #["b", plotprint0r],
            #["findMinMax", findMinMax],
            ["Print Information about data elements", printData],
            ["New plot row", createPlotRow],
            ["new MDI window", createWindow],
            ["log X", logX],
            ["log Y", logY]
           ]
