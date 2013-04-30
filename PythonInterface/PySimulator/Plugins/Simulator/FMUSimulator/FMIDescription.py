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


import xml.etree.ElementTree as etree
import copy
import FMUError


class DISPLAYUnit:
    ''' Class for converting unit to displayUnits according to
                displayUnit = gain * unit + offset
        This is not according to FMI-Standard 1.0, but
        there is probably a inconsistency in the Standard
        compared to the given examples in the Standard document.
    '''
    def __init__(self, gain, offset):
        self.gain = float(gain)
        self.offset = float(offset)

    def convert(self, unitValue):
        return self.gain * unitValue + self.offset


class FMIType:
    ''' Class for description of Data types in FMI
        Some values are optional, them not being defined is signaled by a value of None
    '''
    def __init__(self, type):
        ''' Populate data from type
            @type type: ElemenTree Element holding a type description
        '''
        self.type = str(type.tag).replace('Type', '')
        self.description = type.get('description')
        self.quantity = type.get('quantity')
        self.unit = type.get('unit')
        self.displayUnit = type.get('displayUnit')  # Default display unit
        self.relativeQuantity = type.get('relativeQuantity') == 'true'
        self.min = type.get('min')
        self.max = type.get('max')
        self.nominal = type.get('nominal')
        self.item = []
        for item in type.findall('Item'):
            self.item.append((item.get('name'), item.get('description')))
        self.start = type.get('start')
        self.fixed = type.get('fixed')
        self.name = type.get('declaredType')

    def updateDefaults(self, update):
        ''' Update data using update
            @type update: ElemenTree Element holding a [partial] type description to update this description with
        '''
        if update.get('quantity') is not None:
            self.quantity = update.get('quantity')
        if update.get('unit') is not None:
            self.unit = update.get('unit')
        if update.get('displayUnit') is not None:
            self.displayUnit = update.get('displayUnit')
        if update.get('relativeQuantity') is not None:
            self.relativeQuantity = update.get('relativeQuantity') == 'true'
        if update.get('min') is not None:
            self.min = update.get('min')
        if update.get('max') is not None:
            self.max = update.get('max')
        if update.get('nominal') is not None:
            self.nominal = update.get('nominal')
        if update.get('start') is not None:
            self.start = update.get('start')
        if update.get('fixed') is not None:
            self.fixed = update.get('fixed')


class FMIScalarVariable:
    ''' Class for description of Scalar Variables
    '''
    def __init__(self, type, reference):
        self.type = type
        self.valueReference = int(reference)
        self.description = None
        self.variability = 'continuous'
        self.causality = None
        self.alias = None


class FMIDescription:
    ''' This object holds the description of an Functional Mock-up Interface for Model Exchange
        It parses an XML-file description as defined by MODELISAR (ITEA 2 - 07006) Version 1.0
        The model description (FMI) is usually part of a Functional Mock-Up Unit (FMU)
    '''
    def __init__(self, xmlFile, parent=None):
        ''' Create FMIDescription from XML-file
            @param xmlFile: File object of the describing XML-Document
        '''

        ''' initialization of variables and more visible public interface '''
        self.units = {}
        self.types = {}
        self.scalarVariables = {}
        self.fmiVersion = ''
        self.modelName = ''
        self.modelIdentifier = ''
        self.guid = ''
        self.description = ''
        self.author = ''
        self.version = ''
        self.generationTool = ''
        self.generationDateAndTime = ''
        self.variableNamingConvention = 'structured'
        self.numberOfContinuousStates = 0
        self.numberOfEventIndicators = 0
        self.defaultStartTime = 0
        self.defaultStopTime = 1
        self.defaultTolerance = 1e-4

        if xmlFile is None:
            return

        ''' Parse the file '''
        try:
            self._document = etree.parse(xmlFile)
        except BaseException as e:
            print 'Error when parsing FMU\'s xml-file. Error: ', e
            raise FMUError.FMUError('Error when parsing FMU\'s xml-file.\n' + str(e) + '\n')
        self._docroot = self._document.getroot()
        if self._docroot.tag != 'fmiModelDescription':
            raise FMUError.FMUError('XML-File type not recognized!\n')
        ''' Parse the global FMI Model Description Attributes '''
        for desc in self._docroot.keys():
            if desc == 'fmiVersion':
                self.fmiVersion = self._docroot.get(desc)
                if self.fmiVersion != '1.0':
                    '''According to latest standard only version 1.0 is supported
                    '''
                    raise FMUError.FMUError('Only FMI v1.0 supported!\n')
            elif desc == 'modelName':
                self.modelName = self._docroot.get(desc)
            elif desc == 'modelIdentifier':
                self.modelIdentifier = self._docroot.get(desc)
            elif desc == 'guid':
                self.guid = self._docroot.get(desc)
            elif desc == 'description':
                self.description = self._docroot.get(desc)
            elif desc == 'author':
                self.author = self._docroot.get(desc)
            elif desc == 'version':
                self.version = self._docroot.get(desc)
            elif desc == 'generationTool':
                self.generationTool = self._docroot.get(desc)
            elif desc == 'generationDateAndTime':
                self.generationDateAndTime = self._docroot.get(desc)
            elif desc == 'variableNamingConvention':
                self.variableNamingConvention = self._docroot.get(desc)
            elif desc == 'numberOfContinuousStates':
                self.numberOfContinuousStates = int(self._docroot.get(desc))
            elif desc == 'numberOfEventIndicators':
                self.numberOfEventIndicators = int(self._docroot.get(desc))
            else:
                print('unrecognized model description:\t %s: %s \n' % (desc, self._docroot.get(desc)))
        ''' Child nodes are each parsed by their own subroutine '''
        for child in self._docroot:
            if child.tag == 'UnitDefinitions':
                self._parseUnits(child)
            elif child.tag == 'TypeDefinitions':
                self._parseTypes(child)
            elif child.tag == 'VendorAnnotations':
                print('Vendor specific data found. This is currently ignored!\n')
            elif child.tag == 'DefaultExperiment':
                self._parseDefaultExperiment(child)
            elif child.tag == 'ModelVariables':
                self._parseModelVariables(child)
            else:
                print('Unknown tag in FMI Model: %s\n' % child.tag)

    def _parseModelVariables(self, varRoot):
        ''' Parse Model Variables
            @type varRoot: ElemenTree Element holding Model Variable definitions
        '''
        ''' See documentation for: '_parseTypes' '''
        for scalar in varRoot:
            if scalar.tag != 'ScalarVariable':
                ''' The current FMI definition only knows scalar values '''
                raise FMUError.FMUError('ModelVariables definition using non-scalar value.\n')
            if scalar[0].get('declaredType') is not None:
                type = copy.copy(self.types[scalar[0].get('declaredType')])
                type.name = scalar[0].get('declaredType')
                type.updateDefaults(scalar[0])
            else:
                type = FMIType(scalar[0])
            reference = scalar.get('valueReference')
            ''' Change some variable names '''
            scalarName = scalar.get('name')
            if len(scalarName) > 5:
                ''' Change variable name for derivatives to include them
                    correctly in the variable browser; only a temorary solution
                '''
                if scalarName[:4] == "der(":
                    scalar.set('name', scalarName[4:-1] + "_(der)")
                    scalarName = scalar.get('name')
            '''
            Change variable name for arrays to include them
            correctly in the variable browser
            '''
            scalarName = scalarName.replace('[', '.[')
            # Set the scalarVariable
            s = FMIScalarVariable(type, reference)
            s.description = scalar.get('description')
            s.variability = scalar.get('variability', 'continuous')
            s.causality = scalar.get('causality')
            s.alias = scalar.get('alias')
            s.directDependency = True if scalar.find('DirectDependency') is not None else False
            self.scalarVariables[scalarName] = s

    def _parseUnits(self, unitsRoot):
        ''' Parse Unit descriptions.
            @param unitsRoot: ElemenTree Element holding unit definitions
        '''
        for unit in unitsRoot:
            if unit.tag != 'BaseUnit':
                ''' According to definition this may only be BaseUnit '''
                raise FMUError.FMUError('Unknown unit type: ' + unit.tag + '\n')

            unitName = unit.get('unit')
            '''
                The following creates a dictionary for each base unit containing a dictionary for each corresponding display
                unit, which again holds the gain and offset and a function for conversion from the base to the display unit.
                Usage: converted_value_in_displayUnit = fmimodel.units[baseUnit][displayUnit].convert(100)
                eg: print fmi.units['K']['degC'].convert(100)
                    --> -173.15
            '''
            self.units[unitName] = dict()
            for displayUnitDef in unit.findall('DisplayUnitDefinition'):
                gain = displayUnitDef.get('gain', '1')
                offset = displayUnitDef.get('offset', '0')
                displayUnit = displayUnitDef.get('displayUnit', '')
                self.units[unitName][displayUnit] = DISPLAYUnit(gain, offset)

    def _parseDefaultExperiment(self, child):
        self.defaultStartTime = child.get('startTime')
        self.defaultStopTime = child.get('stopTime')
        self.defaultTolerance = child.get('tolerance')

    def _parseTypes(self, typesRoot):
        ''' Parse Type descriptions.
            @type typesRoot: ElemenTree Element holding type definitions
        '''
        ''' Most functionality has be encapsulated in FMIType for Scalar Variables use a similar definition of types.
            According to standard, type has one and only one child. It can therefore be accessed safely by type[0]
        '''
        for type in typesRoot:
            if type.tag != 'Type':
                ''' The current FMI definition only knows type Type '''
                raise FMUError.FMUError('TypeDefinitions defining non-type.\n')
            if len(type) != 1:
                raise FMUError.FMUError('Bad type description for: ' + type + '\n')
            self.types[type.get('name')] = FMIType(type[0])


if __name__ == '__main__':
    ''' This is for testing and development only! '''

    ''' Read FMI description file (directly from zip-file)'''
    import zipfile
    fmuFile = zipfile.ZipFile('Modelica_Electrical_Analog_Examples_Rectifier.fmu',  'r')
    fmi = FMIDescription(fmuFile.open('modelDescription.xml'))

    print "Attributes"
    print "*************"
    print fmi.fmiVersion
    print fmi.guid
    print fmi.numberOfContinuousStates

    print "Units"
    print "*************"
    print fmi.units
    print fmi.units['K']
    print fmi.units['K']['degC'].gain, fmi.units['K']['degC'].offset
    print fmi.units['K']['degC'].convert(100)
    print fmi.units['rad']['deg'].convert(100)

    print "Types"
    print "*************"
    print fmi.types.keys()
    print fmi.types['Modelica.SIunits.Voltage'].type
    print fmi.types['Modelica.SIunits.Voltage'].description

    print "ScalarVariables"
    print "***************"
    print fmi.scalarVariables.keys()
    print fmi.scalarVariables['Capacitor1.p.v'].type
    print fmi.scalarVariables['Capacitor1.p.v'].type.unit
    print fmi.scalarVariables['Capacitor1.p.v'].valueReference
    print fmi.scalarVariables['Capacitor1.p.v'].variability
