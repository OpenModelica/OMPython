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


import types
from PySide import QtGui, QtCore
import functools


class VariablesBrowser(QtGui.QTreeWidget):
    ''' Shows the data described in the FMI as tree.
        Changes to values are signaled using the Qt Signal interface
    '''
    valueChanged = QtCore.Signal(types.StringType, types.StringType, types.StringType)
    VariableCheckChanged = QtCore.Signal(types.ObjectType)
    currentModelChanged = QtCore.Signal()

    ''' Python and Qt are using a different memory model - this causes Python to free
        memory still in use by Qt. To make python keep this elements in memory, they
        have to be saved somewhere, so they are simply added to this list
    '''
    _memoryHack = []

    def __init__(self, parent, model=None):
        self.parent = parent
        super(VariablesBrowser, self).__init__(parent)
        ''' Set up the columns '''
        self.setHeaderLabels(('Name', 'Value', 'Unit'))
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 70)
        self.setColumnWidth(2, 50)
        self.setIndentation(10)

        self.currentModelItem = None
        self.itemChanged.connect(self.browserItemCheckChanged)

        # Enable Context Menu (by click of right mouse button)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self._menuContextTree)

        ''' If a model is given with the constructor, load it
        '''
        if model is not None:
            self.addModel(model)

    def closeTheModel(self, model):
            self.parent.closeModel(model.numberedModelName)

    def duplicateTheModel(self, model):
            self.parent.duplicateModel(model.numberedModelName)

    def _menuContextTree(self, point):
        ''' Use entries in context menu lists of SimulatorGUI to
            build own context menus
        '''
        # Infos about the node selected.
        index = self.indexAt(point)
        if not index.isValid():
            return
        item = self.itemAt(point)

        #Seperate by case:
        #After right click on an item:
        if 'variable' in vars(item):
            menu = QtGui.QMenu(self)
            model = self.parent.models[item.modelName]
            if not model.integrationResults.isAvailable:
                menu.addAction("(Only availabe after simulation)", None)
                menu.addSeparator()
                menu.setDisabled(True)
                variable = None
                data = None
                unit = None
            else:
                menu.setDisabled(False)
                variable = item.variable
                data = model.integrationResults.readData(variable)
                unit = model.variableTree.variable[variable].unit

            # show registered callbacks in context menu
            for pluginEntry in self.parent.variableMenuCallbacks:
                for name, func in pluginEntry:
                    menu.addAction(name, functools.partial(func, model, variable, data, unit))

            # shows menu at current cursor position
            menu.exec_(QtGui.QCursor.pos())
            return

        if 'isModelRoot' in vars(item):
            modelName = str(item.text(0))
            menu = QtGui.QMenu(self)
            model = self.parent.models[modelName]

            # default entries, which should show up for all models
            menu.addAction("Close Model", functools.partial(self.closeTheModel, model))
            menu.addAction("Duplicate Model", functools.partial(self.duplicateTheModel, model))

            for pluginEntry in self.parent.modelMenuCallbacks:
                for name, func in pluginEntry:
                    menu.addAction(name, functools.partial(func, model))

            #At the end, add additional result file information:
            def fileSize2str(size):
                if size is not None:
                    if size > 1024:
                        return format(size/1024, '0.1f') + ' GB'
                    else:
                        return format(size, '0.1f') + ' MB'
                else:
                    return ''

            fileName = self.parent.models[modelName].integrationResults.fileName
            fileSize = ''
            res = menu.addMenu("Results")
            if fileName == '':
                fileName = 'No result file'
            res.addAction(fileName).setDisabled(True)
            if fileName != '':
                fileSize = fileSize2str(self.parent.models[modelName].integrationResults.fileSize())
                if fileSize != '':
                    res.addAction("File size: " + fileSize).setDisabled(True)

            # shows menu at current cursor position
            menu.exec_(QtGui.QCursor.pos())
            return

    def addItemToTree(self, treeParent, v, qualifiedName, model):
        ''' Adds a model to the tree
            recursive function for adding the items to the tree in their appropriate place
        '''
        # modifying and adding stuff in the tree by default genrates Qt Signals
        self.blockSignals(True)
        # don't redraw after each change, but wait for all changes to finish
        self.setUpdatesEnabled(False)
        if v[0].find(".") > -1:
            qualifier, remainder = v[0].split(".", 1)
            par = None
            ''' try to find tree element that already got the name of the qualifier,
                otherwise add it.
            '''
            for num in xrange(0, treeParent.childCount()):
                if treeParent.child(num).text(0) == qualifier:
                    par = treeParent.child(num)
                    break

            if par is None:
                par = QtGui.QTreeWidgetItem(treeParent)
                # save a list of all the sub-variables, to be evaluated dynamicly when tree branch is expanded
                par._dynamic = list()

            par.setText(0, qualifier)
            par.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
            par._dynamic.append(list([list([remainder, v[1]]), qualifiedName]))
            par._m = model
            self.blockSignals(False)
            self.setUpdatesEnabled(True)
            self.update()
            return

        ''' After building up the tree structure for the current element or
            finding the correct position in the tree, a "leave" is generated
            for each variable
        '''
        treeItem = QtGui.QTreeWidgetItem(treeParent)
        treeItem.setCheckState(0, QtCore.Qt.Unchecked)
        treeItem.variable = qualifiedName
        treeItem.modelName = model.numberedModelName
        treeItem.setFlags(treeItem.flags() & ~QtCore.Qt.ItemIsEditable & ~QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable)
        variableText = str(v[0])
        if len(variableText) > 6:
            if variableText[-6:] == '_(der)':
                variableText = 'der(' + variableText[:-6] + ')'
        treeItem.setText(0, variableText)

        if model.variableTree.variable[v[1]].variability == 'continuous':
            treeItem.setForeground(0, QtGui.QBrush(QtGui.QColor('blue')))
        elif model.variableTree.variable[v[1]].variability == 'discrete':
            treeItem.setForeground(0, QtGui.QBrush(QtGui.QColor('green')))

        if model.variableTree.variable[v[1]].value is not None:
            if model.variableTree.variable[v[1]].valueEdit is not None:
                if model.variableTree.variable[v[1]].valueEdit:
                    startValueBox = valueEdit(self, model.numberedModelName, treeItem.variable)
                    startValueBox.setEnabled(True)
                    startValueBox.setFrame(True)
                    startValueBox.setMaximumHeight(15)
                    startValueBox.setText(str(model.variableTree.variable[v[1]].value))
                    startValueBox.setAlignment(QtCore.Qt.Alignment(2))
                    startValueBox.valueChanged.connect(self.valueChanged)
                    self._memoryHack.append(startValueBox)
                    self.setItemWidget(treeItem, 1, startValueBox)
                else:
                    treeItem.setText(1, str(model.variableTree.variable[v[1]].value))
                    treeItem.setTextAlignment(1, QtCore.Qt.Alignment(2))

        # Set the showed unit
        if model.variableTree.variable[v[1]].unit is not None:
            treeItem.setText(2, str(model.variableTree.variable[v[1]].unit))

        # Define deepest treeitem: Additional attribute for each variable
        if model.variableTree.variable[v[1]].attribute is not None:
            description = QtGui.QTreeWidgetItem(treeItem)
            description.setFlags(description.flags() & ~QtCore.Qt.ItemIsEditable & ~QtCore.Qt.ItemIsSelectable)
            description.setFirstColumnSpanned(True)
            description.setText(0, model.variableTree.variable[v[1]].attribute)
            self._memoryHack.append(description)

        self.blockSignals(False)
        self.setUpdatesEnabled(True)
        self.update()

    def addModel(self, model, treeRoot=None):
        ''' Adds the given model to the variable browser
        '''
        self.itemChanged.disconnect()
        model.setVariableTree()

        if treeRoot is None:
            treeRoot = QtGui.QTreeWidgetItem(self)
            treeRoot.setCheckState(0, QtCore.Qt.Checked)
            treeRoot.setFlags(treeRoot.flags() & ~QtCore.Qt.ItemIsEditable & ~QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable)
            treeRoot.setText(0, model.numberedModelName)
            if model.modelType == 'None':
                treeRoot.setForeground(0, QtGui.QBrush(QtGui.QColor('grey')))
            treeRoot.numberedModelName = model.numberedModelName
            treeRoot.model = model
            treeRoot.isModelRoot = True
            treeRoot.setFirstColumnSpanned(True)
            treeRoot.setExpanded(True)
            model.rootItem = treeRoot
        elif treeRoot.childCount() > 0:
            # Define function that is called when a item of the tree will be checked/unchecked
            self.itemChanged.connect(self.browserItemCheckChanged)
            return

        # Define the tipText displayed when stopping the mouse over the numbered model name in the variable browser
        tipText = 'Model type: ' + model.modelType
        if model.variableTree.rootAttribute is not None:
            if len(model.variableTree.rootAttribute) > 0:
                tipText += '\n\n' + model.variableTree.rootAttribute
        treeRoot.setToolTip(0, tipText)
        # Generate a nice list of model variables
        variableNames = model.variableTree.variable.keys()

        def sortKey(x):
            a = str(x).upper()
            i = a.rfind('.')
            if i < 0:
                return '^' + a
            else:
                return a[:i] + '.^' + a[i + 1:]
        # Sort the variables for the tree
        variableNames.sort(key=sortKey)

        for v in variableNames:
            self.addItemToTree(treeRoot, (v, v), v, model)

        # Show changed start values in startValueBox given in model.settings
        for variable in model.changedStartValue:
            self.setVariable(model, variable, model.changedStartValue[variable])

        # Define function that is called when a item of the tree will be checked/unchecked
        self.itemChanged.connect(self.browserItemCheckChanged)
        self.itemExpanded.connect(self.dyamicLoadBranch)
        # To set this model as current one
        self.browserItemCheckChanged(treeRoot)

    def removeModel(self, model):
        ''' Remove model from tree
        '''
        for i in range(0, self.topLevelItemCount()):
            #if self.topLevelItem(i).text(0) == modelName:
            if self.topLevelItem(i).model == model:
                deletedItem = self.takeTopLevelItem(i)
                if deletedItem.numberedModelName == self.currentModelItem.numberedModelName:
                    # Set new current model
                    if i < self.topLevelItemCount():
                        self.changeCurrentModel(self.topLevelItem(i))
                    elif i - 1 >= 0:
                        self.changeCurrentModel(self.topLevelItem(i - 1))
                    else:
                        self.changeCurrentModel(None)
                return

    def changeCurrentModel(self, toItem):
        ''' Changes the current marked model in the variables browser to the model
            defined by the tree item 'toItem'
        '''
        def checkNewItem():
            ''' Marks the item as current one
            '''           
            toItem.setCheckState(0, QtCore.Qt.Checked)
            font = toItem.font(0)
            font.setBold(True)
            blocked = self.signalsBlocked()
            self.blockSignals(True)
            # Setting the font leads to an emitted signal 'itemChanged' that we do not want to have here
            toItem.setFont(0, font)
            self.blockSignals(blocked)

        def uncheckCurrentItem():
            ''' Sets the current item to a normal one
            '''
            blocked = self.signalsBlocked()
            self.blockSignals(True)
            # Unchecking should not lead to an emitted signal 'itemChanged'
            self.currentModelItem.setCheckState(0, QtCore.Qt.Unchecked)
            font = self.currentModelItem.font(0)
            font.setBold(False)
            # Setting the font leads to an emitted signal 'itemChanged' that we do not want to have here
            self.currentModelItem.setFont(0, font)
            self.blockSignals(blocked)

        if self.currentModelItem is None:
            if toItem is not None:
                checkNewItem()
        else:
            if toItem is None:
                uncheckCurrentItem()
                # Emit currentModelChanged, because no item will be checked to emit the signal
                self.currentModelItem = None                
                self.currentModelChanged.emit()
            elif toItem.numberedModelName == self.currentModelItem.numberedModelName:
                checkNewItem()
            else:
                uncheckCurrentItem()
                checkNewItem()
        self.currentModelItem = toItem

    def browserItemCheckChanged(self, item):
        ''' This function is normally called when the check state of the given
            tree item has changed. Different activities result from this event. '''

        if 'variable' in vars(item):
            ''' Relay the signal, that a variable check state has changed
            '''
            self.VariableCheckChanged.emit(item)
        elif hasattr(item, 'isModelRoot'):
            ''' Handle changing the current model
            '''
            blocked = self.signalsBlocked()
            self.blockSignals(True)
            self.changeCurrentModel(item)
            self.blockSignals(blocked)
            self.currentModelChanged.emit()

    def dyamicLoadBranch(self, item):
        ''' Generating the Qt tree elements requires significant time.
            Therefore the tree elements are generated and loaded dynamicly
            as the user unfolds tree elements
        '''
        if item.childCount() > 0 or (not hasattr(item, '_dynamic')):
            return
        for i in item._dynamic:
            self.addItemToTree(item, i[0], i[1], item._m)

    def setVariable(self, model, variable, value):
        ''' Set the start value in the startValueBox of variable variableName
            in model modelName to value value
        '''
        item = self.findVariableItem(model, variable)
        if item:
            self.itemWidget(item, 1).setText(str(value))

    def findVariableItem(self, model, variable):
        ''' Finds a variable reference in a model
        '''
        # This is rather ugly but I don't know how this could be done nicer, for PySide here pretty much
        # simply mirrors Qt C++-Interface. So this has to be done manually and unoptimized.
        for i in range(0, self.topLevelItemCount()):
            ''' top level items are the model names
            '''
            if self.topLevelItem(i).model == model:
                ''' performe a simple BFS for the value in the tree
                '''
                findList = [self.topLevelItem(i).child(x) for x in range(0, self.topLevelItem(i).childCount())]
                while len(findList) > 0:
                    item = findList.pop(0)
                    if hasattr(item, 'variable'):
                        if item.variable == variable:
                            return item
                    else:
                        for x in range(0, item.childCount()):
                            findList.append(item.child(x))

    def checkVariable(self, model, variable, state=True, BlockSignals=True):
        ''' Change the check state of a variable in the tree
            The generation of Qt Signals indicating the change can be blocked
        '''
        self.blockSignals(BlockSignals)
        item = self.findVariableItem(model, variable)
        if item:
            item.setCheckState(0, (QtCore.Qt.Checked if state else QtCore.Qt.Unchecked))
        else:
            print "Error finding variable in tree! ", state, model, variable
        self.blockSignals(False)


class valueEdit(QtGui.QLineEdit):
    ''' Editable field in tree structure
    '''
    valueChanged = QtCore.Signal(types.StringType, types.StringType, types.StringType)

    def __init__(self, parent, numberedModelName, variable):
        self.numberedModelName = numberedModelName
        self.variable = variable
        QtGui.QLineEdit.__init__(self)
        self.setFrame(True)

        ''' Set background to white as default
        '''
        self._palette = QtGui.QPalette()
        self._palette.setColor(self.backgroundRole(), QtGui.QColor(255, 255, 255))
        self.setPalette(self._palette)

        self.editingFinished.connect(self._relay)
        self.textEdited.connect(self._edited)

    def _edited(self):
        ''' if text was edited, set background to grey
        '''
        self._palette.setColor(self.backgroundRole(), QtGui.QColor(200, 200, 200))
        self.setPalette(self._palette)

    def _relay(self):
        if self.isModified():
            self.valueChanged.emit(self.numberedModelName, self.variable, self.text())
            self.setModified(False)
            ''' When editing is finished, reset background color to white
            '''
            self._palette.setColor(self.backgroundRole(), QtGui.QColor(255, 255, 255))
            self.setPalette(self._palette)


if __name__ == "__main__":
    app = QtGui.QApplication([])

    from Plugins.Simulator.FMUSimulator import FMUSimualtor
    fmu = FMUSimulator.Model('Examples/Modelica_Mechanics_Rotational_Examples_Friction.fmu')

    def blub(a, b, c):
        print 'variable value changed: %s %s %s' % (a, b[0], c)

    def bla(a):
        print 'Item %s' % a
        print a.text(0)

    vb = VariablesBrowser(None)
    vb.addModel(fmu)
    vb.show()

    vb.valueChanged.connect(blub)
    vb.VariableCheckChanged.connect(bla)

    vb.setVariable('', 'startTime', 1.5e-3)

    app.exec_()
