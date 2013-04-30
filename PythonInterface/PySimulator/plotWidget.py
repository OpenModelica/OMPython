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
Everything required for showing Plots
'''


from PySide import QtCore
from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = "qt4"
from PySide import QtGui
import enable.api
from chaco.api import Plot, ArrayPlotData, AbstractController, BaseXYPlot, AbstractTickGenerator
from chaco import ticks
from chaco.tools.api import ZoomTool
from chaco.tools.pan_tool import PanTool  # there is some bug in in the default Pantools handling of the event "left_up"...
from functools import partial
from numpy import array
import math


class plotContainer_test(QtGui.QWidget):
    widgets = list()

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

    def setPlotWidget(self, widget):
        print self.size()
        widget.move(0, 0)
        widget.show()
        self.widgets.append(widget)

    def resizeEvent(self, event):
        print event.oldSize(), event.size()
        #print self.itemAt(100, 100)
        self.widgets[0].resize(event.size())

    def dragEnterEvent(self, event):
        print event

    def dragMoveEvent(self, event):
        print event

    def mousePressEvent(self, event):
        print event


class plotContainer(QtGui.QWidget):
    ''' The PlotContainer arranges multiple plots in a grid
        This class is currently unfinished until a consenus is
        reached on the way plot shoulsd be arranged, added.
    '''
    activeWidgetChanged = QtCore.Signal(QtGui.QWidget)
    closed = QtCore.Signal(QtGui.QWidget)
    activeWidget = None
    columns = 0
    rows = 0

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QGridLayout(self))

    def setPlotWidget(self, widget):
        ''' primarily for use in unit test code
        '''
        self.layout().addWidget(widget, 0, 0)
        widget.activated.connect(self._changeActive)
        if (self.activeWidget):
            self.activeWidget.setDeactive()
        self.activeWidget = widget
        widget.setActive()
        self.activeWidgetChanged.emit(widget)

    def addFirst(self, parent, context):
        ''' The first element (plot) has to be added with this function
        '''
        widget = DefaultPlotWidget(parent, context)
        self.layout().addWidget(widget, 0, 0)
        widget.activated.connect(self._changeActive)
        if (self.activeWidget):
            self.activeWidget.setDeactive()
        self.activeWidget = widget
        widget.setActive()
        self.activeWidgetChanged.emit(widget)

    def addRight(self, parent, context):
        ''' Adds a new column of plots to the right
        '''
        self.columns += 1
        for row in range(0, self.rows + 1):
            widget = DefaultPlotWidget(parent, context)
            self.layout().addWidget(widget, row, self.columns)
            widget.activated.connect(self._changeActive)
            if (self.activeWidget):
                self.activeWidget.setDeactive()
            self.activeWidget = widget
            widget.setActive()
            self.activeWidgetChanged.emit(widget)

    def addBottom(self, parent, context):
        ''' Adds a new row of elements (plots) at the bottom
        '''
        self.rows += 1
        for col in range(0, self.columns + 1):
            widget = DefaultPlotWidget(parent, context)
            self.layout().addWidget(widget, self.rows, col)
            widget.activated.connect(self._changeActive)
            if (self.activeWidget):
                self.activeWidget.setDeactive()
            self.activeWidget = widget
            widget.setActive()
            self.activeWidgetChanged.emit(widget)

    @QtCore.Slot()
    def _changeActive(self):
        ''' This slot activated by a plot when clicked on
            This deactivates the old plot and activates the new one
        '''
        if (self.activeWidget):
            self.activeWidget.setDeactive()
        self.sender().setActive()
        if not self.sender() == self.activeWidget:
            self.activeWidgetChanged.emit(self.sender())
        self.activeWidget = self.sender()

    def closeEvent(self, event):
        self.closed.emit(self)


class activationHandler(AbstractController):
    ''' When the plot is clicked, this generats a Qt Signal
        which is then used to change the currently activated
        plot
    '''
    def __init__(self, plot, parent):
        AbstractController.__init__(self, plot)
        self.parent = parent

    def dispatch(self, event, suffix):
        if suffix == "left_down":
            self.parent._activated()



def getColor(plots):
    ''' Returns a color and linestyle from a list of colors and linestyles
        Used for plot lines
    '''        
    if len(plots) > 0:    
        c = dict()
        for style in getColor.styles:
            for color in getColor.colors:            
                c[color+style] = 0
        for plot in plots.values():
            c[plot[0].color+plot[0].linestyle] += 1
        cMin = min(c.values())
        for style in getColor.styles:       
            for color in getColor.colors:            
                if c[color+style] == cMin:                    
                    return color, style
    else:
        return getColor.colors[0], getColor.styles[0]
                     
getColor.colors = ['blue', 'red', 'green', 'magenta', 'cyan', 'gold', 'black', 'brown']
getColor.styles = ['solid', 'long dash']


class PlotWidget(QtGui.QWidget):
    ''' Base class for different plots
    '''
    plot = None
    activated = QtCore.Signal()
    selectionChanged = QtCore.Signal(QtGui.QWidget)
    variableAdded = QtCore.Signal(list)
    variableRemoved = QtCore.Signal(list)
    variableUpdate = QtCore.Signal(list)

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.adapter = PlotWidgetAdapter(self)
        box = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight, self)
        box.addWidget(self.adapter.control)
        self.setLayout(box)
        self.variables = []

    def setPlot(self, plot):
        ''' Sets up the underlying plot element
        '''
        self.plot = plot
        plot.tools.append(activationHandler(plot, self))
        self.adapter.setPlot(plot)

    def addVariable(self, model, variable):
        ''' Show the given variable in the plot
        '''
        var = model, variable
        self.variables.append(var)
        self.variableAdded.emit((self, model, variable))

    def removeVariable(self, model, variable):
        ''' Remove the variable
        '''
        var = model, variable
        self.variables.remove(var)
        self.variableRemoved.emit((self, model, variable))

    def updateVariable(self, model, variable):
        ''' Tells the plot, that the variables data
            has changed and the plot needs to be updated
        '''
        self.variableUpdate.emit((self, model, variable))

    @QtCore.Slot()
    def setActive(self):
        ''' Tells widget that is has been selected as
            activated.
        '''
        if self.plot:
            self.plot.bgcolor = (1.0, 1.0, 1.0)
            self.plot.request_redraw()

    @QtCore.Slot()
    def setDeactive(self):
        ''' Widget has been deactivated
        '''
        if self.plot:
            self.plot.bgcolor = (0.9, 0.9, 0.9)
            self.plot.request_redraw()

    def _activated(self):
        self.activated.emit()

    def _selectionChanged(self):
        self.selectionChanged.emit(self)

    def createNewWindow(self):
        from PySide import QtGui
        window = QtGui.QWidget(self.parent().parent().parent().parent().parent())
        self.parent().parent().parent().parent().addSubWindow(window)
        return window


class PlotWidgetAdapter(enable.api.Window):
    ''' Adapter for combining Chaco elements with QtWidgets
    '''
    def __init__(self, parent):
        super(enable.api.Window, self).__init__(parent, -1)
        self.parent = parent

    def setPlot(self, plot):
        self.component = plot


''' Some functionality of these derived tools are active but not
    imidiatly obvious! For example pressing ESC will reset a plot
    and dragging while holding STRG/CTRL zooms to an area.
'''


class NonAxisPan(PanTool):
    ''' Modified standard PanTool
        Only difference is, that panning only works in the plot area
        itself and not in the axis areas.
    '''
    def __init__(self, plot):
        PanTool.__init__(self, plot)
        self.speed = 2
        self.drag_pointer = "cross"

    def drag_start_DEACTIVE(self, event):
        self.origpos = (event.x, event.y)

    def dragging_DEACTIVE(self, event):
        ''' These two functions are currently not in use
            They remain here for future reference
        '''
        plot = self.component
        mapper = plot.index_mapper
        range = mapper.range
        screenlow, screenhigh = mapper.screen_bounds
        screendelta = self.speed * (event.x - self.origpos[0])
        newlow = mapper.map_data(screenlow - screendelta)
        newhigh = mapper.map_data(screenhigh - screendelta)
        range.set_bounds(newlow, newhigh)
        self.origpos = (event.x, event.y)
        plot.request_redraw()

    def is_draggable(self, y, x):
        return self.component.value_mapper.screen_bounds[0] < x and self.component.value_mapper.screen_bounds[1] > x and self.component.index_mapper.screen_bounds[0] < y and self.component.index_mapper.screen_bounds[1] > y


class axisZoom(ZoomTool):
    ''' Modification of the default zommtool
        While hovering the plot the default behaviour
        is unchanged, while hovering the axes, it only
        zooms along this axis.
    '''
    def normal_mouse_wheel(self, event):
        self.zoom_factor = 1.25
        if self.component.x_axis.is_in(event.x, event.y):
            self.axis = "index"
        elif self.component.y_axis.is_in(event.x, event.y):
            self.axis = "value"
        else:
            self.axis = "both"
        if event.mouse_wheel != 0:
            self.zoom_to_mouse = True
            if event.mouse_wheel > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.handled = True
            self.component.request_redraw()


class ConstPlot(BaseXYPlot):
    ''' Specialized plot type for displaying constants.
        These have only one value and are always displayed
        independent of time.
    '''
    color = "red"
    line_width = 1

    def __init__(self, **kwtraits):
        BaseXYPlot.__init__(self, **kwtraits)

    def _gather_points(self):
        # not required for this type
        pass

    def _downsample(self):
        # not required for this type
        pass

    def _render(self, gc, points):
        ''' Displays a single horizontal line to indicate the constants value
        '''
        value = self.value.get_data()[0]
        value_screen = self.y_mapper.map_screen(value)
        with gc:
            gc.set_antialias(True)
            gc.clip_to_rect(self.x, self.y, self.width, self.height)
            gc.set_alpha(1)
            gc.set_stroke_color(enable.api.color_table[self.color])
            gc.set_line_width(self.line_width)
            gc.move_to(self.x_mapper.low_pos, value_screen)
            gc.line_to(self.x_mapper.high_pos, value_screen)
            gc.draw_path()

    def _render_icon(self, gc, x, y, width, height):
        ''' An icon shown in the ledgend.
            Just a short line
        '''
        with gc:
            gc.set_stroke_color(enable.api.color_table[self.color])
            gc.set_line_width(self.line_width)
            gc.set_antialias(True)
            gc.move_to(x, y + height / 2)
            gc.line_to(x + width, y + height / 2)
            gc.stroke_path()
        return


class ContextMenu(AbstractController):
    ''' Shows a context menu for the plot with custom commands
    '''
    def __init__(self, plot, parent, menuActions):
        ''' Parent is a QWidget,
            MenuActions is a list with tuples of format:
            (str<DisplayedName>, func<callback>)
        '''
        AbstractController.__init__(self, plot)
        self.parent = parent
        self.menuActions = menuActions

    def normal_right_down(self, event):
        ''' Displays the context menu
        '''
        menu = QtGui.QMenu(event.window.parent)
        menu.move(QtGui.QCursor.pos())  # the menu shall be shown at the curren cursor position
        for pluginEntry in self.menuActions:
            for name, func in pluginEntry:
                menu.addAction(name, partial(func, widget=self.parent))  # callbacks get the plot widget as parameter
        menu.show()


class setSelectionDialog(QtGui.QDialog):
    ''' Dialog for input of upper and lower limits of a custom
        selection range. Used by Selector.
    '''
    selectionSet = QtCore.Signal(float, float)

    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Set Selection")
        layout = QtGui.QGridLayout(self)
        self.setLayout(layout)
        self.minIn = QtGui.QLineEdit(self)
        layout.addWidget(QtGui.QLabel("Min: "), 0, 0)
        layout.addWidget(self.minIn, 0, 1)
        self.maxIn = QtGui.QLineEdit(self)
        layout.addWidget(QtGui.QLabel("Max: "), 1, 0)
        layout.addWidget(self.maxIn, 1, 1)
        done = QtGui.QPushButton("Done", self)
        done.clicked.connect(self.selectionDone)
        layout.addWidget(done)

    def selectionDone(self):
        self.selectionSet.emit(float(self.minIn.text()), float(self.maxIn.text()))
        self.close()


class Selector(enable.api.BaseTool):
    ''' Tool for selecting a time range in a plot
    '''
    def __init__(self, plot, parent):
        enable.api.BaseTool.__init__(self, plot)
        self.parent = parent
        self.visible = True
        self.component.selection = None

    def dispatch(self, event, suffix):
        ''' Divertes double click events and dispatches all others
            using the base class functionality
        '''
        if self.component.x_axis.is_in(event.x, event.y) and suffix == "left_dclick":
            ''' When the X-Axis is double clicked, this shows an input dialog
                for manually entering the slection boundaries.
            '''
            diag = setSelectionDialog(self.parent)
            diag.selectionSet.connect(self.setSelection)
            diag.show()
        enable.api.BaseTool.dispatch(self, event, suffix)

    @QtCore.Slot()
    def setSelection(self, a, b):
        ''' Set selection to given limits a and b
        '''
        self.event_state = "selected"
        self.component.selection = (a, b)
        self.component.request_redraw()
        self.parent._selectionChanged()

    def normal_left_down(self, event):
        if self.component.x_axis.is_in(event.x, event.y):
            self.event_state = "selecting"
            event.window.set_pointer("size left")
            self.component.selection = (self.component.x_axis.mapper.map_data(event.x), self.component.x_axis.mapper.map_data(event.x))
            self.component.request_redraw()
            event.handled = True

    def selecting_mouse_move(self, event):
        self.component.selection = (self.component.selection[0], self.component.x_axis.mapper.map_data(event.x))
        self.component.request_redraw()
        event.handled = True

    def selecting_left_up(self, event):
        self._endSelection(event)

    def selecting_mouse_leave(self, event):
        self._endSelection(event)

    def _endSelection(self, event):
        if self.component.selection[0] != self.component.selection[1]:  # not a double click
            self.event_state = "selected"
            self.parent._selectionChanged()
        else:
            self.event_state = "normal"
            self.component.selection = None
            self.component.request_redraw()
        event.window.set_pointer("arrow")
        event.handled = True

    def selected_left_down(self, event):
        if self.component.x_axis.is_in(event.x, event.y):
            self.event_state = "normal"
            self.component.selection = None
            self.component.request_redraw()
            self.parent._selectionChanged()

    def do_layout(self):
        pass

    def overlay(self, component, gc, view_bounds=None, mode='normal'):
        ''' Displays the selected area by overlaying it with a
            semi transparent, colored area
        '''
        if self.component.selection:
            x1_, x2_ = self.component.selection
            x1 = self.component.x_axis.mapper.map_screen(x1_)
            x2 = self.component.x_axis.mapper.map_screen(x2_)
            x1 = max(min(x1, self.component.x_axis.mapper.high_pos + 1), self.component.x_axis.mapper.low_pos)
            x2 = max(min(x2, self.component.x_axis.mapper.high_pos + 1), self.component.x_axis.mapper.low_pos)
            with gc:
                gc.set_fill_color((0.8, 0.8, 1.0, 0.7))
                gc.rect(x1, self.component.value_mapper.screen_bounds[0], x2 - x1, self.component.value_mapper.screen_bounds[1] - self.component.value_mapper.screen_bounds[0] + 1)
                gc.draw_path()


class updateHack(QtCore.QObject):
    """ ugly hack required, cause for some reason QObjects and enable/chaco elements
        are incompatible with each other.
    """
    def __init__(self, obj, timeout=0):
        QtCore.QObject.__init__(self)
        self.obj = obj
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(timeout)

    def update(self):
        self.obj.update()


# a global variable for the current time to be displayed by the timeMarker in all plot
timeMark = None


class TimeMarker(enable.api.BaseTool):
    ''' The timeMarker draws a vertical line at the current mouse position in the current
        plot and at the according timeStamp in all other plots.
    '''
    # Requires global variable timeMark
    draw_layer = 'overlay'

    def __init__(self, plot):
        enable.api.BaseTool.__init__(self, plot)
        self.visible = True
        self.updateHack = updateHack(self, 50)

    def normal_mouse_move(self, event):
        global timeMark
        timeMark = self.component.x_axis.mapper.map_data(event.x)
        self.component.request_redraw()

    def normal_mouse_leave(self, event):
        global timeMark
        timeMark = None
        self.component.request_redraw()

    def overlay(self, component, gc, view_bounds=None, mode='normal'):
        global timeMark
        if timeMark:
            x = max(min(self.component.x_axis.mapper.map_screen(timeMark), self.component.x_axis.mapper.high_pos + 1), self.component.x_axis.mapper.low_pos)
            with gc:
                gc.set_stroke_color(enable.api.color_table["black"])
                gc.set_line_width(1)
                gc.set_antialias(True)
                gc.move_to(x, self.component.value_mapper.screen_bounds[0])
                gc.line_to(x, self.component.value_mapper.screen_bounds[1])
                gc.stroke_path()
            # redraws are handled by the updateHack in regular intervals.
            # redraws must be handled carefully or otherwise they lock up
            # the entire CPU
            #self.component.request_redraw()

    def do_layout(self):
        pass

    def update(self):
        self.component.request_redraw()


class tickGenerator(AbstractTickGenerator):
    pixelInterval = 50

    def __init__(self, orientation="h"):
        AbstractTickGenerator.__init__(self)
        self.orientation = orientation

    def get_ticks_and_labels(self, data_low, data_high, bounds_low, bounds_high, orientation="h"):
        abslargest = max(abs(data_low), abs(data_high))
        exp = math.floor(math.log(abslargest, 10))
        steps = math.floor((bounds_high - bounds_low) / self.pixelInterval)
        if steps <= 1:
            return array([data_low]), ["{:1.2g}".format(data_low)]
        step = ticks.tick_intervals(data_low, data_high, steps)
        retData = []
        retLabels = []
        if  exp > 3 or exp < -2:
            retData.append(data_high)
            tmp = "[10^" + str(int(exp)) + "]"
            if self.orientation == "h":
                tmp += "       "
            retLabels.append(tmp)
        pos0 = ticks.calc_bound(data_high, step, True)
        pos= pos0
        i = 0
        while (pos - step > data_low):
            i += 1
            pos = pos0 - i*step
            retData.append(pos)
            if exp > 3 or exp < -2:
                retLabels.append('{:g}'.format(pos / math.pow(10, exp)))
            else:
                retLabels.append('{:g}'.format(pos))
        return array(retData), retLabels


class DefaultPlotWidget(PlotWidget):
    ''' The plot widget used by default in PySimulator for displaying multiple variable
        trajectories with a custom tool set.
    '''
    def __init__(self, parent, context=None):
        PlotWidget.__init__(self, parent)
        self.plotActive = None
        plot = Plot(None, title=None, padding=[45, 10, 5, 20], border_visible=True)
        self.component = plot
        self.setPlot(plot)
        self.plot.window.bgcolor = (1, 1, 1, 0)
        self.tickGenV = tickGenerator("v")
        self.tickGenI = tickGenerator("h")
        self.plot.value_axis.tick_generator = self.tickGenV
        self.plot.index_axis.tick_generator = self.tickGenI
        self.context = context
        # Max. number of points to be displayed in plots
        self.maxDisplayPoints = 5000000

    def getData(self):
        ''' Return a list of the variables in the plot and their data elements
            in the format:
            list((<modelNumber>, <modelName>, <variableName>), <variableData - list(<timeStamp><value>)>)
        '''
        return ((y[:y.rfind(".values")].split(":"), zip(self.plot.data.get_data(y[:y.rfind(".values")] + ".time"), self.plot.data.get_data(y))) for y in self.plot.data.list_data() if y.split(".")[-1] == "values")

    def activatePlot(self):
        # some parts cause problems on initialization
        self.plot.legend.visible = True
        self.plot.overlays.append(TimeMarker(self.plot))
        self.plot.overlays.append(axisZoom(self.plot))
        self.plot.tools.append(NonAxisPan(self.plot))
        self.plot.overlays.append(Selector(self.plot, self))
        self.plot.value_range.tight_bounds = False
        self.plot.index_range.tight_bounds = True
        if self.context:
            self.plot.tools.append(ContextMenu(self.plot, self, self.context))
        self.plotActive = True

    def _idVariableUnit(self, model, variable, dPoints=1):
        unit = ''
        markDownSampling = ''
        if dPoints > 1:
            markDownSampling = '*'
        if model.variableTree.variable[variable].unit is not None:
            if len(model.variableTree.variable[variable].unit) > 0:
                unit = ' [' + model.variableTree.variable[variable].unit + ']'
        return markDownSampling + model.numberedModelName.split(':', 1)[0] + ":" + variable + unit

    def addVariable(self, model, variable):
        dPoints = 1
        if not self.plotActive:
            self.activatePlot()
        PlotWidget.addVariable(self, model, variable)
        if (model.integrationResults.isAvailable):
            y, x, interpolationMethod = model.integrationResults.readData(variable)
            if len(x) > self.maxDisplayPoints:
                dPoints = max(1, math.ceil(float(len(x)) / self.maxDisplayPoints))
                x = x[::dPoints]
                y = y[::dPoints]
        else:
            return
        if (self.plot.data == None):
                self.plot.data = ArrayPlotData()
        if not x == None and not y == None:
            self.plot.data.set_data(model.numberedModelName + ":" + variable + ".values", x)
            self.plot.data.set_data(model.numberedModelName + ":" + variable + ".time", y)
            lPlots = self.plot.legend.plots
            name = self._idVariableUnit(model, variable)           
            color, style = getColor(self.plot.plots)
            p = self.plot.plot((model.numberedModelName + ":" + variable + ".time", model.numberedModelName + ":" + variable + ".values"), name=name, color=color, linestyle=style, line_width=1.5, render_style=("connectedhold" if interpolationMethod == "constant" else "connectedpoints"))
            legendLabel = self._idVariableUnit(model, variable, dPoints)
            if not hasattr(self.plot, 'legendLabel'):
                self.plot.legendLabel = dict()
            self.plot.legendLabel[name] = legendLabel
            self.plot.legend.labels.append(legendLabel)
            self.plot.legend.plots = lPlots
            self.plot.legend.plots[legendLabel] = p
        if y == None and not x == None:
            self.plot.data.set_data(model.numberedModelName + ":" + variable + ".values", x)
            self.plot.data.set_data(model.numberedModelName + ":" + variable + ".time", [0])
            lPlots = self.plot.legend.plots
            name = self._idVariableUnit(model, variable)
            color, style = getColor(self.plot.plots)
            p = self.plot.add_xy_plot(model.numberedModelName + ":" + variable + ".time", model.numberedModelName + ":" + variable + ".values", ConstPlot, name=name, color=color, linestyle=style, line_width=1.5)
            legendLabel = self._idVariableUnit(model, variable, dPoints)
            if not hasattr(self.plot, 'legendLabel'):
                self.plot.legendLabel = dict()
            self.plot.legendLabel[name] = legendLabel
            self.plot.legend.labels.append(legendLabel)
            self.plot.legend.plots = lPlots
            self.plot.legend.plots[legendLabel] = p
        self.plot.request_redraw()

    def removeVariable(self, model, variable):
        PlotWidget.removeVariable(self, model, variable)      
        name = self._idVariableUnit(model, variable)
        if name in self.plot.plots:
            lPlots = self.plot.legend.plots
            self.plot.delplot(name)
            legendLabel = self.plot.legendLabel[name]
            del(self.plot.legendLabel[name])
            del(lPlots[legendLabel])            
            del(self.plot.legend.labels[self.plot.legend.labels.index(legendLabel)])                        
            self.plot.legend.plots = lPlots
            self.plot.data.del_data(model.numberedModelName + ":" + variable + ".values")
            self.plot.data.del_data(model.numberedModelName + ":" + variable + ".time")
        self.plot.request_redraw()

    def updateVariable(self, model, variable):
        name = self._idVariableUnit(model, variable)        
        if not name in self.plot.plots:
            self.addVariable(model, variable)
        else:
            dPoints = 1
            y, x, interpolationMethod = model.integrationResults.readData(variable)
            if x is None:
            	return
            if len(x) > self.maxDisplayPoints:
                dPoints = max(1,math.ceil(float(len(x)) / self.maxDisplayPoints))
                x = x[::dPoints]
                y = y[::dPoints]
            self.plot.data.set_data(model.numberedModelName + ":" + variable + ".values", x)
            self.plot.data.set_data(model.numberedModelName + ":" + variable + ".time", y)
            legendLabel = self._idVariableUnit(model, variable, dPoints)
            if legendLabel not in self.plot.legend.labels:
                # Update legend label
                legendLabelOld = self.plot.legendLabel[name]
                self.plot.legendLabel[name] = legendLabel
                index = self.plot.legend.labels.index(legendLabelOld)
                self.plot.legend.labels[index] = legendLabel             
                self.plot.legend.plots[legendLabel] = self.plot.legend.plots[legendLabelOld]
                del(self.plot.legend.plots[legendLabelOld])              
            self.plot.request_redraw()


if __name__ == "__main__":
    ''' Development and unit test code

        Generates an example plot for testing features
    '''
    from numpy import linspace
    from scipy.special import jn
    from PySide import QtGui

    def printbla(widget):
        print "printing ", widget, " Selected region: ", widget.plot.selection

    def manuallySetSelection(sel, widget):
        diag = setSelectionDialog(widget)
        diag.selectionSet.connect(sel.setSelection)
        diag.show()

    app = QtGui.QApplication.instance()
    if not app:
        app = QtGui.QApplication([])
    main_window = QtGui.QMainWindow()
    main_window.resize(500, 500)
    containter = plotContainer(main_window)
    plotWidget = PlotWidget(containter)
    containter.setPlotWidget(plotWidget)

    x = linspace(-2.0, 10.0, 100)
    pd = ArrayPlotData(index=x)
    for i in range(5):
        pd.set_data("y" + str(i), jn(i, x))
    pd.set_data("const", [4])
    plot = Plot(pd, title=None, padding_left=60, padding_right=5, padding_top=5, padding_bottom=30, border_visible=True)
    plot.legend.visible = True

    slect0r = Selector(plot, plotWidget)
    plot.overlays.append(slect0r)
    plot.tools.append(NonAxisPan(plot))
    zoom = axisZoom(component=plot)
    plot.overlays.append(zoom)
    plot.value_range.tight_bounds = False
    plot.index_range.tight_bounds = True
    plot.value_range.margin = 0.1
    menuActions = {"printbla": printbla, "Manually set Selection": partial(manuallySetSelection, sel=slect0r)}
    plot.tools.append(ContextMenu(plot, plotWidget, menuActions))
    plot.overlays.append(TimeMarker(plot))

    plot.plot(("index", "y0", "y1", "y2"), name="j_n, n<3", color="red")
    doet = plot.plot(("index", "y3"), name="j_3", color="blue", type="line")
    plot.add_xy_plot("const", "const", ConstPlot, name="const", color="blue")

    def tickFormatter(value):
        return "{:+3.2g}".format(value)
    plot.value_axis.tick_label_formatter = tickFormatter

    plotWidget.setPlot(plot)

    def print0r(widget):
        print "Selected region: ", widget.plot.selection
    plotWidget.selectionChanged.connect(print0r)

    main_window.setCentralWidget(containter)
    main_window.show()

    runBenchmark = False
    if runBenchmark:
        import cProfile
        cProfile.run('app.exec_()', 'logfile')
        import pstats
        p = pstats.Stats('logfile')
        p.strip_dirs().sort_stats('cumulative').print_stats()
    else:
        app.exec_()
