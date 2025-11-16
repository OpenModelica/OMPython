import tempfile
import pathlib
import shutil
import os

import OMPython


def buildModelFMU(modelName):
    omc = OMPython.OMCSessionZMQ()

    tempdir = pathlib.Path(tempfile.mkdtemp())
    try:
        omc.sendExpression(f'cd("{tempdir.as_posix()}")')

        omc.sendExpression("loadModel(Modelica)")
        omc.sendExpression("getErrorString()")

        fileNamePrefix = modelName.split(".")[-1]
        exp = f'buildModelFMU({modelName}, fileNamePrefix="{fileNamePrefix}")'
        fmu = omc.sendExpression(exp)
        assert os.path.exists(fmu)
    finally:
        del omc
        shutil.rmtree(tempdir, ignore_errors=True)


def test_Modelica_Blocks_Examples_Filter():
    buildModelFMU("Modelica.Blocks.Examples.Filter")


def test_Modelica_Blocks_Examples_RealNetwork1():
    buildModelFMU("Modelica.Blocks.Examples.RealNetwork1")


def test_Modelica_Electrical_Analog_Examples_CauerLowPassAnalog():
    buildModelFMU("Modelica.Electrical.Analog.Examples.CauerLowPassAnalog")


def test_Modelica_Electrical_Digital_Examples_FlipFlop():
    buildModelFMU("Modelica.Electrical.Digital.Examples.FlipFlop")


def test_Modelica_Mechanics_Rotational_Examples_FirstGrounded():
    buildModelFMU("Modelica.Mechanics.Rotational.Examples.FirstGrounded")


def test_Modelica_Mechanics_Rotational_Examples_CoupledClutches():
    buildModelFMU("Modelica.Mechanics.Rotational.Examples.CoupledClutches")


def test_Modelica_Mechanics_MultiBody_Examples_Elementary_DoublePendulum():
    buildModelFMU("Modelica.Mechanics.MultiBody.Examples.Elementary.DoublePendulum")


def test_Modelica_Mechanics_MultiBody_Examples_Elementary_FreeBody():
    buildModelFMU("Modelica.Mechanics.MultiBody.Examples.Elementary.FreeBody")


def test_Modelica_Fluid_Examples_PumpingSystem():
    buildModelFMU("Modelica.Fluid.Examples.PumpingSystem")


def test_Modelica_Fluid_Examples_TraceSubstances_RoomCO2WithControls():
    buildModelFMU("Modelica.Fluid.Examples.TraceSubstances.RoomCO2WithControls")


def test_Modelica_Clocked_Examples_SimpleControlledDrive_ClockedWithDiscreteTextbookController():
    buildModelFMU("Modelica.Clocked.Examples.SimpleControlledDrive.ClockedWithDiscreteTextbookController")
