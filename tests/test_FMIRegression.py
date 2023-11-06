import OMPython
import tempfile, shutil, os
import pytest


"""
do not change the prefix class name, the class name should have prefix "Test"
according to the documenation of pytest
"""
class Test_FMIRegression:

    def checkModel(self, modelName):
        mod = OMPython.ModelicaSystem(modelName=modelName)
        fileNamePrefix = modelName.split(".")[-1]
        fmu = mod.convertMo2Fmu(fileNamePrefix=fileNamePrefix)
        assert True == os.path.exists(fmu)
        shutil.rmtree(mod.getWorkDirectory(), ignore_errors=True)
        mod.__del__()


    def test_Modelica_Blocks_Examples_Filter(self):
        self.checkModel("Modelica.Blocks.Examples.Filter")

    def test_Modelica_Blocks_Examples_RealNetwork1(self):
        self.checkModel("Modelica.Blocks.Examples.RealNetwork1")

    def test_Modelica_Electrical_Analog_Examples_CauerLowPassAnalog(self):
        self.checkModel("Modelica.Electrical.Analog.Examples.CauerLowPassAnalog")

    def test_Modelica_Electrical_Digital_Examples_FlipFlop(self):
        self.checkModel("Modelica.Electrical.Digital.Examples.FlipFlop")

    def test_Modelica_Mechanics_Rotational_Examples_FirstGrounded(self):
        self.checkModel("Modelica.Mechanics.Rotational.Examples.FirstGrounded")

    def test_Modelica_Mechanics_Rotational_Examples_CoupledClutches(self):
        self.checkModel("Modelica.Mechanics.Rotational.Examples.CoupledClutches")

    def test_Modelica_Mechanics_MultiBody_Examples_Elementary_DoublePendulum(self):
        self.checkModel("Modelica.Mechanics.MultiBody.Examples.Elementary.DoublePendulum")

    def test_Modelica_Mechanics_MultiBody_Examples_Elementary_FreeBody(self):
        self.checkModel("Modelica.Mechanics.MultiBody.Examples.Elementary.FreeBody")

    def test_Modelica_Fluid_Examples_PumpingSystem(self):
        self.checkModel("Modelica.Fluid.Examples.PumpingSystem")

    def test_Modelica_Fluid_Examples_TraceSubstances_RoomCO2WithControls(self):
        self.checkModel("Modelica.Fluid.Examples.TraceSubstances.RoomCO2WithControls")

    def test_Modelica_Clocked_Examples_SimpleControlledDrive_ClockedWithDiscreteTextbookController(self):
        self.checkModel("Modelica.Clocked.Examples.SimpleControlledDrive.ClockedWithDiscreteTextbookController")

