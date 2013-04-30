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

''' Plugin for finding the minimum and maximum in a plot
    The plugin system at currently very much work in progress!


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


def printData(widget):
    ''' Example callback function for plot specific actions
        showing how to access data elements
    '''
    for x in widget.plot.data.list_data():
        print "Data entries: ", x, " of type: ", type(widget.plot.data.get_data(x)), " data: ", widget.plot.data.get_data(x)


def findMinMax(widget):
    ''' Find the min and max value within all shown plots and display them
    '''
    for (modelNumber, modelName, variableName), data in ((y[:y.rfind(".values")].split(":"), zip(widget.plot.data.get_data(y[:y.rfind(".values")]+".time"), widget.plot.data.get_data(y))) for y in widget.plot.data.list_data() if y.split(".")[-1] == "values"):
        # this loop is a bit complecated but can be used as is in other plugins
        # important is the way data is saved plots with a name ending in .values and .time
        # this loop iterates over all data elements shown in the plot. For this application
        # the data is format is changed to a list of tuples (time, value) in variable data
        # modelNumber, modelName, variableName indicate current variable

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


def getModelCallbacks():
    ''' Registers model callbacks with main application
        return a list of lists, one list for each callback, each sublist
        containing a name for the function and a function pointer
    '''
    return [["a", print0r], ["b", print0r]]


def getPlotCallbacks():
    ''' see getModelCallbacks
    '''
    return [["a", plotprint0r], ["b", plotprint0r], ["findMinMax", findMinMax], ["Print Information about data elements", printData]]
