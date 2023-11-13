import OMPython
import tempfile, shutil, os
import pytest


"""
do not change the prefix class name, the class name should have prefix "Test"
according to the documenation of pytest
"""
class Test_FMIRegression:

    def buildModelFMU(self, modelName):
        omc = OMPython.OMCSessionZMQ()

        ## create a temp dir for each session
        tempdir = tempfile.mkdtemp()
        if not os.path.exists(tempdir):
            return print(tempdir, " cannot be created")

        tempdirExp="".join(["cd(","\"",tempdir,"\"",")"]).replace("\\","/")
        omc.sendExpression(tempdirExp)

        omc.sendExpression("loadModel(Modelica)")
        omc.sendExpression("getErrorString()")

        fileNamePrefix = modelName.split(".")[-1]
        exp = "buildModelFMU(" + modelName + ", fileNamePrefix=\"" + fileNamePrefix  + "\"" + ")"

        fmu = omc.sendExpression(exp)
        assert True == os.path.exists(fmu)

        omc.__del__()
        shutil.rmtree(tempdir, ignore_errors= True)

    def test_Modelica_Blocks_Examples_Filter(self):
        self.buildModelFMU("Modelica.Blocks.Examples.Filter")

    def test_Modelica_Blocks_Examples_RealNetwork1(self):
        self.buildModelFMU("Modelica.Blocks.Examples.RealNetwork1")

    def test_Modelica_Electrical_Analog_Examples_CauerLowPassAnalog(self):
        self.buildModelFMU("Modelica.Electrical.Analog.Examples.CauerLowPassAnalog")

    def test_Modelica_Electrical_Digital_Examples_FlipFlop(self):
        self.buildModelFMU("Modelica.Electrical.Digital.Examples.FlipFlop")

    def test_Modelica_Mechanics_Rotational_Examples_FirstGrounded(self):
        self.buildModelFMU("Modelica.Mechanics.Rotational.Examples.FirstGrounded")

    def test_Modelica_Mechanics_Rotational_Examples_CoupledClutches(self):
        self.buildModelFMU("Modelica.Mechanics.Rotational.Examples.CoupledClutches")

    def test_Modelica_Mechanics_MultiBody_Examples_Elementary_DoublePendulum(self):
        self.buildModelFMU("Modelica.Mechanics.MultiBody.Examples.Elementary.DoublePendulum")

    def test_Modelica_Mechanics_MultiBody_Examples_Elementary_FreeBody(self):
        self.buildModelFMU("Modelica.Mechanics.MultiBody.Examples.Elementary.FreeBody")

    def test_Modelica_Fluid_Examples_PumpingSystem(self):
        self.buildModelFMU("Modelica.Fluid.Examples.PumpingSystem")

    def test_Modelica_Fluid_Examples_TraceSubstances_RoomCO2WithControls(self):
        self.buildModelFMU("Modelica.Fluid.Examples.TraceSubstances.RoomCO2WithControls")

    def test_Modelica_Clocked_Examples_SimpleControlledDrive_ClockedWithDiscreteTextbookController(self):
        self.buildModelFMU("Modelica.Clocked.Examples.SimpleControlledDrive.ClockedWithDiscreteTextbookController")
