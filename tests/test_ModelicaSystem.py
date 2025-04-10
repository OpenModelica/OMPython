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
        stopTime = 5*tau
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

    def test_getters(self):
        model_file = self.tmp / "M_getters.mo"
        model_file.write_text("""
model M_getters
  Real x(start = 1, fixed = true);
  output Real y "the derivative";
  parameter Real a = -0.5;
  parameter Real b = 0.1;
equation
  der(x) = x*a + b;
  y = der(x);
end M_getters;
""")
        mod = OMPython.ModelicaSystem(model_file.as_posix(), "M_getters", raiseerrors=True)

        q = mod.getQuantities()
        assert isinstance(q, list)
        assert sorted(q, key=lambda d: d["name"]) == sorted([
            {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'local',
                'changeable': 'true',
                'description': None,
                'max': None,
                'min': None,
                'name': 'x',
                'start': '1.0',
                'unit': None,
                'variability': 'continuous',
            },
            {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'local',
                'changeable': 'false',
                'description': None,
                'max': None,
                'min': None,
                'name': 'der(x)',
                'start': None,
                'unit': None,
                'variability': 'continuous',
            },
            {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'output',
                'changeable': 'false',
                'description': 'the derivative',
                'max': None,
                'min': None,
                'name': 'y',
                'start': '-0.4',
                'unit': None,
                'variability': 'continuous',
            },
            {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'parameter',
                'changeable': 'true',
                'description': None,
                'max': None,
                'min': None,
                'name': 'a',
                'start': '-0.5',
                'unit': None,
                'variability': 'parameter',
            },
            {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'parameter',
                'changeable': 'true',
                'description': None,
                'max': None,
                'min': None,
                'name': 'b',
                'start': '0.1',
                'unit': None,
                'variability': 'parameter',
            }
        ], key=lambda d: d["name"])

        assert mod.getQuantities("y") == [
            {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'output',
                'changeable': 'false',
                'description': 'the derivative',
                'max': None,
                'min': None,
                'name': 'y',
                'start': '-0.4',
                'unit': None,
                'variability': 'continuous',
            }
        ]

        assert mod.getQuantities(["y", "x"]) == [
            {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'output',
                'changeable': 'false',
                'description': 'the derivative',
                'max': None,
                'min': None,
                'name': 'y',
                'start': '-0.4',
                'unit': None,
                'variability': 'continuous',
            },
            {
                'alias': 'noAlias',
                'aliasvariable': None,
                'causality': 'local',
                'changeable': 'true',
                'description': None,
                'max': None,
                'min': None,
                'name': 'x',
                'start': '1.0',
                'unit': None,
                'variability': 'continuous',
            },
        ]

        assert mod.getInputs() == {}
        # getOutputs before simulate()
        assert mod.getOutputs() == {'y': '-0.4'}
        assert mod.getOutputs("y") == ["-0.4"]
        assert mod.getOutputs(["y", "y"]) == ["-0.4", "-0.4"]

        # getContinuous before simulate():
        assert mod.getContinuous() == {
            'x': '1.0',
            'der(x)': None,
            'y': '-0.4'
        }
        assert mod.getContinuous("y") == ['-0.4']
        assert mod.getContinuous(["y", "x"]) == ['-0.4', '1.0']
        assert mod.getContinuous("a") == ["NotExist"]  # a is a parameter

        stopTime = 1.0
        a = -0.5
        b = 0.1
        x0 = 1.0
        x_analytical = -b/a + (x0 + b/a) * np.exp(a * stopTime)
        dx_analytical = (x0 + b/a) * a * np.exp(a * stopTime)
        mod.setSimulationOptions(f"stopTime={stopTime}")
        mod.simulate()

        # getOutputs after simulate()
        d = mod.getOutputs()
        assert d.keys() == {"y"}
        assert np.isclose(d["y"], dx_analytical, 1e-4)
        assert mod.getOutputs("y") == [d["y"]]
        assert mod.getOutputs(["y", "y"]) == [d["y"], d["y"]]

        # getContinuous after simulate() should return values at end of simulation:
        with self.assertRaises(OMPython.ModelicaSystemError):
            mod.getContinuous("a")  # a is a parameter
        with self.assertRaises(OMPython.ModelicaSystemError):
            mod.getContinuous(["x", "a", "y"])  # a is a parameter
        d = mod.getContinuous()
        assert d.keys() == {"x", "der(x)", "y"}
        assert np.isclose(d["x"], x_analytical, 1e-4)
        assert np.isclose(d["der(x)"], dx_analytical, 1e-4)
        assert np.isclose(d["y"], dx_analytical, 1e-4)
        assert mod.getContinuous("x") == [d["x"]]
        assert mod.getContinuous(["y", "x"]) == [d["y"], d["x"]]

        with self.assertRaises(OMPython.ModelicaSystemError):
            mod.setSimulationOptions("thisOptionDoesNotExist=3")

    def test_simulate_inputs(self):
        model_file = self.tmp / "M_input.mo"
        model_file.write_text("""
model M_input
  Real x(start=0, fixed=true);
  input Real u;
  output Real y;
equation
  der(x) = u;
  y = x;
end M_input;
""")
        mod = OMPython.ModelicaSystem(model_file.as_posix(), "M_input", raiseerrors=True)

        mod.setSimulationOptions("stopTime=1.0")

        # integrate a constant
        mod.setInputs("u=2.5")
        assert mod.getInputs() == {
            "u": [
                (0.0, 2.5),
                (1.0, 2.5),
            ],
        }
        mod.simulate()
        y = mod.getSolutions("y")[0]
        assert np.isclose(y[-1], 2.5)

        # now let's integrate the sum of two ramps
        mod.setInputs("u=[(0.0, 0.0), (0.5, 2), (1.0, 0)]")
        assert mod.getInputs("u") == [[
            (0.0, 0.0),
            (0.5, 2.0),
            (1.0, 0.0),
        ]]
        mod.simulate()
        y = mod.getSolutions("y")[0]
        assert np.isclose(y[-1], 1.0)


if __name__ == '__main__':
    unittest.main()
