import OMPython
import os
import pathlib
import pytest
import tempfile
import numpy as np


@pytest.fixture
def model_firstorder(tmp_path):
    mod = tmp_path / "M.mo"
    mod.write_text("""model M
  Real x(start = 1, fixed = true);
  parameter Real a = -1;
equation
  der(x) = x*a;
end M;
""")
    return mod


def test_ModelicaSystem_loop(model_firstorder):
    def worker():
        filePath = model_firstorder.as_posix()
        mod = OMPython.ModelicaSystem()
        mod.model_definition(
            file=filePath,
            model="M",
        )
        mod.simulate()
        mod.convertMo2Fmu(fmuType="me")
    for _ in range(10):
        worker()


def test_setParameters():
    omc = OMPython.OMCSessionZMQ()
    model_path = omc.sendExpression("getInstallationDirectoryPath()") + "/share/doc/omc/testmodels/"
    mod = OMPython.ModelicaSystem()
    mod.model_definition(
        file=model_path + "BouncingBall.mo",
        model="BouncingBall",
    )

    # method 1
    mod.setParameters(pvals={"e": 1.234})
    mod.setParameters(pvals={"g": 321.0})
    assert mod.getParameters("e") == ["1.234"]
    assert mod.getParameters("g") == ["321.0"]
    assert mod.getParameters() == {
        "e": "1.234",
        "g": "321.0",
    }
    with pytest.raises(KeyError):
        mod.getParameters("thisParameterDoesNotExist")

    # method 2
    mod.setParameters(pvals={"e": 21.3, "g": 0.12})
    assert mod.getParameters() == {
        "e": "21.3",
        "g": "0.12",
    }
    assert mod.getParameters(["e", "g"]) == ["21.3", "0.12"]
    assert mod.getParameters(["g", "e"]) == ["0.12", "21.3"]
    with pytest.raises(KeyError):
        mod.getParameters(["g", "thisParameterDoesNotExist"])


def test_setSimulationOptions():
    omc = OMPython.OMCSessionZMQ()
    model_path = omc.sendExpression("getInstallationDirectoryPath()") + "/share/doc/omc/testmodels/"
    mod = OMPython.ModelicaSystem()
    mod.model_definition(
        file=model_path + "BouncingBall.mo",
        model="BouncingBall",
    )

    # method 1
    mod.setSimulationOptions(simOptions={"stopTime": 1.234})
    mod.setSimulationOptions(simOptions={"tolerance": 1.1e-08})
    assert mod.getSimulationOptions("stopTime") == ["1.234"]
    assert mod.getSimulationOptions("tolerance") == ["1.1e-08"]
    assert mod.getSimulationOptions(["tolerance", "stopTime"]) == ["1.1e-08", "1.234"]
    d = mod.getSimulationOptions()
    assert isinstance(d, dict)
    assert d["stopTime"] == "1.234"
    assert d["tolerance"] == "1.1e-08"
    with pytest.raises(KeyError):
        mod.getSimulationOptions("thisOptionDoesNotExist")

    # method 2
    mod.setSimulationOptions(simOptions={"stopTime": 2.1, "tolerance": "1.2e-08"})
    d = mod.getSimulationOptions()
    assert d["stopTime"] == "2.1"
    assert d["tolerance"] == "1.2e-08"


def test_relative_path(model_firstorder):
    cwd = pathlib.Path.cwd()
    (fd, name) = tempfile.mkstemp(prefix='tmpOMPython.tests', dir=cwd, text=True)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(model_firstorder.read_text())

        model_file = pathlib.Path(name).relative_to(cwd)
        model_relative = str(model_file)
        assert "/" not in model_relative

        mod = OMPython.ModelicaSystem()
        mod.model_definition(
            file=model_relative,
            model="M",
        )
        assert float(mod.getParameters("a")[0]) == -1
    finally:
        model_file.unlink()  # clean up the temporary file


def test_customBuildDirectory(tmp_path, model_firstorder):
    filePath = model_firstorder.as_posix()
    tmpdir = tmp_path / "tmpdir1"
    tmpdir.mkdir()
    mod = OMPython.ModelicaSystem(customBuildDirectory=tmpdir)
    mod.model_definition(
        file=filePath,
        model="M",
    )
    assert mod.getWorkDirectory().resolve() == tmpdir.resolve()
    result_file = tmpdir / "a.mat"
    assert not result_file.exists()
    mod.simulate(resultfile="a.mat")
    assert result_file.is_file()


def test_getSolutions(model_firstorder):
    filePath = model_firstorder.as_posix()
    mod = OMPython.ModelicaSystem()
    mod.model_definition(
        file=filePath,
        model="M",
    )
    x0 = 1
    a = -1
    tau = -1 / a
    stopTime = 5*tau
    mod.setSimulationOptions(simOptions={"stopTime": stopTime, "stepSize": 0.1, "tolerance": 1e-8})
    mod.simulate()

    x = mod.getSolutions("x")
    t, x2 = mod.getSolutions(["time", "x"])
    assert (x2 == x).all()
    sol_names = mod.getSolutions()
    assert isinstance(sol_names, tuple)
    assert "time" in sol_names
    assert "x" in sol_names
    assert "der(x)" in sol_names
    with pytest.raises(OMPython.ModelicaSystemError):
        mod.getSolutions("thisVariableDoesNotExist")
    assert np.isclose(t[0], 0), "time does not start at 0"
    assert np.isclose(t[-1], stopTime), "time does not end at stopTime"
    x_analytical = x0 * np.exp(a*t)
    assert np.isclose(x, x_analytical, rtol=1e-4).all()


def test_getters(tmp_path):
    model_file = tmp_path / "M_getters.mo"
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
    mod = OMPython.ModelicaSystem()
    mod.model_definition(
        file=model_file.as_posix(),
        model="M_getters",
    )

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

    with pytest.raises(KeyError):
        mod.getQuantities("thisQuantityDoesNotExist")

    assert mod.getInputs() == {}
    with pytest.raises(KeyError):
        mod.getInputs("thisInputDoesNotExist")
    # getOutputs before simulate()
    assert mod.getOutputs() == {'y': '-0.4'}
    assert mod.getOutputs("y") == ["-0.4"]
    assert mod.getOutputs(["y", "y"]) == ["-0.4", "-0.4"]
    with pytest.raises(KeyError):
        mod.getOutputs("thisOutputDoesNotExist")

    # getContinuous before simulate():
    assert mod.getContinuous() == {
        'x': '1.0',
        'der(x)': None,
        'y': '-0.4'
    }
    assert mod.getContinuous("y") == ['-0.4']
    assert mod.getContinuous(["y", "x"]) == ['-0.4', '1.0']
    with pytest.raises(KeyError):
        mod.getContinuous("a")  # a is a parameter

    stopTime = 1.0
    a = -0.5
    b = 0.1
    x0 = 1.0
    x_analytical = -b/a + (x0 + b/a) * np.exp(a * stopTime)
    dx_analytical = (x0 + b/a) * a * np.exp(a * stopTime)
    mod.setSimulationOptions(simOptions={"stopTime": stopTime})
    mod.simulate()

    # getOutputs after simulate()
    d = mod.getOutputs()
    assert d.keys() == {"y"}
    assert np.isclose(d["y"], dx_analytical, 1e-4)
    assert mod.getOutputs("y") == [d["y"]]
    assert mod.getOutputs(["y", "y"]) == [d["y"], d["y"]]
    with pytest.raises(KeyError):
        mod.getOutputs("thisOutputDoesNotExist")

    # getContinuous after simulate() should return values at end of simulation:
    with pytest.raises(OMPython.ModelicaSystemError):
        mod.getContinuous("a")  # a is a parameter
    with pytest.raises(OMPython.ModelicaSystemError):
        mod.getContinuous(["x", "a", "y"])  # a is a parameter
    d = mod.getContinuous()
    assert d.keys() == {"x", "der(x)", "y"}
    assert np.isclose(d["x"], x_analytical, 1e-4)
    assert np.isclose(d["der(x)"], dx_analytical, 1e-4)
    assert np.isclose(d["y"], dx_analytical, 1e-4)
    assert mod.getContinuous("x") == [d["x"]]
    assert mod.getContinuous(["y", "x"]) == [d["y"], d["x"]]

    with pytest.raises(OMPython.ModelicaSystemError):
        mod.getContinuous("a")  # a is a parameter

    with pytest.raises(OMPython.ModelicaSystemError):
        mod.setSimulationOptions(simOptions={"thisOptionDoesNotExist": 3})


def test_simulate_inputs(tmp_path):
    model_file = tmp_path / "M_input.mo"
    model_file.write_text("""
model M_input
Real x(start=0, fixed=true);
input Real u1;
input Real u2;
output Real y;
equation
der(x) = u1 + u2;
y = x;
end M_input;
""")
    mod = OMPython.ModelicaSystem()
    mod.model_definition(
        file=model_file.as_posix(),
        model="M_input",
    )

    mod.setSimulationOptions(simOptions={"stopTime": 1.0})

    # integrate zero (no setInputs call) - it should default to None -> 0
    assert mod.getInputs() == {
        "u1": None,
        "u2": None,
    }
    mod.simulate()
    y = mod.getSolutions("y")[0]
    assert np.isclose(y[-1], 0.0)

    # integrate a constant
    mod.setInputs(name={"u1": 2.5})
    assert mod.getInputs() == {
        "u1": [
            (0.0, 2.5),
            (1.0, 2.5),
        ],
        # u2 is set due to the call to simulate() above
        "u2": [
            (0.0, 0.0),
            (1.0, 0.0),
        ],
    }
    mod.simulate()
    y = mod.getSolutions("y")[0]
    assert np.isclose(y[-1], 2.5)

    # now let's integrate the sum of two ramps
    mod.setInputs(name={"u1": [(0.0, 0.0), (0.5, 2), (1.0, 0)]})
    assert mod.getInputs("u1") == [[
        (0.0, 0.0),
        (0.5, 2.0),
        (1.0, 0.0),
    ]]
    mod.simulate()
    y = mod.getSolutions("y")[0]
    assert np.isclose(y[-1], 1.0)

    # let's try some edge cases
    # unmatched startTime
    with pytest.raises(OMPython.ModelicaSystemError):
        mod.setInputs(name={"u1": [(-0.5, 0.0), (1.0, 1)]})
        mod.simulate()
    # unmatched stopTime
    with pytest.raises(OMPython.ModelicaSystemError):
        mod.setInputs(name={"u1": [(0.0, 0.0), (0.5, 1)]})
        mod.simulate()

    # Let's use both inputs, but each one with different number of
    # samples. This has an effect when generating the csv file.
    mod.setInputs(name={"u1": [(0.0, 0), (1.0, 1)],
                        "u2": [(0.0, 0), (0.25, 0.5), (0.5, 1.0), (1.0, 0)]})
    csv_file = mod._createCSVData()
    assert pathlib.Path(csv_file).read_text() == """time,u1,u2,end
0.0,0.0,0.0,0
0.25,0.25,0.5,0
0.5,0.5,1.0,0
1.0,1.0,0.0,0
"""

    mod.simulate()
    y = mod.getSolutions("y")[0]
    assert np.isclose(y[-1], 1.0)
