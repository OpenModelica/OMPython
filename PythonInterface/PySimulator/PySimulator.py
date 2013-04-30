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
The main UI window
'''


import os
from PySide import QtGui

version = '0.5'


def loadPlugins(type):
    def get_immediate_subdirectories(directory):
        return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name)) and name[0] != '.']

    PlugInNames = get_immediate_subdirectories(os.path.abspath(os.path.dirname(__file__)) + "/Plugins/" + type)
    ret = dict()
    for i in range(len(PlugInNames)):
            try:
                print PlugInNames[i] + " plug-in loading"
                mod = __import__('Plugins.' + type + '.' + PlugInNames[i] + "." + PlugInNames[i], locals(), globals(), ['Plugins.' + type + '.' + PlugInNames[i] + "." + PlugInNames[i]])
                ret[PlugInNames[i]] = mod
            except Exception, info:
                print PlugInNames[i] + " plug-in could not be loaded. Error message: '" + info.message + "'"
    return ret


class SimulatorGui(QtGui.QMainWindow):
    ''' The main window of the application
    '''
    # Dictionary of currently loaded models; key is the model name
    models = dict()
    plotContainers = []    
    activePlotContainer = None
    activePlot = None
    plotWindowNr = 0

    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.lastCurrentPlotWindow = None
        self.rootDir = os.path.abspath(os.path.dirname(__file__))
       
        self.setWindowTitle("Simulation and Analysis Environment")
        self.setWindowIcon(QtGui.QIcon(self.rootDir + '/Icons/anonymous_simple_weather_symbols_1.png'))
        self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)

        '''  The information output shall replace the outputs from the python shell '''
        self.textOutput = WindowConsole(self)
        self.dockTextOutput = QtGui.QDockWidget('Information output', self)
        self.dockTextOutput.setWidget(self.textOutput)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.dockTextOutput)
        self._origStdout = sys.stdout
        #sys.stdout = self.textOutput       # sometimes causes crashes of Python.exe

        self.simulatorPlugins = loadPlugins("Simulator")
        self.SimulationResult = loadPlugins("SimulationResult")
        self.analysisPlugins = loadPlugins("Analysis")

        '''  Defining the menu bar  '''
        menu = QtGui.QMenuBar()
        subMenu = menu.addMenu('File')
        openModelMenu = subMenu.addMenu("Open Model")
        for key, value in self.simulatorPlugins.items():
            openModelMenu.addAction(key, partial(self._openFileMenu, value))

        subMenu.addSeparator()
        subMenu.addAction("Open Result File", self._openResultFileMenu)
        subMenu.addAction("Convert to MTSF", self._convertResultFileMenu)
        subMenu.addSeparator()
        subMenu.addAction('Exit', self.close)
        self.simulateAction = menu.addAction("Simulate", self._showIntegratorControl)
        self.plotMenuCallbacks = []
        self.variableMenuCallbacks = []
        self.modelMenuCallbacks = []
        for pluginName, plugin in self.analysisPlugins.items():
            try:
                self.plotMenuCallbacks.append(plugin.getPlotCallbacks())
            except:
                pass
            try:
                self.variableMenuCallbacks.append(plugin.getVariableCallbacks())
            except:
                pass
            try:
                self.modelMenuCallbacks.append(plugin.getModelMenuCallbacks())
            except:
                pass

        pluginsMenu = menu.addMenu("Plugins")
        for pluginName, plugin in self.analysisPlugins.items():
            try:
                pluginMenu = pluginsMenu.addMenu(pluginName)
                for name, func in plugin.getModelCallbacks():
                    pluginMenu.addAction(name, partial(self._execAnalysisPlugin, func))
            except:
                print "No Model Callbacks for plugin: ", pluginName

        ''' The variables browser on the left side is added as dock to the main window. '''
        self._dock = QtGui.QDockWidget(self)
        self.nvb = VariablesBrowser.VariablesBrowser(self)
        self.nvb.VariableCheckChanged.connect(self._variableCheckChanged)
        self.nvb.valueChanged.connect(self._variableValueChanged)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self._dock)
        self._dock.setWidget(self.nvb)
        self._dock.setMinimumWidth(160)
        self._dock.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        self._dock.setWindowTitle('Variables Browser')

        ''' The toolbar provides buttons for user actions.
        '''
        self._plotbar = QtGui.QToolBar('Plot', self)
        self.addToolBar(QtCore.Qt.RightToolBarArea, self._plotbar)
        #self._plotbar.setIconSize(QtCore.QSize(18, 18))
        self._plotbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/window-new-6.png"), 'New Plot Window', self._newPlotContainer)
        #self._plotbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/draw-eraser-2.png"), 'Erase lines from current plot', self.erasePlotCurrentAxes)
        self._plotbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/document-save-5.png"), 'Save Figure', self.saveFigure)
        #self._plotbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/zoom-in-5.png"), 'Not yet implemented: Zoom plot', self.zoomCurrentAxes)
        #self._plotbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/dlr-grid.png"), 'Grid on/off', self.setGridOnCurrentAxes)
        self._plotbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/dlr-subplot-add.png"), 'Add row to subplot', self.addRowToPlot)
        self._plotbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/dlr-subplot-remove.png"), 'Remove row from subplot', self.removeRowFromPlot)
        self._plotbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/view-right-new-3.png"), 'Add column to subplot', self.addColumnToPlot)
        self._plotbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/view-right-close.png"), 'Remove column from subplot', self.removeColumnFromPlot)

        self.mdi = QtGui.QMdiArea(self)
        self.mdi.setViewMode(QtGui.QMdiArea.TabbedView)
        self.setCentralWidget(self.mdi)
        self.mdi.subWindowActivated.connect(self._currentContainerChanged)

        self._newPlotContainer()
        self._currentContainerChanged()

        # Help should be the last menu item
        helpMenu = menu.addMenu("Help")
        helpMenu.addAction("Documentation", self.showHelp)
        helpMenu.addAction("About", self.showAbout)
        self.setMenuBar(menu)

    def _execAnalysisPlugin(self, func):
        if self.nvb.currentModelItem:
            func(self.models[self.nvb.currentModelItem.numberedModelName])
        else:
            print("No Model selected, unable to execute Plugin\n")

    def showHelp(self):
        os.startfile("file:///" + self.rootDir + "/Documentation/index.html")

    def showAbout(self):
        widget = QtGui.QDialog(self)
        widget.setWindowTitle("About PySimulator")
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Background, QtGui.QColor("white"))
        widget.setPalette(p)
        layout = QtGui.QGridLayout(widget)
        widget.setLayout(layout)
        pixmap = QtGui.QPixmap(self.rootDir + "/Icons/dlr-splash.png")
        iconLabel = QtGui.QLabel()
        iconLabel.setPixmap(pixmap)
        layout.addWidget(iconLabel, 0, 0)
        layout.addWidget(QtGui.QLabel("Copyright (C) 2011-2012 German Aerospace Center DLR (Deutsches Zentrum fuer Luft- und Raumfahrt e.V.),\nInstitute of System Dynamics and Control. All rights reserved.\n\nPySimulator is free software: you can redistribute it and/or modify\nit under the terms of the GNU Lesser General Public License as published by\nthe Free Software Foundation, either version 3 of the License, or\n(at your option) any later version.\n\nPySimulator is distributed in the hope that it will be useful,\nbut WITHOUT ANY WARRANTY; without even the implied warranty of\nMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the\nGNU Lesser General Public License for more details.\n\nYou should have received a copy of the GNU Lesser General Public License\nalong with PySimulator. If not, see www.gnu.org/licenses."), 1, 0)
        layout.addWidget(QtGui.QLabel("PySimulator Version: " + str(version)), 2, 0)
        button = QtGui.QPushButton("OK")
        button.clicked.connect(widget.close)
        layout.addWidget(button, 3, 0)
        widget.show()

    def zoomCurrentAxes(self):
        print("functionality temporarily not available\n")

    def setGridOnCurrentAxes(self):
        print("functionality temporarily not available\n")

    def saveFigure(self):
        ''' Exports the current window to an image '''
        if self.activePlotContainer and self.activePlot:
            rast = "rasterized images (*.png *.tiff *.bmp *.jpg *.jpeg *.gif)"
            pdf = "Portable Document Format (*.pdf)"
            svg = "Scalable Vector Graphics (*.svg *.html)"
            #(fileName, extension) = QtGui.QFileDialog().getSaveFileName(self, 'Save Plot as image', os.getcwd(), rast + ";;" + pdf + ";;" + svg)
            (fileName, extension) = QtGui.QFileDialog().getSaveFileName(self, 'Save Plot as image', os.getcwd(), rast)
            if not fileName:
                return
            if extension == rast:
                gc = chaco.plot_graphics_context.PlotGraphicsContext((self.activePlotContainer.activeWidget.width(), self.activePlotContainer.activeWidget.height()))
                gc.render_component(self.activePlotContainer.activeWidget.component)
                gc.save(fileName)
                print "Saved rasterized image to: ", fileName
                '''
                elif extension == pdf:
                    print "PDF rendering is currently in a unfinished state!"
                    __import__("chaco.pdf_graphics_context", globals(), locals(), [], -1)
                    gc = chaco.pdf_graphics_context.PdfPlotGraphicsContext(None, fileName, "A4")
                    gc.render_component(self.activePlotContainer.activeWidget.component)
                    gc.save()
                    print "Saved PDF to: ", fileName
                elif extension == svg:
                    __import__("chaco.svg_graphics_context", globals(), locals(), [], -1)
                    gc = chaco.svg_graphics_context.SVGGraphicsContext((self.activePlotContainer.activeWidget.width(), self.activePlotContainer.activeWidget.height()))
                    gc.render_component(self.activePlotContainer.activeWidget.component)
                    gc.save(fileName)
                    print "Saved SVG to: ", fileName
                '''
            else:
                print "File extension error. Unable to save image."
        else:
            print "Error saving plot. Plot type unknown or invalid"

    def addRowToPlot(self):
        ''' Adds a new row to the current subplot '''
        if self.activePlotContainer:
            self.activePlotContainer.addBottom(self, self.plotMenuCallbacks)

    def erasePlotCurrentAxes(self):
        print("functionality temporarily not available\n")

    def removeRowFromPlot(self):
        ''' Removes the last row from the current subplot '''
        print("functionality temporarily not available\n")

    def addColumnToPlot(self):
        ''' Adds a new column to the current subplot '''
        if self.activePlotContainer:
            self.activePlotContainer.addRight(self, self.plotMenuCallbacks)

    def removeColumnFromPlot(self):
        ''' Removes the last column of the current subplot '''
        print("functionality temporarily not available\n")

    def _currentPlotChanged(self, plot):
        if self.activePlot:
            for model, variable in self.activePlot.variables:
                self.nvb.checkVariable(model, variable, False)
        if plot:
            for model, variable in plot.variables:
                    self.nvb.checkVariable(model, variable, True)
        self.activePlot = plot

    def _currentContainerChanged(self):
        children = self.mdi.currentSubWindow().findChildren(plotWidget.plotContainer)
        if children:
            self.activePlotContainer = children[0]
            self._currentPlotChanged(self.activePlotContainer.activeWidget)
        else:
            self.activePlotContainer = None
            self._currentPlotChanged(None)

    def openModelFile(self, loaderplugin, fileName, modelName=None):
        if fileName == '':
            return
        if modelName is None:
            sp = string.rsplit(fileName, '.', 1)
            modelName = string.rsplit(sp[0], '/', 1)[1]
        model = loaderplugin.Model(modelName, str(fileName))
        self._newModel(model)

    def _openFileMenu(self, loaderplugin):
        extensionStr = ''
        for ex in loaderplugin.modelExtension:
            extensionStr += '*.' + ex + ';'
        if len(extensionStr) > 0:
            extensionStr = extensionStr[:-1]
        ''' Load a model '''
        (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open Model', os.getcwd(), extensionStr)
        fileName = str(fileName)
        if fileName == '':
            return
        split = string.rsplit(fileName, '.', 1)
        if len(split) > 1:
            suffix = split[1]
        else:
            suffix = ''
        modelName = None
        if suffix in ['mo', 'moe']:
            if len(split[0]) > 0:
                split = string.rsplit(split[0], '/', 1)
                defaultModelName = split[1]
            else:
                defaultModelName = ''
            modelName, ok = QtGui.QInputDialog().getText(self, 'Modelica model', 'Modelica model name', text=defaultModelName)
            if not ok:
                return
            modelName = str(modelName)

        self.setEnabled(False)
        self._loadingFileInfo()
        self.openModelFile(loaderplugin, fileName, modelName)
        self.setEnabled(True)

    def openResultFile(self, fileName):
        ''' Load a result file and display variables in variable browser '''
        
        import Plugins.Simulator.SimulatorBase        
        if fileName == '':
            return

        self.setEnabled(False)
        self._loadingFileInfo()
        sp = string.rsplit(fileName, '.', 1)
        modelName = string.rsplit(sp[0], '/', 1)[1]
        model = Plugins.Simulator.SimulatorBase.Model(modelName, None, 'None')
        model.loadResultFile(fileName)
        model.integrationResultFileSemaphore = threading.Semaphore()
        self._newModel(model)
        self.setEnabled(True)

    def _openResultFileMenu(self):
        ''' Load a Result file '''
        (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Open Result File', os.getcwd(), 'MA Time Series File Format (*.mtsf);;Dymola Result File (*.mat)')
        fileName = str(fileName)
        self.openResultFile(fileName)

    
    def _loadingFileInfo(self):
        ''' Shows a label 'Loading file...' '''
        w = QtGui.QWidget(None)
        w.resize(300, 100)
        w.move(self.pos().x() + self.size().width() / 2 - 300 / 2, self.pos().y() + self.size().height() / 2 - 100 / 2)
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Background, QtGui.QColor("white"))
        w.setPalette(p)
        l = QtGui.QLabel(w)
        l.setText("<b>Loading file...</b>")
        l.move(50, 50)
        w.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        w.show()
        app = QtGui.QApplication.instance()
        app.processEvents()
        
    
    def _convertResultFileMenu(self):
        ''' Select a result file '''
        (fileName, trash) = QtGui.QFileDialog().getOpenFileName(self, 'Select Result File', os.getcwd(), 'Dymola Result File (*.mat)')
        fileName = str(fileName)
        if fileName == '':
            return
        print("Convert " + fileName + " ...")                 
        mtsfFileName = Plugins.SimulationResult.Mtsf.Mtsf.convertFromDymolaMatFile(fileName)
        print(" done: " + mtsfFileName + "\n")

    def _showIntegratorControl(self):
        ''' Show the Integrator Control window and connect its signals.  '''
        if len(self.models) == 0:
            print("No models opened!\n")
        else:
            currentModelName = str(self.nvb.currentModelItem.text(0))
            if self.models[currentModelName].modelType != 'None':
                self.simulateAction.setDisabled(True)
                self.ic = IntegratorControl.IntegratorControl(self, self.models)
                self.ic.show()
                #self.ic.printText.connect(print)
                self.ic.resultsUpdated.connect(self._resultsUpdated)
                self.ic.reallyFinished.connect(self._finishIntegratorControl)
            else:
                print("Only result file opened, no model existing that can be simulated!\n")

    def _finishIntegratorControl(self):
        self.simulateAction.setEnabled(True)
        del(self.ic)

    def _newPlotContainer(self):
        ''' Create a new plot and add it to the current tab '''
        plotContainer = plotWidget.plotContainer(self.mdi)
        #defaultWidget = plotWidget.DefaultPlotWidget(self, self.plotMenuCallbacks)
        #plotContainer.addRight(defaultWidget)
        plotContainer.addFirst(self, self.plotMenuCallbacks)
        self.plotContainers.append(plotContainer)
        plotContainer.activeWidgetChanged.connect(self._currentPlotChanged)
        plotContainer.closed.connect(self._removePlotContainer)
        window = self.mdi.addSubWindow(plotContainer)
        self.plotWindowNr += 1
        window.setWindowTitle("Tab " + str(self.plotWindowNr))
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Background, QtGui.QColor("white"))
        window.setPalette(p)
        window.setWindowIcon(QtGui.QIcon(self.rootDir + '/Icons/office-chart-line-stacked.png'))
        window.showMaximized()
        return plotContainer

    def _removePlotContainer(self, container):
        self.plotContainers.remove(container)

    def _resultsUpdated(self, modelName):
        ''' Redraw all relevant plots when ever new data is available
        '''
        for container in self.plotContainers:
            for plotw in container.findChildren(plotWidget.PlotWidget):
                for var in (x[1] for x in plotw.variables if x[0] == self.models[modelName]):
                    plotw.updateVariable(self.models[modelName], var)

    def _variableCheckChanged(self, item):
        ''' This function is normally called  when the user checks/unchecks a
            tree item in the variables browser. The corresponding line will be
            shown resp. removed.
        '''
        if self.activePlot:
            if item.checkState(0) == QtCore.Qt.Checked:
                self.activePlot.addVariable(self.models[item.modelName], item.variable)
            else:
                self.activePlot.removeVariable(self.models[item.modelName], item.variable)
        else:
            item.setCheckState(0, (QtCore.Qt.Unchecked))

    def _removeLinesByModel(self, model):
        varList = []
        # Do NOT delete the lines in the following first loop, because plotw is changed by plotw.removeVariable -> undefined behaviour
        
        # First, search for all variables of the model plotted in widgets 
        for container in self.plotContainers:
            for plotw in container.findChildren(plotWidget.PlotWidget):               
                for var in (x[1] for x in plotw.variables if x[0].numberedModelName == model.numberedModelName):                        
                    varList.append([plotw, var])
                    
        # Now delete the lines
        for v in varList:
            v[0].removeVariable(model, v[1])
                    

    def setNumberedStuff(self, model):
        ''' Set the numbered model name and the corresponding result file name '''        
        currentNumber = 0
        for m in self.models.values():
            currentNumber = max(currentNumber, int(m.numberedModelName.split(':', 1)[0]))
        number = currentNumber + 1       
        model.numberedModelName = '%01i:' % number + model.name
        model.integrationSettings.resultFileName = str(model.name) + '_%01i' % number + '.' + model.integrationSettings.resultFileExtension

    def _newModel(self, model):
        ''' Handles to add a new given model into the framework '''
        # Set the numbered model name
        self.setNumberedStuff(model)
        # Set default values for GUI realted topics
        model.integrationSettings.plotOnline_isChecked = True
        model.integrationSettings.duplicateModel_isChecked = False
        model.integrationStatistics.finished = True
        # Include the model in the model dictionary
        self.models[model.numberedModelName] = model
        # Add the model to the variables browser
        self.nvb.addModel(model)

    def duplicateModel(self, modelName):
        ''' Duplicates the given model '''
        model = self.models[modelName]
        if model.modelType == 'None':
            print('Duplicating a result file is not supported.')
            return
        model2 = model.duplicate()
        self._newModel(model2)
        return model2

    def closeModel(self, numberedModelName):
        ''' Removes the given model '''
        # Check if closing the model is allowed
        if not self.models[numberedModelName].integrationStatistics.finished:
            # A simulation is still running
            return
        # Delete the corresponding tree in the variable browser
        self.nvb.removeModel(self.models[numberedModelName])
        # Delete the corresponding lines and information in the plot windows
        self._removeLinesByModel(self.models[numberedModelName])
        # Close the result file (if any)
        try:
            self.models[numberedModelName].integrationResults.close()
        except:
            pass
        # Delete the model itself:
        self.models[numberedModelName].close()
        del self.models[numberedModelName]

    def _variableValueChanged(self, numberedModelName, variableName, value):
        ''' The user entered a new value for a variable in the variable browser.
            Store this information in the model. '''
        print('Variable value changed: %s: %s = %s\n' % (numberedModelName, variableName, value))
        self.models[str(numberedModelName)].changedStartValue[variableName] = value
        # Delete pluginData because values of parameters have been changed
        self.models[str(numberedModelName)].pluginData.clear()

    def closeEvent(self, event):
        for pluginName, plugin in self.simulatorPlugins.items():  # and self.analysisPlugins
            try:
                plugin.closeSimulatorPlugin()
                print "Closed Simulator Plugin " + pluginName
            except:
                print "Closing of Simulator Plugin " + pluginName + " failed."
        sys.stdout = self._origStdout


class WindowConsole(QtGui.QWidget):
    ''' Class to write stdout prints to the QTextEdit textField  '''

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QGridLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.out = QtGui.QTextEdit(self)
        self.layout().addWidget(self.out, 0, 0)
        self.out.setStyleSheet("QTextEdit { background-color: white; color: black; font-weight: normal; }")
        self.out.setReadOnly(True)
        self.input = QtGui.QLineEdit()
        self.layout().addWidget(self.input, 1, 0)
        self.consoleAccessMutex = QtCore.QMutex()

    def write(self, text):
        self.consoleAccessMutex.lock()
        self.out.setUpdatesEnabled(False)
        cursor = self.out.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
        # Set Cursor to the end of the visible text
        self.out.setTextCursor(cursor)
        # Insert the given text at this position
        self.out.insertPlainText(text)
        #self.textField.insertHtml(text)
        self.update()
        self.out.setUpdatesEnabled(True)
        self.consoleAccessMutex.unlock()
        # Process event to see the printed message immediatly
        app = QtGui.QApplication.instance()
        app.processEvents()


''' Just launches the application
'''
if __name__ == "__main__":
    runBenchmark = False
    app = QtGui.QApplication.instance()
    if not app:
        app = QtGui.QApplication([])

    pixmap = QtGui.QPixmap(os.path.abspath(os.path.dirname(__file__)) + "/Icons/dlr-splash.png")
    splash = QtGui.QSplashScreen(pixmap)
    splash.show()
    app.processEvents()

    splash.showMessage("Loading External dependencies...")
    # modified import statements, allowing them to be processed inside this function and make them globally available
    globals()["QtCore"] = __import__("PySide", globals(), locals(), ["QtCore"], -1).QtCore
    globals()["ETSConfig"] = __import__("traits.etsconfig.etsconfig", globals(), locals(), ["ETSConfig"], -1).ETSConfig
    ETSConfig.toolkit = "qt4"
    globals()["chaco"] = __import__("chaco", globals(), locals(), [], -1)
    globals()["string"] = __import__("string", globals(), locals(), [], -1)
    globals()["threading"] = __import__("threading", globals(), locals(), [], -1)
    globals()["os"] = __import__("os", globals(), locals(), [], -1)
    globals()["re"] = __import__("re", globals(), locals(), [], -1)
    globals()["sys"] = __import__("sys", globals(), locals(), [], -1)
    globals()["VariablesBrowser"] = __import__("VariablesBrowser", globals(), locals(), [], -1)
    globals()["IntegratorControl"] = __import__("IntegratorControl", globals(), locals(), [], -1)
    globals()["plotWidget"] = __import__("plotWidget", globals(), locals(), [], -1)
    globals()["IntegratorControl"] = __import__("IntegratorControl", globals(), locals(), [], -1)
    globals()["Plugins"] = __import__("Plugins", globals(), locals(), [], -1)
    globals()["partial"] = __import__("functools", globals(), locals(), ["partial"], -1).partial
    import compileall

    splash.showMessage("Loading PySimulator...")
    compileall.compile_dir(os.getcwd(), force=True, quiet=True, rx=re.compile('/[.]svn'))
    sg = SimulatorGui()
    sg.show()
    splash.finish(sg)

    if runBenchmark:
        #shows a benchmark including the time spent in diffrent routines during execution
        import cProfile
        cProfile.run('app.exec_()', 'logfile')
        import pstats
        p = pstats.Stats('logfile')
        p.strip_dirs().sort_stats('cumulative').print_stats()
    else:
        app.exec_()
