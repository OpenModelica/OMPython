import OMPython
import unittest
import tempfile
import shutil
import os


class ModelicaSystemTester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ModelicaSystemTester, self).__init__(*args, **kwargs)
        self.tmp = tempfile.mkdtemp(prefix='tmpOMPython.tests')
        with open("%s/M.mo" % self.tmp, "w") as fout:
            fout.write("""model M
  Real x(start = 1);
  parameter Real a = -1;
equation
  der(x) = x*a;
end M;
                   """)

    def __del__(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def testModelicaSystemLoop(self):
        def worker():
            filePath = os.path.join(self.tmp, "M.mo").replace("\\", "/")
            m = OMPython.ModelicaSystem(filePath, "M")
            m.simulate()
            m.convertMo2Fmu(fmuType="me")
            for _ in range(10):
                worker()

    def test_setParameters(self):
        omc = OMPython.OMCSessionZMQ()
        model_path = omc.sendExpression("getInstallationDirectoryPath()") + "/share/doc/omc/testmodels/"
        mod = OMPython.ModelicaSystem(model_path + "BouncingBall.mo", "BouncingBall", raiseerrors=True)

        # method 1
        mod.setParameters("e=1.234")
        mod.setParameters("g=321.0")
        assert mod.getParameters("e") == [1.234]
        assert mod.getParameters("g") == [321.0]
        assert mod.getParameters() == {
            "e": 1.234,
            "g": 321.0,
        }

        # method 2
        mod.setParameters(["e=21.3", "g=0.12"])
        assert mod.getParameters() == {
            "e": 21.3,
            "g": 0.12,
        }
        assert mod.getParameters(["e", "g"]) == [21.3, 0.12]
        assert mod.getParameters(["g", "e"]) == [0.12, 21.3]

        # method 3
        mod.setParameters({
            "e": 2.13,
            "g": 0.21,
        })
        assert mod.getParameters() == {
            "e": 2.13,
            "g": 0.21,
        }

if __name__ == '__main__':
    unittest.main()
