import OMPython
import unittest
import shutil
import os


class testFMIExport(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(testFMIExport, self).__init__(*args, **kwargs)
        self.tmp = ""

    def __del__(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def testCauerLowPassAnalog(self):
        print("testing Cauer")
        mod = OMPython.ModelicaSystem(modelName="Modelica.Electrical.Analog.Examples.CauerLowPassAnalog",
                                      lmodel=["Modelica"])
        self.tmp = mod.getWorkDirectory()

        fmu = mod.convertMo2Fmu(fileNamePrefix="CauerLowPassAnalog")
        self.assertEqual(True, os.path.exists(fmu))

    def testDrumBoiler(self):
        print("testing DrumBoiler")
        mod = OMPython.ModelicaSystem(modelName="Modelica.Fluid.Examples.DrumBoiler.DrumBoiler", lmodel=["Modelica"])
        self.tmp = mod.getWorkDirectory()

        fmu = mod.convertMo2Fmu(fileNamePrefix="DrumBoiler")
        self.assertEqual(True, os.path.exists(fmu))


if __name__ == '__main__':
    unittest.main()
