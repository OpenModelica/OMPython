import OMPython
import unittest
import tempfile
import shutil
import os
import pathlib


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
        assert mod.getParameters("e") == ["1.234"]
        assert mod.getParameters("g") == ["321.0"]
        assert mod.getParameters() == {
            "e": "1.234",
            "g": "321.0",
        }

        # method 2
        mod.setParameters(["e=21.3", "g=0.12"])
        assert mod.getParameters() == {
            "e": "21.3",
            "g": "0.12",
        }
        assert mod.getParameters(["e", "g"]) == ["21.3", "0.12"]
        assert mod.getParameters(["g", "e"]) == ["0.12", "21.3"]

    def test_setSimulationOptions(self):
        omc = OMPython.OMCSessionZMQ()
        model_path = omc.sendExpression("getInstallationDirectoryPath()") + "/share/doc/omc/testmodels/"
        mod = OMPython.ModelicaSystem(model_path + "BouncingBall.mo", "BouncingBall", raiseerrors=True)

        # method 1
        mod.setSimulationOptions("stopTime=1.234")
        mod.setSimulationOptions("tolerance=1.1e-08")
        assert mod.getSimulationOptions("stopTime") == ["1.234"]
        assert mod.getSimulationOptions("tolerance") == ["1.1e-08"]
        assert mod.getSimulationOptions(["tolerance", "stopTime"]) == ["1.1e-08", "1.234"]
        d = mod.getSimulationOptions()
        assert isinstance(d, dict)
        assert d["stopTime"] == "1.234"
        assert d["tolerance"] == "1.1e-08"

        # method 2
        mod.setSimulationOptions(["stopTime=2.1", "tolerance=1.2e-08"])
        d = mod.getSimulationOptions()
        assert d["stopTime"] == "2.1"
        assert d["tolerance"] == "1.2e-08"

    def test_relative_path(self):
        cwd = pathlib.Path.cwd()
        (fd, name) = tempfile.mkstemp(dir=cwd, text=True)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write("""model M
  Real x(start = 1, fixed=true);
  parameter Real a = -1;
equation
  der(x) = x*a;
end M;
""")

            model_file = pathlib.Path(name).relative_to(cwd)
            model_relative = str(model_file)
            assert "/" not in model_relative

            mod = OMPython.ModelicaSystem(model_relative, "M", raiseerrors=True)
            assert float(mod.getParameters("a")[0]) == -1
        finally:
            # clean up the temporary file
            model_file.unlink()


if __name__ == '__main__':
    unittest.main()
