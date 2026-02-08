import os
import pathlib
import shutil

import OMPython


def test_CauerLowPassAnalog():
    mod = OMPython.ModelicaSystemOMC()
    mod.model(
        model_name="Modelica.Electrical.Analog.Examples.CauerLowPassAnalog",
        libraries=["Modelica"],
    )
    tmp = pathlib.Path(mod.getWorkDirectory())
    try:
        fmu = mod.convertMo2Fmu(fileNamePrefix="CauerLowPassAnalog")
        assert os.path.exists(fmu)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_DrumBoiler():
    mod = OMPython.ModelicaSystemOMC()
    mod.model(
        model_name="Modelica.Fluid.Examples.DrumBoiler.DrumBoiler",
        libraries=["Modelica"],
    )
    tmp = pathlib.Path(mod.getWorkDirectory())
    try:
        fmu = mod.convertMo2Fmu(fileNamePrefix="DrumBoiler")
        assert os.path.exists(fmu)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
