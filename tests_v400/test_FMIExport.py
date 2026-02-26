import OMPython
import shutil
import os


def test_CauerLowPassAnalog():
    mod = OMPython.ModelicaSystem(modelName="Modelica.Electrical.Analog.Examples.CauerLowPassAnalog",
                                  lmodel=["Modelica"])
    tmp = mod.getWorkDirectory()
    try:
        fmu = mod.convertMo2Fmu(fileNamePrefix="CauerLowPassAnalog")
        assert os.path.exists(fmu)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_DrumBoiler():
    mod = OMPython.ModelicaSystem(modelName="Modelica.Fluid.Examples.DrumBoiler.DrumBoiler", lmodel=["Modelica"])
    tmp = mod.getWorkDirectory()
    try:
        fmu = mod.convertMo2Fmu(fileNamePrefix="DrumBoiler")
        assert os.path.exists(fmu)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
