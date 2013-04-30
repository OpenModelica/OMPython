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

from PySide import QtGui, QtCore
import threading
import types

import os
import math
import gc
import time

import Plugins.Simulator.SimulatorBase


class IntegratorControl(QtGui.QDialog):
    ''' Class for the Integrator Control GUI '''

    ''' Signals of the class  '''
    resultsUpdated = QtCore.Signal(types.StringType)
    reallyFinished = QtCore.Signal()
    SimulationFinished = QtCore.Signal(types.BooleanType)

    def __init__(self, parent, models=None):
        self.models = models
        self.parent = parent

        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Integrator Control")

        _mainGrid = QtGui.QGridLayout(self)

        _numIn = QtGui.QGroupBox("Numerical Integration", self)
        _mainGrid.addWidget(_numIn, 0, 0)
        _numInLayout = QtGui.QGridLayout()
        _numIn.setLayout(_numInLayout)

        _numInLayout.addWidget(QtGui.QLabel("Time in s:"), 0, 0)
        self.timeFrom = QtGui.QLineEdit(self)
        self.timeFrom.setValidator(QtGui.QDoubleValidator(-1e9, 1e9, 15, self))
        _numInLayout.addWidget(self.timeFrom, 0, 1)
        _numInLayout.addWidget(QtGui.QLabel("      to"), 0, 2)
        self.timeTo = QtGui.QLineEdit(self)
        self.timeTo.setValidator(QtGui.QDoubleValidator(-1e9, 1e9, 15, self))
        _numInLayout.addWidget(self.timeTo, 0, 3)

        _numInLayout.addWidget(QtGui.QLabel("Algorithm:"), 1, 0)
        self.algorithm = QtGui.QComboBox(self)
        _numInLayout.addWidget(self.algorithm, 1, 1, 1, 3)

        _numInLayout.addWidget(QtGui.QLabel("Error tolerance: "), 2, 0)
        self.errorTol = QtGui.QLineEdit(self)
        _errorValid = QtGui.QDoubleValidator(0, 10, 20, self)
        _errorValid.setNotation(QtGui.QDoubleValidator.ScientificNotation)
        self.errorTol.setValidator(_errorValid)
        _numInLayout.addWidget(self.errorTol, 2, 1)

        _numInLayout.addWidget(QtGui.QLabel("Step size: "), 2, 2)
        self.stepSize = QtGui.QLineEdit(self)
        _stepSizeValid = QtGui.QDoubleValidator(0, 10, 20, self)
        _stepSizeValid.setNotation(QtGui.QDoubleValidator.ScientificNotation)
        self.stepSize.setValidator(_stepSizeValid)
        self.stepSize.setEnabled(False)
        _numInLayout.addWidget(self.stepSize, 2, 3)

        _results = QtGui.QGroupBox("Results", self)
        _mainGrid.addWidget(_results, 1, 0)
        _resultsLayout = QtGui.QGridLayout()
        _results.setLayout(_resultsLayout)

        self.inTime = QtGui.QRadioButton("Equidistant grid points in time", self)
        self.inTime.setChecked(True)
        _resultsLayout.addWidget(self.inTime, 0, 0, 1, 2)
        self.inTimeVal = QtGui.QLineEdit(self)
        self.inTimeVal.setValidator(QtGui.QDoubleValidator(2, 1.e9, 0, self))
        _resultsLayout.addWidget(self.inTimeVal, 0, 2)

        self.perTime = QtGui.QRadioButton("Width of equidistant time grid", self)
        _resultsLayout.addWidget(self.perTime, 1, 0, 1, 2)
        self.perTimeVal = QtGui.QLineEdit(self)
        self.perTimeVal.setValidator(QtGui.QDoubleValidator(0, 1.e9, 15, self))
        _resultsLayout.addWidget(self.perTimeVal, 1, 2)
        self.useIntegratorGrid = QtGui.QRadioButton("Use integrator steps for grid points", self)
        _resultsLayout.addWidget(self.useIntegratorGrid, 2, 0, 1, 3)
        _resultsLayout.addItem(QtGui.QSpacerItem(0, 30))

        self.plot = QtGui.QCheckBox("Plot online during numerical integration", self)
        _resultsLayout.addWidget(self.plot, 3, 0, 1, 3)

        saveFile = QtGui.QLabel("Save results in:", self)
        _resultsLayout.addWidget(saveFile, 4, 0, QtCore.Qt.AlignRight)
        _browseSaveFile = QtGui.QPushButton("Select", self)
        _resultsLayout.addWidget(_browseSaveFile, 4, 3)
        self.saveFilePath = QtGui.QLineEdit("", self)
        _resultsLayout.addWidget(self.saveFilePath, 4, 1, 1, 2)

        _control = QtGui.QGroupBox("Control", self)
        _mainGrid.addWidget(_control, 2, 0)
        _controlLayout = QtGui.QGridLayout()
        _control.setLayout(_controlLayout)

        self.run = QtGui.QPushButton("Run", self)
        _controlLayout.addWidget(self.run, 0, 0)
        self.stop = QtGui.QPushButton("Stop", self)
        _controlLayout.addWidget(self.stop, 0, 1)
        self.closebutton = QtGui.QPushButton("Close", self)
        _controlLayout.addWidget(self.closebutton, 0, 2)
        self._duplicateModelCheck = QtGui.QCheckBox("Duplicate model after simulation", self)
        _controlLayout.addWidget(self._duplicateModelCheck, 1, 0, 1, 2)

        _simulationInfo = QtGui.QGroupBox("Simulation info", self)
        _mainGrid.addWidget(_simulationInfo, 3, 0)
        _simulationInfoLayout = QtGui.QGridLayout()
        _simulationInfo.setLayout(_simulationInfoLayout)

        label = QtGui.QLabel('Model name:')
        label.setAlignment(QtCore.Qt.AlignRight)
        _simulationInfoLayout.addWidget(label, 0, 0)
        label = QtGui.QLabel('Current time:')
        label.setAlignment(QtCore.Qt.AlignRight)
        _simulationInfoLayout.addWidget(label, 1, 0)
        label = QtGui.QLabel('Time events:')
        label.setAlignment(QtCore.Qt.AlignRight)
        _simulationInfoLayout.addWidget(label, 2, 0)
        label = QtGui.QLabel('State events:')
        label.setAlignment(QtCore.Qt.AlignRight)
        _simulationInfoLayout.addWidget(label, 3, 0)
        label = QtGui.QLabel('Result points:')
        label.setAlignment(QtCore.Qt.AlignRight)
        _simulationInfoLayout.addWidget(label, 4, 0)
        label = QtGui.QLabel('Result file size:')
        label.setAlignment(QtCore.Qt.AlignRight)
        _simulationInfoLayout.addWidget(label, 5, 0)
        label = QtGui.QLabel('Result file name:')
        label.setAlignment(QtCore.Qt.AlignRight)
        _simulationInfoLayout.addWidget(label, 6, 0)
        label = QtGui.QLabel('Elapsed real time:')
        label.setAlignment(QtCore.Qt.AlignRight)
        _simulationInfoLayout.addWidget(label, 7, 0)

        self.currentModelLabel = QtGui.QLabel('')
        _simulationInfoLayout.addWidget(self.currentModelLabel, 0, 1, 1, 3)
        self.showedTimeLabel = QtGui.QLabel('')
        _simulationInfoLayout.addWidget(self.showedTimeLabel, 1, 1)
        self.currentTimeProgress = QtGui.QProgressBar()
        self.currentTimeProgress.setRange(0, 100)
        self.currentTimeProgress.setMaximumHeight(13)
        _simulationInfoLayout.addWidget(self.currentTimeProgress, 1, 2, 1, 2)
        self.showedTimeEvents = QtGui.QLabel('')
        _simulationInfoLayout.addWidget(self.showedTimeEvents, 2, 1, 1, 3)
        self.showedStateEvents = QtGui.QLabel('')
        _simulationInfoLayout.addWidget(self.showedStateEvents, 3, 1, 1, 3)
        self.showedGridPoints = QtGui.QLabel('')
        _simulationInfoLayout.addWidget(self.showedGridPoints, 4, 1, 1, 3)
        self.filesizeLabel = QtGui.QLabel('')
        _simulationInfoLayout.addWidget(self.filesizeLabel, 5, 1, 1, 3)
        self.realResultFileNameEdit = QtGui.QLineEdit('', self)
        self.realResultFileNameEdit.setFrame(False)
        self.realResultFileNameEdit.setReadOnly(True)
        self.realResultFileNameEdit.setMaximumHeight(13)
        pal = self.realResultFileNameEdit.palette()
        pal.setColor(self.realResultFileNameEdit.backgroundRole(), QtCore.Qt.transparent)
        self.realResultFileNameEdit.setPalette(pal)
        _simulationInfoLayout.addWidget(self.realResultFileNameEdit, 6, 1, 1, 3)
        self.realtimeLabel = QtGui.QLabel('')
        _simulationInfoLayout.addWidget(self.realtimeLabel, 7, 1, 1, 3)

        self.run.setFocus()

        def _resultTypeChanged():
            if self.inTime.isChecked():
                self.inTimeVal.setEnabled(True)
                self.perTimeVal.setEnabled(False)
            if self.perTime.isChecked():
                self.inTimeVal.setEnabled(False)
                self.perTimeVal.setEnabled(True)
            if self.useIntegratorGrid.isChecked():
                self.inTimeVal.setEnabled(False)
                self.perTimeVal.setEnabled(False)

        def _plotOnlineChanged():
            self.models[self.currentNumberedModelName].integrationSettings.plotOnline_isChecked = self.plot.isChecked()

        def _browseSaveFileDo():
            (fileName, trash) = QtGui.QFileDialog().getSaveFileName(self, 'Save results', os.getcwd(), 'MA Time Series Result File (*.mtsf)')
            fileName = str(fileName)
            if fileName != '':
                self.saveFilePath.setText(fileName)

        self.algorithm.currentIndexChanged.connect(self._algoChanged)
        self.inTime.toggled.connect(_resultTypeChanged)
        self.perTime.toggled.connect(_resultTypeChanged)
        self.useIntegratorGrid.toggled.connect(_resultTypeChanged)

        _browseSaveFile.clicked.connect(_browseSaveFileDo)

        self.run.clicked.connect(self._simulate)
        self.stop.clicked.connect(self._stopSimulation)
        self.closebutton.clicked.connect(self._close)

        self.stop.setEnabled(False)
        self.currentNumberedModelName = None
        self.changeCurrentModel()
        self.parent.nvb.currentModelChanged.connect(self.changeCurrentModel)

        if self.models[self.currentNumberedModelName].integrationResults.canLoadPartialData:
            self.plot.setCheckState(QtCore.Qt.Checked)
        else:
            self.plot.setEnabled(False)
            self.plot.setCheckState(QtCore.Qt.Unchecked)
        self.plot.toggled.connect(_plotOnlineChanged)

        self.SimulationFinished.connect(self.triggerdResultUpdate)

    def _algoChanged(self, item):
        if self.models[self.currentNumberedModelName].getIntegrationAlgorithmHasFixedStepSize(self.algorithm.currentText()):
            self.errorTol.setEnabled(False)
            self.stepSize.setEnabled(True)
        else:
            self.errorTol.setEnabled(True)
            self.stepSize.setEnabled(False)
        if self.models[self.currentNumberedModelName].getIntegrationAlgorithmCanProvideStepSizeResults(self.algorithm.currentText()):
            self.useIntegratorGrid.setEnabled(True)
        else:
            if self.useIntegratorGrid.isChecked():
                self.inTime.setChecked(True)
            self.useIntegratorGrid.setEnabled(False)

    def reject(self):
        ''' Overload the standard reject function to not close the GUI
            when ESC is pressed '''
        pass

    def closeEvent(self, event):
        #print "Close event"
        if not self.closebutton.isEnabled():
            # Prevent closing the GUI when a simulation is running
            event.ignore()
        else:
            self.parent.nvb.currentModelChanged.disconnect(self.changeCurrentModel)
            self.reallyFinished.emit()

    def changeCurrentModel(self):
        #print "Change current model in IntegratorControl"
        # Only change the current model if it is not being simulated
        if self.currentNumberedModelName is not None:
            if not self.models[self.currentNumberedModelName].integrationStatistics.finished:
                return
        # Get the tree item of the new selected model
        item = self.parent.nvb.currentModelItem
        if item is None:
            # There is no current model in the variables browser (no model loaded)
            # Close the GUI
            self._close()
            return
        modelName = str(item.text(0))
        if modelName == self.currentNumberedModelName:
            return

        # Before changing the current model, save the integrator settings to the model
        self._setSettingsFromIntegratorControlGUI(self.currentNumberedModelName)
        self.currentNumberedModelName = modelName
        if self.models[modelName].modelType == 'None':
            self._close()
            return
        self._setIntegratorControlGUIFromSettings(self.currentNumberedModelName)

    def _close(self):
        self._setSettingsFromIntegratorControlGUI(self.currentNumberedModelName)
        self.close()

    def _setSettingsFromIntegratorControlGUI(self, modelName):
        ''' Stores the settings of the GUI into the model  '''
        if modelName is None:
            return
        if modelName == '':
            return
        if modelName not in self.models.keys():
            return
        model = self.models[modelName]
        model.integrationSettings.startTime = float(self.timeFrom.text())
        model.integrationSettings.stopTime = float(self.timeTo.text())
        model.integrationSettings.algorithmName = str(self.algorithm.currentText())
        model.integrationSettings.errorToleranceRel = float(self.errorTol.text())
        model.integrationSettings.fixedStepSize = float(self.stepSize.text())
        model.integrationSettings.gridPoints = int(float(self.inTimeVal.text()))
        model.integrationSettings.gridWidth = float(self.perTimeVal.text())
        if self.inTime.isChecked():
            model.integrationSettings.gridPointsMode = 'NumberOf'
        elif self.perTime.isChecked():
            model.integrationSettings.gridPointsMode = 'Width'
        else:
            model.integrationSettings.gridPointsMode = 'Integrator'
        model.integrationSettings.resultFileName = str(self.saveFilePath.text())
        model.integrationSettings.plotOnline_isChecked = self.plot.isChecked()
        model.integrationSettings.duplicateModel_isChecked = self._duplicateModelCheck.isChecked()

    def _setIntegratorControlGUIFromSettings(self, modelName):
        ''' Shows the settings of the model in the GUI  '''
        model = self.models[modelName]

        self.timeFrom.setText(str(model.integrationSettings.startTime))
        self.timeTo.setText(str(model.integrationSettings.stopTime))
        self.algorithm.currentIndexChanged.disconnect()
        self.algorithm.clear()
        self._itemList = model.getAvailableIntegrationAlgorithms()
        self.algorithm.addItems(self._itemList)
        self.algorithm.currentIndexChanged.connect(self._algoChanged)
        self.algorithm.setCurrentIndex(self._itemList.index(model.integrationSettings.algorithmName))
        self.errorTol.setText(str(model.integrationSettings.errorToleranceRel))
        self.stepSize.setText(str(model.integrationSettings.fixedStepSize))
        self.inTimeVal.setText(str(model.integrationSettings.gridPoints))
        self.useIntegratorGrid.setEnabled(model.getIntegrationAlgorithmCanProvideStepSizeResults(model.integrationSettings.algorithmName))
        if model.integrationSettings.gridPointsMode == 'NumberOf':
            self.inTime.setChecked(True)
            self.inTimeVal.setEnabled(True)
            self.perTimeVal.setEnabled(False)
        elif model.integrationSettings.gridPointsMode == 'Width':
            self.perTime.setChecked(True)
            self.inTimeVal.setEnabled(False)
            self.perTimeVal.setEnabled(True)
        else:
            self.useIntegratorGrid.setChecked(True)
            self.inTimeVal.setEnabled(False)
            self.perTimeVal.setEnabled(False)
        self.perTimeVal.setText(str(model.integrationSettings.gridWidth))
        self.saveFilePath.setText(model.integrationSettings.resultFileName)
        self.plot.setEnabled(self.models[self.currentNumberedModelName].integrationResults.canLoadPartialData)
        self.plot.setCheckState(QtCore.Qt.Checked if model.integrationSettings.plotOnline_isChecked else QtCore.Qt.Unchecked)
        self._duplicateModelCheck.setCheckState(QtCore.Qt.Checked if model.integrationSettings.duplicateModel_isChecked else QtCore.Qt.Unchecked)
        self.currentModelLabel.setText(modelName)
        self.showTimeLabelAndProgress(model.integrationSettings, model.integrationStatistics, True)
        self.showedTimeEvents.setText(str(model.integrationStatistics.nTimeEvents) if model.integrationStatistics.nTimeEvents is not None else '')
        self.showedStateEvents.setText(str(model.integrationStatistics.nStateEvents) if model.integrationStatistics.nStateEvents is not None else '')
        self.showedGridPoints.setText(str(model.integrationStatistics.nGridPoints) if model.integrationStatistics.nGridPoints is not None else '')
        self.filesizeLabel.setText(self.fileSize2str(model.integrationResults.fileSize()))
        self.realResultFileNameEdit.setText(model.integrationResults.fileName)

    def fileSize2str(self, size):
        if size is not None:
            if size > 1024:
                return format(size/1024, '0.1f') + ' GB'
            else:
                return format(size, '0.1f') + ' MB'
        else:
            return ''

    def showTimeLabelAndProgress(self, settings, statistics, lastCall=False):
        ''' Shows the current time and corresponding progress bar in simulation info '''
        # Current Time
        if statistics.reachedTime is None:
            currentTimeText = ''
        else:
            if lastCall:
                formatString = '0.14g'
                currentTimeText = format(statistics.reachedTime, formatString)
            else:
                # Current time: The number of showed digits depends on the difference
                #               to the last shown time. The effect is that you can
                #               see, if the simulation is slowing down in time
                #               but without displaying to much digits for fast sections.
                difference = statistics.reachedTime - self.lastCurrentTime
                self.lastCurrentTime = statistics.reachedTime
                if difference > 0.0:
                    nDigits = int(abs(min(0, math.log10(difference) - 1)))
                    formatString = '0.' + str(nDigits) + 'f'
                else:
                    nDigits = 14
                    formatString = '0.' + str(nDigits) + 'g'
                currentTimeText = format(math.floor(math.pow(10,nDigits)*statistics.reachedTime)/math.pow(10,nDigits), formatString)
            
            if len(currentTimeText) > 0:
                currentTimeText += ' s'
        self.showedTimeLabel.setText(currentTimeText)

        # Progress bar
        if statistics.reachedTime is None:
            progressBarTimeValue = settings.startTime
        else:
            progressBarTimeValue = statistics.reachedTime
            if lastCall:
                progressBarTimeValue = settings.stopTime

        a = settings.startTime
        b = settings.stopTime
        if b - a == 0.0:
            b = a + 1
        steps = (progressBarTimeValue - a) / (b - a) * (self.currentTimeProgress.maximum() - self.currentTimeProgress.minimum())
        self.currentTimeProgress.setValue(steps)
        # CPU time
        if hasattr(self, '_cpuStartTime'):
            statistics.cpuTime = time.clock() - self._cpuStartTime
        if statistics.cpuTime is not None:
            self.realtimeLabel.setText("%.2f s" % statistics.cpuTime)
        else:
            self.realtimeLabel.setText('')

    def _simulate(self):
        ''' Starts the simulation of the current model with the current settings in the GUI '''
        self.models[self.currentNumberedModelName].integrationStatistics.finished = False
        self.run.setEnabled(False)
        self.closebutton.setEnabled(False)
        # Delete pluginData because new simulation will start
        self.models[self.currentNumberedModelName].pluginData.clear()
        self._setSettingsFromIntegratorControlGUI(self.currentNumberedModelName)
        # Close the corresponding result file to have write access
        self.models[self.currentNumberedModelName].integrationResults.close()
        try:
            os.remove(self.models[self.currentNumberedModelName].integrationResults.fileName)
        except:
            pass

        self.models[self.currentNumberedModelName].integrationResultFileSemaphore = threading.Semaphore()
        if hasattr(self.models[self.currentNumberedModelName], 'integrationResults'):
            self.models[self.currentNumberedModelName].integrationResults.fileName = ''

        # Define some variables before simulation can start
        self.models[self.currentNumberedModelName].integrationStatistics.cpuTime = None
        self.models[self.currentNumberedModelName].integrationStatistics.nTimeEvents = 0
        self.models[self.currentNumberedModelName].integrationStatistics.nStateEvents = 0
        self.models[self.currentNumberedModelName].integrationStatistics.nGridPoints = 0
        self.models[self.currentNumberedModelName].integrationStatistics.reachedTime = self.models[self.currentNumberedModelName].integrationSettings.startTime

        # Define Timers for result updates and simulation info updates
        self.updateData = QtCore.QTimer()
        self.updateData.timeout.connect(self.triggerdResultUpdate)

        self.updateSimulationInfo = QtCore.QTimer()
        self.updateSimulationInfo.timeout.connect(self.showSimulationInfo)

        # Define a new thread for the simulation task
        self._simThread = simulationThread(self)

        self._simThread.model = self.models[self.currentNumberedModelName]
        self._simThread.model.simulationStopRequest = False

        self.lastCurrentTime = self._simThread.model.integrationStatistics.reachedTime
        self.showSimulationInfo()

        # Start the timers and the simulation thread
        self._simThread.SimulationFinished = self.SimulationFinished
        self.updateData.start(1000)
        self.updateSimulationInfo.start(500)
        self._cpuStartTime = time.clock()
        self.stop.setEnabled(True)
        self._simThread.start(QtCore.QThread.LowPriority)

    def showSimulationInfo(self, lastCall=False):
        ''' Shows the updated simulation information in the Integrator Control GUI '''

        model = self.models[self.currentNumberedModelName]
        # File size of result file
        fileSizeText = self.fileSize2str(model.integrationResults.fileSize())
        self.filesizeLabel.setText(fileSizeText)

        if not lastCall:
            model.integrationStatistics.reachedTime = model.getReachedSimulationTime()

        self.showTimeLabelAndProgress(model.integrationSettings, model.integrationStatistics, lastCall)

        # Number of events and grid points
        self.showedTimeEvents.setText(str(model.integrationStatistics.nTimeEvents))
        self.showedStateEvents.setText(str(model.integrationStatistics.nStateEvents))
        self.showedGridPoints.setText(str(model.integrationStatistics.nGridPoints))

        self.realResultFileNameEdit.setText(model.integrationResults.fileName)

    def _stopSimulation(self):
        ''' Stops the current simulation '''
        if '_simThread' in self.__dict__ and self._simThread.isRunning():
            print('try to stop integration ... ')
            self._simThread.model.simulationStopRequest = True

    def triggerdResultUpdate(self, lastCall=False):
        ''' This function is normally called when updated results shall be plotted '''
        if not self._simThread.isRunning() or lastCall:
            # The numerical integration is not running any more
            # Stop the timers
            self.updateData.stop()
            self.updateSimulationInfo.stop()
            # Close the result file to guarantee that all results are on file
            self.models[self.currentNumberedModelName].integrationResultFileSemaphore.acquire()
            self.models[self.currentNumberedModelName].integrationResults.close()
            self.models[self.currentNumberedModelName].integrationResultFileSemaphore.release()
            print("Results saved in " + self.models[self.currentNumberedModelName].integrationSettings.resultFileName + ".")

            # Re-open result file for further plotting
            self.models[self.currentNumberedModelName].integrationResultFileSemaphore.acquire()
            self.models[self.currentNumberedModelName].loadResultFile(self.models[self.currentNumberedModelName].integrationSettings.resultFileName)
            self.models[self.currentNumberedModelName].integrationResultFileSemaphore.release()

            # Show the correct simulation information
            self.showSimulationInfo(lastCall=True)
            if hasattr(self, '_cpuStartTime'):
                del(self._cpuStartTime)

            if self._simThread.model.simulationStopRequest:
                print("Integration stopped.")
            else:
                print("Integration completed.")

            self.resultsUpdated.emit(self.currentNumberedModelName)

            # Enable run and close buttons of Integrator menu
            self.run.setEnabled(True)
            self.closebutton.setEnabled(True)
            self.stop.setEnabled(False)

            # Duplicate model after simulation if selected
            if self._duplicateModelCheck.isChecked():
                self.parent.duplicateModel(self.currentNumberedModelName)

            self.models[self.currentNumberedModelName].integrationStatistics.finished = True

            # Check if the selection of the current model has changed during integration
            self.changeCurrentModel()
            gc.collect()

        else:
            # During integration: Send signal that results are updated, if selected and possible
            if self.models[self.currentNumberedModelName].integrationSettings.plotOnline_isChecked:
                self.resultsUpdated.emit(self.currentNumberedModelName)


class simulationThread(QtCore.QThread):
    ''' Class for the simulation thread '''
    def __init__(self, parent):
        super(simulationThread, self).__init__(parent)

    def run(self):
        try:
            '''
            Do the numerical integration in a try branch
            to avoid loosing the thread when an intended exception is raised
            '''
            self.model.simulate()            
        except Plugins.Simulator.SimulatorBase.Stopping:
            print("solver canceled ... ")
        #except Exception, e:
        #    print("unexpected error ... ")
        #    print e

        # Define simulation completed to stop updating plots and come back to the GUI
        self.SimulationFinished.emit(True)

