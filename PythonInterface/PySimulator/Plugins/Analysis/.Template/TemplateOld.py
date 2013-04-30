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


'''
The init function is the entry point for every Plug-In. 
Is provides functions for the main gui which can be accessed three different ways:

    - 1. A pull-down menu by the call of subMenu.addAction. An Icon can be specified
    - 2. An own button bar with user-defined buttons
    - 3. An entry in the context menus which appears when right-clicking on different gui elements.
      For this, the Plug-In writes a callback functions in a list, e.g. in the list QMainWindow.actionOnModelInTree
        
See the example functionality below for the implementation of this functionality.

'''
def init(QMainWindow, subMenu):
    #Change Toolbar:
    subMenu.setTitle("Template")   
    return TemplateToolbar(QMainWindow, subMenu)


class TemplateToolbar:
      
    '''
        This functions adds the entries to the toolbar and links them with the functions
        which are called when the buttons are pressed
    '''
    def __init__(self, QMainWindow, subMenu):

        import os
        self.rootDir = os.path.abspath(os.path.dirname(__file__))
        
        #Save a pointer to the main window:
        self.parent = QMainWindow
        
        #Decide here how you want your plug-in to be integrated in the main GUI:
        self.createMenuEntries = True
        self.showIconsInMenuEntries = True
        self.createButtonBar = True
        
        #1. Create entries from the pull-down menu:        
        if self.createMenuEntries:
            if self.showIconsInMenuEntries:
                self.entry1 = subMenu.addAction(QtGui.QIcon(self.rootDir + "/Icons/one.png"), 'First Entry', self._action1) 
                self.entry2 = subMenu.addAction(QtGui.QIcon(self.rootDir + "/Icons/two.png"), 'Second Entry', self._action2)
                self.entry3 = subMenu.addAction(QtGui.QIcon(self.rootDir + "/Icons/three.png"), 'Third Entry', self._action3)
            else:
                self.entry1 = subMenu.addAction('First Entry', self._action1) 
                self.entry2 = subMenu.addAction('Second Entry', self._action2)
                self.entry3 = subMenu.addAction('Third Entry', self._action3)            
            #action3 will be available after action1 was pressed:
            self.entry3.setEnabled(False)
 
 
        #2. Create buttons in an own buttonBar:           
        if self.createButtonBar:                          
            self._iconbar = QtGui.QToolBar('TemplateBar', QMainWindow)
            QMainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self._iconbar)
            self._iconbar.setIconSize(QtCore.QSize(18, 18))
            self.button1 = self._iconbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/one.png"), 'Action 1', self._action1)
            self.button2 = self._iconbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/two.png"), 'Action 2', self._action2)
            self.button3 = self._iconbar.addAction(QtGui.QIcon(self.rootDir + "/Icons/three.png"), 'Action 3', self._action3)
            #action3 will be available after action1 was pressed:
            self.button3.setEnabled(False)  


        #3. Add some additional functions for the context menus of variables and models:
        self.parent.actionOnVariableInTree.append(["Template", "Print name", self._rightClickOnVariable])
        self.parent.actionOnModelInTree.append(["Template", "Print name", self._rightClickOnModel])   
     
     
    def _action1(self):       
        print "action1 pressed"    
            
        #Action3 is now possible:
        if self.createMenuEntries:
            self.entry3.setEnabled(True)
        if self.createButtonBar:
            self.button3.setEnabled(True)          
     
    def _action2(self):       
        print "action2 pressed"    

    def _action3(self):
        print "action3 pressed"    
        
    def _rightClickOnVariable(self, model, variable, data, unit):
        print "Clicked on variable " + variable
        
    def _rightClickOnModel(self, model):
        print "Clicked on model " + model.name        
