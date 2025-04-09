import OMPython
import unittest
import tempfile
import shutil
import os
import pathlib
import numpy as np


class ModelicaSystemTester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ModelicaSystemTester, self).__init__(*args, **kwargs)
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix='tmpOMPython.tests'))
        with open(self.tmp / "M.mo", "w") as fout:
            fout.write("""model M
  Real x(start = 1, fixed = true);
  parameter Real a = -1;
equation
  der(x) = x*a;
end M;
                   """)

    def __del__(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def testModelicaSystemLoop(self):
        def worker():
            filePath = (self.tmp / "M.mo").as_posix()
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
        (fd, name) = tempfile.mkstemp(prefix='tmpOMPython.tests', dir=cwd, text=True)
        try:
            with os.fdopen(fd, 'w') as f:
                f.write((self.tmp / "M.mo").read_text())

            model_file = pathlib.Path(name).relative_to(cwd)
            model_relative = str(model_file)
            assert "/" not in model_relative

            mod = OMPython.ModelicaSystem(model_relative, "M", raiseerrors=True)
            assert float(mod.getParameters("a")[0]) == -1
        finally:
            # clean up the temporary file
            model_file.unlink()

    def test_customBuildDirectory(self):
        filePath = (self.tmp / "M.mo").as_posix()
        tmpdir = self.tmp / "tmpdir1"
        tmpdir.mkdir()
        m = OMPython.ModelicaSystem(filePath, "M", raiseerrors=True,
                                    customBuildDirectory=tmpdir)
        assert pathlib.Path(m.getWorkDirectory()).resolve() == tmpdir.resolve()
        result_file = tmpdir / "a.mat"
        assert not result_file.exists()
        m.simulate(resultfile="a.mat")
        assert result_file.is_file()

    def test_getSolutions(self):
        filePath = (self.tmp / "M.mo").as_posix()
        mod = OMPython.ModelicaSystem(filePath, "M", raiseerrors=True)
        x0 = 1
        a = -1
        tau = -1 / a
        stopTime=5*tau
        mod.setSimulationOptions([f"stopTime={stopTime}", "stepSize=0.1", "tolerance=1e-8"])
        mod.simulate()

        x = mod.getSolutions("x")
        t, x2 = mod.getSolutions(["time", "x"])
        assert (x2 == x).all()
        sol_names = mod.getSolutions()
        assert isinstance(sol_names, tuple)
        assert "time" in sol_names
        assert "x" in sol_names
        assert "der(x)" in sol_names
        with self.assertRaises(OMPython.ModelicaSystemError):
            mod.getSolutions("t")  # variable 't' does not exist
        assert np.isclose(t[0], 0), "time does not start at 0"
        assert np.isclose(t[-1], stopTime), "time does not end at stopTime"
        x_analytical = x0 * np.exp(a*t)
        assert np.isclose(x, x_analytical, rtol=1e-4).all()


if __name__ == '__main__':
    unittest.main()
